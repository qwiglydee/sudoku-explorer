from typing import Any, Callable
from collections.abc import Generator, AsyncGenerator
from dataclasses import dataclass

from board import Cell, Board
from analytics import Target, validate


@dataclass
class Resolution:
    castaways: set[Target] | None = None
    finals: set[Target] | None = None

    def apply(self, current: Board) -> Board:
        """Removing castaways and isolating all finals"""

        if self.castaways:
            for trg in self.castaways:
                orig = current.get(trg.loc)
                current = Board.replace(current, trg.loc, Cell(orig.cell - {trg.dig}))

        if self.finals:
            for trg in self.finals:
                current = Board.replace(current, trg.loc, Cell({trg.dig}))

        return current

    # for inspecting
    highlights: dict[str, Any] | None = None


Resolving = Generator[Resolution]
Resolver = Callable[[Board], Resolving]
Solving = AsyncGenerator[tuple[Resolver, Resolution, Board]]


async def orchestrator(initial: Board, *resolvers: Resolver) -> AsyncGenerator[Resolver, Board | None]:
    """Orchestrating resolvers based on their result
    Yields resolvers in sequence
    - when nothing changed, turn moves to next resolver
    - when something changed, sequence resets
    """
    idx = 0
    lng = len(resolvers)

    current = initial
    while idx < lng:
        last = current
        current = yield resolvers[idx]
        if current == last:
            idx += 1
        else:
            idx = 0


async def solver(initial: Board, *resolvers: Resolver) -> Solving:
    """Applies all resolutions from orchestra of resolvers
    Yield intermediate results for inspecting
    """
    orchestra = orchestrator(initial, *resolvers)

    current = initial
    resolver = await orchestra.asend(None)  # type: ignore that fucking caveat
    while True:
        for resolution in resolver(current):
            current = resolution.apply(current)
            yield resolver, resolution, current
        try:
            resolver = await orchestra.asend(current)
        except StopAsyncIteration:
            break


async def solve_silent(initial: Board, *resolvers: Resolver):
    result = initial
    async for _, _, result in solver(initial, *resolvers):
        pass
    return result


async def solve_logging(initial: Board, /, *resolvers: Resolver, filtout: set[str] | None = None):
    result = initial
    iterations = 0
    async for resolver, resolution, result in solver(initial, *resolvers):
        iterations += 1
        if filtout and resolver.__name__ in filtout:
            continue
        print(f"{iterations:03d} {resolver.__name__}", end=": ")
        if resolution.castaways:
            print("-={", " ".join(map(str, resolution.castaways)), "}", end=" ")
        if resolution.finals:
            print(":={", " ".join(map(str, resolution.finals)), "}", end=" ")
        if resolution.highlights:
            if "zone" in resolution.highlights:
                print("@", resolution.highlights["zone"], end=" ")
            print("#", end=" ")
            if "anchors" in resolution.highlights:
                print(" ".join(map(str, resolution.highlights["anchors"])), end=" ")
            if "chain" in resolution.highlights:
                print(resolution.highlights["chain"], end=" ")
        print()
    print(validate(result), "in", iterations)
    return result
