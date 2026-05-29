from typing import Any, Callable
from collections.abc import Generator, AsyncGenerator
from dataclasses import dataclass

from board import Cell, Board
from analytics import Target


@dataclass
class Resolution:
    castaways: set[Target]
    finals: set[Target]

    def apply(self, current: Board) -> Board:
        """Removing castaways and isolating all finals"""

        for trg in self.castaways:
            orig = current.get(trg.loc)
            current = Board.replace(current, trg.loc, Cell(orig.cell - {trg.dig}))

        for trg in self.finals:
            current = Board.replace(current, trg.loc, Cell({trg.dig}))

        return current

    # for inspecting
    highlights: dict[str, set[Any]] | None = None


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


async def solver(initial: Board, orchestra: AsyncGenerator[Resolver, Board]) -> Solving:
    """Applies all resolutions from orchestra of resolvers
    Yield intermediate results for inspecting
    """
    resolver = await orchestra.asend(None)  # type: ignore that fucking caveat

    current = initial
    while True:
        for resolution in resolver(current):
            current = resolution.apply(current)
            yield resolver, resolution, current
        try:
            resolver = await orchestra.asend(current)
        except StopAsyncIteration:
            break
