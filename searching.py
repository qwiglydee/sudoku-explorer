"""Very generic search algorithms"""

from collections import deque
from collections.abc import Generator
from typing import Callable, Iterable, TypeVar


T = TypeVar("T")


def search_breadth[T](init: Iterable[T], expand: Callable[[T], Iterable[T]], accepting: Callable[[T], bool], canceling: Callable[[T], bool]) -> Generator[T]:
    """Generic infinite bread-first search"""
    frontier = deque[T](init)  # queue
    explored = set[T]()
    while frontier:
        state = frontier.popleft()
        if accepting(state):
            yield state
        explored.add(state)
        if not canceling(state):
            frontier.extend(ext for ext in expand(state) if ext not in explored and ext not in frontier)


def search_depth[T](init: Iterable[T], expand: Callable[[T], Iterable[T]], accepting: Callable[[T], bool], canceling: Callable[[T], bool]) -> Generator[T]:
    """Generic infinite bread-first search"""
    frontier = deque[T](init)  # stack
    explored = set[T]()
    while frontier:
        state = frontier.pop()
        if accepting(state):
            yield state
        explored.add(state)
        if not canceling(state):
            frontier.extend(ext for ext in expand(state) if ext not in explored and ext not in frontier)
