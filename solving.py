"""Generic iterative solving tools
Using async generators to integrate with interactive scripts/gui
"""

from typing import Any, Callable
from collections.abc import Generator, AsyncGenerator
from functools import wraps

from board import Board, Cell, Digits
from analysis import Node


Pattern = dict[str, set[Node] | Any]
Resolving = Generator[Pattern]
Resolver = Callable[[Board], Resolving]
Solving = AsyncGenerator[tuple[Resolver, Pattern, Board]]


def removler(spoilers: set[Node]):
    def trans(cell: Cell) -> Cell:
        for s in spoilers:
            if cell.loc in s.zone:
                return Cell(cell.loc, Digits(cell.digits - s.digits))
        return cell

    return trans


def resolve(board: Board, pattern: Pattern):
    assert "spoilers" in pattern
    spoilers = pattern["spoilers"]
    assert isinstance(spoilers, set)
    return Board.transform(board, removler(spoilers))


def onceolver(fn: Resolver):
    """Makes resolver to fire only once"""

    @wraps(fn)
    def wrapped(board: Board):
        scanning = fn(board)
        try:
            yield next(scanning)
        except StopIteration:
            pass

    return wrapped


async def orchestrator(initial: Board, *resolvers: Resolver) -> AsyncGenerator[Resolver, Board | None]:
    """Orchestrating resolvers based on their result
    Receives board after applying last resolver
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
    Yields matching patterns and their results
    """
    orchestra = orchestrator(initial, *resolvers)

    current = initial
    resolver = await orchestra.asend(None)  # type: ignore that fucking caveat
    while True:
        for pattern in resolver(current):
            current = resolve(current, pattern)
            yield resolver, pattern, current
        try:
            resolver = await orchestra.asend(current)
        except StopAsyncIteration:
            break
