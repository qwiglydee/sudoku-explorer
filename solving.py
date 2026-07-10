"""Generic iterative solving tools
Using async generators to integrate with interactive scripts/gui
"""

from typing import Any, Callable
from collections.abc import Generator, AsyncGenerator
from functools import wraps

from board import Board, Cell, Digits
from utils import boardiff
from targeting import Node


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


async def orchestrator(*resolvers: Resolver) -> AsyncGenerator[Resolver, bool | None]:
    """Orchestrating resolvers based on their result
    Yields resolvers in sequence:
    - if something worked, sequence is reset,
    - if didn't work, move to a next resolver
    """
    idx = 0
    lng = len(resolvers)

    while idx < lng:
        worked = yield resolvers[idx]
        if worked:
            idx = 0
        else:
            idx += 1


async def solver(initial: Board, *resolvers: Resolver) -> Solving:
    """Applies all resolutions from orchestra of resolvers
    Yields matching patterns and their results
    """
    orchestra = orchestrator(*resolvers)

    current = initial
    try:
        worked = None
        while True:
            resolver = await orchestra.asend(worked)
            last = current
            for pattern in resolver(current):
                current = resolve(current, pattern)
                yield resolver, pattern, current
            worked = last != current
    except StopAsyncIteration:
        pass


async def solve_silent(initial: Board, *resolvers: Resolver):
    result = initial
    _, _, drafted = result.validate()
    assert drafted
    async for _, _, result in solver(initial, *resolvers):
        complete, valid, drafted = result.validate()
        if complete or not valid or not drafted:
            break
    return result


async def solve_logging(initial: Board, *resolvers: Resolver, mute: set[str] = set(), verbose: set[str] = set()):
    result = initial
    iterations = 0
    _, _, drafted = result.validate()
    assert drafted
    current = result
    async for resolver, pattern, result in solver(initial, *resolvers):
        iterations += 1
        if resolver.__name__ not in mute:
            print(f"{iterations:03d} {resolver.__name__}", end=": ")
            diff = list(boardiff(current, result))
            print("-", " ".join(map(str, diff)), end="\t")

            if "*" in verbose or resolver.__name__ in verbose:
                for k, v in pattern.items():
                    if isinstance(v, set):
                        s = " ".join(map(str, v))
                        print("#", f"{k}:{{ {s} }}", end=" ")
                    else:
                        print("#", f"{k}:{v}", end=" ")
            print()

        current = result
        complete, valid, drafted = result.validate()
        if complete or not valid or not drafted:
            break

    complete, valid, drafted = result.validate()
    stuck = not complete and not drafted
    print("========")
    print(f"{iterations=} {complete=} {valid=} {stuck=}")
    return result
