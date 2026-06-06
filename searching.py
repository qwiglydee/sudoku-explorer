from collections import deque
from collections.abc import Generator
from typing import Callable, Iterable, TypeVar


T = TypeVar("T")


# TODO: max_depth
def search_breadth[T](init: Iterable[T], expand: Callable[[T], Iterable[T]], criteria: Callable[[T], bool]) -> Generator[T]:
    """Generic infinite bread-first search"""
    frontier = deque[T](init)  # queue
    explored = set[T]()
    while frontier:
        state = frontier.popleft()
        if criteria(state):
            yield state
        explored.add(state)
        frontier.extend(ext for ext in expand(state) if ext not in explored and ext not in frontier)


# TODO: max_depth
def search_depth[T](init: Iterable[T], expand: Callable[[T], Iterable[T]], criteria: Callable[[T], bool]) -> Generator[T]:
    """Generic infinite bread-first search"""
    frontier = deque[T](init)  # stack
    explored = set[T]()
    while frontier:
        state = frontier.pop()
        if criteria(state):
            yield state
        explored.add(state)
        frontier.extend(ext for ext in expand(state) if ext not in explored and ext not in frontier)
