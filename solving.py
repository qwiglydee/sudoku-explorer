"""Generic iterative solving tools
Using async generators to integrate with interactive scripts/gui
"""

from typing import Any, Callable
from collections.abc import Generator, AsyncGenerator
from dataclasses import dataclass, field

from board import Digits, Cell, Board


@dataclass
class Resolution:
    """Single move of solving"""

    castaways: set[Cell] = field(default_factory=set)
    finals: set[Cell] = field(default_factory=set)

    def apply(self, current: Board) -> Board:
        """Removing castaways and isolating all finals"""

        for away in self.castaways:
            orig = current.get(away.loc)
            digits = Digits(orig.digits - away.digits)
            current = Board.insert(current, Cell(away.loc, digits))

        for cell in self.finals:
            current = Board.insert(current, cell)

        return current

    # for inspecting
    highlights: dict[str, Any] = field(default_factory=dict)


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
