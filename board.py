"""Structures to hold and hanle puzzle state.
All supposed to be immune, comparable and hashable.

Apparently, this works for any solving approach.
"""

from collections.abc import Generator, Iterable
from typing import Callable, NamedTuple, Self

DIGITS = {1, 2, 3, 4, 5, 6, 7, 8, 9}
RANGE9 = (1, 2, 3, 4, 5, 6, 7, 8, 9)
RANGE81 = tuple(range(1, 82))


class Loc(NamedTuple):
    row: int
    col: int

    def __str__(self) -> str:
        return f"r{self.row}c{self.col}"


Digits = frozenset[int]


class Cell(NamedTuple):
    loc: Loc
    dgs: Digits

    @property
    def is_empty(self) -> bool:
        return len(self.dgs) == 0

    @property
    def is_final(self) -> bool:
        return len(self.dgs) == 1

    @property
    def is_draft(self) -> bool:
        return len(self.dgs) > 1

    @property
    def final(self) -> int | None:
        if len(self.dgs) == 1:
            (d,) = self.dgs
            return d

    def __contains__(self, dig: int) -> bool:
        return dig in self.dgs

    def __str__(self):
        cont = "".join(map(str, self.dgs))
        return f"{{{cont}@{self.loc}}}"


Transformer = Callable[[Cell], Cell]


class Board:
    __slots__ = "content"

    # storing in row-major order
    content: tuple[Digits, ...]  # note: indexing from 0

    # it's supposed to be immutable
    def __new__(cls, content: Iterable[Iterable[int]] | None = None):
        inst = super().__new__(cls)
        if content is None:
            inst.content = tuple(Digits() for _ in range(81))
        else:
            cont = tuple(map(Digits, content))
            assert len(cont) == 81
            inst.content = cont
        return inst

    def __repr__(self) -> str:
        grid = [repr(cell) + (",\t" if i % 9 else ",\n") for i, cell in enumerate(self.content, 1)]
        return f"Board((\n{''.join(grid)}))"

    @classmethod
    def __idx(cls, loc: Loc) -> int:
        return (loc.row - 1) * 9 + (loc.col - 1)

    @classmethod
    def __loc(cls, idx: int) -> Loc:
        return Loc(1 + idx // 9, 1 + idx % 9)

    def __iter__(self) -> Generator[Cell]:
        """iterate all cells (in storage order)"""
        for idx, cell in enumerate(self.content):
            yield Cell(self.__loc(idx), cell)

    def get(self, loc: Loc) -> Cell:
        return Cell(loc, self.content[self.__idx(loc)])

    def slice(self, locs: Iterable[Loc]) -> Iterable[Cell]:
        return (self.get(loc) for loc in locs)

    def __getitem__(self, loc: Loc | Iterable[Loc]) -> Cell | Iterable[Cell]:
        if isinstance(loc, Loc):
            return self.get(loc)
        else:
            return self.slice(loc)

    def __eq__(self, other: Self) -> bool:
        return self.content == other.content

    def __ne__(self, other: Self) -> bool:
        return not (self == other)

    @classmethod
    def transform(cls, orig: Self, trans: Transformer) -> Self:
        """Apply transformer to all cells"""
        return cls(tuple(trans(cell).dgs for cell in iter(orig)))

    @classmethod
    def replace(cls, orig: Self, loc: Loc, repl: Iterable[int]) -> Self:
        """Replace single cell"""
        content = list(orig.content)
        content[cls.__idx(loc)] = Digits(repl)
        return cls(content)
