from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable

from board import Cell, Board, Node, Target


@dataclass
class Resolution:
    castaways: set[Target]
    highlights: dict[str, set[Any]]

    def apply(self, current: Board) -> Board:
        """Just removing all castaways from the board"""

        def trans(node: Node) -> Node:
            cell = node.cell
            for rem in self.castaways:
                if rem.loc == node.loc:
                    cell = Cell(cell - {rem.dig})
            return Node(node.loc, cell)

        return Board.transform(current, trans)


Resolving = Generator[Resolution]
Resolver = Callable[[Board], Resolving]


async def orchestrator(initial: Board, *resolvers: Resolver) -> AsyncGenerator[Resolver, Board | None]:
    """Orchestrating sequence of resolver based on their result
    When nothing changed, turn moves to next resolver
    When something changed, sequence resets
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


async def solver(initial: Board, orchestra: AsyncGenerator[Resolver, Board]) -> Board:
    """Applies all resolutions from orchestra of resolvers"""
    resolver = await orchestra.asend(None)  # type: ignore that fucking caveat

    current = initial
    while True:
        print("----", resolver.__name__, end=": ")
        for resolution in resolver(current):
            print(len(resolution.castaways), end=", ")
            current = resolution.apply(current)
        print()

        try:
            resolver = await orchestra.asend(current)
        except StopAsyncIteration:
            break

    return current
