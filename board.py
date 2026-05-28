import re
from collections.abc import Generator, Iterable
from types import EllipsisType
from typing import Callable, NamedTuple, Self

DIGITS = {1, 2, 3, 4, 5, 6, 7, 8, 9}
POS9 = (1, 2, 3, 4, 5, 6, 7, 8, 9)
POS81 = tuple(range(1, 82))


class Loc(NamedTuple):
    """Location of a cell in a board"""

    row: int
    col: int

    @property
    def blk(self):
        br = (self.row - 1) // 3
        bc = (self.col - 1) // 3
        return 1 + br * 3 + bc

    def __str__(self) -> str:
        return f"r{self.row}c{self.col}"


class Locality(NamedTuple):
    """Locality of a block, row, col or cell"""

    blk: int | EllipsisType
    row: int | EllipsisType
    col: int | EllipsisType

    def __iter__(self) -> Generator[Loc]:
        """Generate all locations in the locality"""
        match (self.blk, self.row, self.col):  # NB: cannot use self-match because of recursion
            case (int(b), EllipsisType(), EllipsisType()):
                b0 = b - 1
                r1 = 1 + 3 * (b0 // 3)
                c1 = 1 + 3 * (b0 % 3)
                yield from (Loc(r, c) for r in range(r1, r1 + 3) for c in range(c1, c1 + 3))
            case (EllipsisType(), int(r), int(c)):
                yield Loc(r, c)
            case (EllipsisType(), int(r), EllipsisType()):
                yield from (Loc(r, i) for i in POS9)
            case (EllipsisType(), EllipsisType(), int(c)):
                yield from (Loc(i, c) for i in POS9)
            case _:
                raise TypeError()

    def locs(self) -> Iterable[Loc]:
        return tuple(iter(self))

    def __contains__(self, loc: Loc) -> bool:
        """Chack if location is in the locality"""
        match (self.blk, self.row, self.col):
            case (int(b), EllipsisType(), EllipsisType()):
                return loc.blk == b
            case (EllipsisType(), int(r), int(c)):
                return loc.row == r and loc.col == c
            case (EllipsisType(), int(r), EllipsisType()):
                return loc.row == r
            case (EllipsisType(), EllipsisType(), int(c)):
                return loc.col == c
            case _:
                raise TypeError()

    @classmethod
    def around(cls, loc: Loc) -> Iterable[Self]:
        """Get all localities around loc, excluding the cell"""
        return (
            cls(loc.blk, ..., ...),
            cls(..., loc.row, ...),
            cls(..., ..., loc.col),
        )

    @classmethod
    def common(cls, l1: Loc, l2: Loc) -> Generator[Self]:
        """Get all localities common for the locs, including cell itself"""
        if l1 == l2:
            yield cls(..., l1.row, l2.col)
            return
        if l1.blk == l2.blk:
            yield cls(l1.blk, ..., ...)
        if l1.row == l2.row:
            yield cls(..., l1.row, ...)
        if l1.col == l2.col:
            yield cls(..., ..., l1.col)

    def __str__(self):
        match (self.blk, self.row, self.col):
            case (int(b), EllipsisType(), EllipsisType()):
                return f"{{b{b}}}"
            case (EllipsisType(), int(r), int(c)):
                return f"{{r{r}c{c}}}"
            case (EllipsisType(), int(r), EllipsisType()):
                return f"{{r{r}}}"
            case (EllipsisType(), EllipsisType(), int(c)):
                return f"{{c{c}}}"
            case _:
                raise TypeError()


class Target(NamedTuple):
    """Target digit-segment inside a cell"""

    loc: Loc
    dig: int

    def __str__(self):
        return f"{self.dig}{self.loc}"


class MultiTarget(NamedTuple):
    """Target multiple digit-segment inside a cell"""

    loc: Loc
    digs: frozenset[int]

    def __str__(self):
        joined = "".join(map(str, self.digs))
        return f"{joined}{self.loc}"


class Cell(frozenset[int]):
    """Set of digits in a cell"""

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def is_final(self) -> bool:
        return len(self) == 1

    @property
    def is_draft(self) -> bool:
        return len(self) > 1

    @property
    def final(self) -> int | None:
        if len(self) == 1:
            (d,) = self
            return d

    def __str__(self):
        return "".join(map(str, self))


class Node(NamedTuple):
    """Node in a board containing digits
    Decoupled from board itself
    """

    loc: Loc
    cell: Cell

    def __iter__(self) -> Generator[Target]:
        return (Target(self.loc, d) for d in self.cell)

    def __str__(self):
        return f"{self.cell}@{self.loc}"


Transformer = Callable[[Node], Node]


class Board:
    """The container of Nodes adressed by Locs"""

    # storing in row-major order
    cells: tuple[Cell, ...]

    def __init__(self):
        """Init empty board"""
        self.cells = tuple(Cell() for _ in range(82))

    def __repr__(self) -> str:
        grid = [repr(cell) + (",\t" if i % 9 else ",\n") for i, cell in enumerate(self.cells, 1)]
        return f"Board((\n{''.join(grid)}))"

    @classmethod
    def __idx(cls, loc: Loc) -> int:
        return (loc.row - 1) * 9 + (loc.col - 1)

    @classmethod
    def __loc(cls, idx: int) -> Loc:
        return Loc(1 + idx // 9, 1 + idx % 9)

    def __iter__(self) -> Generator[Node]:
        """iterate all nodes (in storage order)"""
        for idx, cell in enumerate(self.cells):
            yield Node(self.__loc(idx), cell)

    def get(self, loc: Loc) -> Node:
        return Node(loc, self.cells[self.__idx(loc)])

    def slice(self, locs: Iterable[Loc] | Locality, filter: None | Callable[[Node], bool] = None) -> Iterable[Node]:
        nodes = tuple(self.get(loc) for loc in locs)
        if filter is None:
            return nodes
        return tuple(n for n in nodes if filter(n))

    def __getitem__(self, loc: Loc | Iterable[Loc] | Locality) -> Node | Iterable[Node]:
        if isinstance(loc, Loc):
            return self.get(loc)
        else:
            return self.slice(loc)

    def __eq__(self, other: Self) -> bool:
        return all(s == o for s, o in zip(self.cells, other.cells))

    def __ne__(self, other: Self) -> bool:
        return not (self == other)

    @classmethod
    def replace(cls, orig: Self, loc: Loc, cell: Cell) -> Self:
        """Replace single cell"""

        def t(node) -> Cell:
            if node.loc == loc:
                return cell
            else:
                return node.cell

        new = cls()
        new.cells = tuple(t(node) for node in orig)
        return new

    @classmethod
    def transform(cls, orig: Self, trans: Transformer) -> Self:
        """Apply transformer to all draft nodes"""

        def t(node) -> Node:
            return node if node.cell.is_final else trans(node)

        new = cls()
        new.cells = tuple(Cell(t(node).cell) for node in orig)
        return new
