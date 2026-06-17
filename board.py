"""Structures to hold and hanle puzzle state.
All supposed to be immune, comparable and hashable.

Apparently, this works for any solving approach.
"""

from collections.abc import Generator, Iterable
from typing import Callable, Iterator, NamedTuple, Self


class Digits(frozenset[int]):
    def __str__(self):
        return "".join(map(str, sorted(self)))


DIGITS = Digits((1, 2, 3, 4, 5, 6, 7, 8, 9))


class Loc(NamedTuple):
    POS = (1, 2, 3, 4, 5, 6, 7, 8, 9)

    r: int
    c: int

    def __str__(self) -> str:
        return f"r{self.r}c{self.c}"

    @classmethod
    def box4loc(cls, loc: Self) -> int:
        assert loc.r in cls.POS and loc.c in cls.POS
        r0 = (loc.r - 1) // 3 * 3
        c0 = (loc.c - 1) // 3
        return r0 + c0 + 1

    @classmethod
    def box4row(cls, row: int) -> tuple[int, int, int]:
        assert row in cls.POS
        b0 = (row - 1) // 3 * 3
        return (b0 + 1, b0 + 2, b0 + 3)

    @classmethod
    def box4col(cls, col: int) -> tuple[int, int, int]:
        assert col in cls.POS
        b0 = (col - 1) // 3
        return (b0 + 1, b0 + 4, b0 + 7)

    @classmethod
    def row4box(cls, box: int) -> tuple[int, int, int]:
        assert box in cls.POS
        r0 = (box - 1) // 3 * 3
        return (r0 + 1, r0 + 2, r0 + 3)

    @classmethod
    def col4box(cls, box: int) -> tuple[int, int, int]:
        assert box in cls.POS
        c0 = (box - 1) % 3 * 3
        return (c0 + 1, c0 + 2, c0 + 3)


class Cell(NamedTuple):
    """Content of a cell coupled with its coords"""

    loc: Loc
    digits: Digits

    @property
    def is_empty(self) -> bool:
        return len(self.digits) == 0

    @property
    def is_final(self) -> bool:
        return len(self.digits) == 1

    @property
    def is_draft(self) -> bool:
        return len(self.digits) > 1

    @property
    def is_virgin(self) -> bool:
        return len(self.digits) == 9

    @property
    def final(self) -> int:
        assert self.is_final
        (d,) = self.digits
        return d

    def __contains__(self, dig: int) -> bool:
        return dig in self.digits

    def __len__(self):
        return len(self.digits)

    def __iter__(self) -> Iterator[int]:
        for d in self.digits:
            yield d

    def __str__(self):
        cont = "".join(map(str, sorted(self.digits)))
        return f"{cont}@{self.loc}"


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

    @classmethod
    def Pristine(cls):
        return cls(DIGITS for _ in range(81))

    def __repr__(self) -> str:
        grid = [repr(cell) + (",\t" if i % 9 else ",\n") for i, cell in enumerate(self.content, 1)]
        return f"Board((\n{''.join(grid)}))"

    @classmethod
    def _idx(cls, loc: Loc) -> int:
        return (loc.r - 1) * 9 + (loc.c - 1)

    @classmethod
    def _loc(cls, idx: int) -> Loc:
        return Loc(1 + idx // 9, 1 + idx % 9)

    def __iter__(self) -> Generator[Cell]:
        """iterate all cells (in storage order)"""
        for idx, cell in enumerate(self.content):
            yield Cell(self._loc(idx), cell)

    def get(self, loc: Loc) -> Cell:
        return Cell(loc, self.content[self._idx(loc)])

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
        return cls(tuple(trans(cell).digits for cell in iter(orig)))

    @classmethod
    def replace(cls, orig: Self, cell: Cell) -> Self:
        """Replace single cell"""
        content = list(orig.content)
        content[cls._idx(cell.loc)] = Digits(cell.digits)
        return cls(content)

    def validate(self) -> tuple[bool, bool, bool]:
        """Check completeness and validness (even for incomplete) and draftness"""
        cells = list(iter(self))

        complete = sum(c.is_final for c in cells) == 81
        drafted = sum(c.is_draft for c in cells) > 0

        def valid_slice(locs: Iterable[Loc]):
            cells = [self.get(loc) for loc in locs]
            finals = tuple(filter(lambda c: c.is_final, cells))
            digits = set(c.final for c in finals)
            return len(finals) == len(digits)

        valid = (
            all(valid_slice(Loc(r, c) for r in Loc.row4box(i) for c in Loc.col4box(i)) for i in Loc.POS)
            and all(valid_slice(Loc(i, c) for c in Loc.POS) for i in Loc.POS)
            and all(valid_slice(Loc(r, i) for r in Loc.POS) for i in Loc.POS)
        )

        return complete, valid, drafted
