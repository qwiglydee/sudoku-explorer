from collections.abc import Generator, Iterable
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

    @classmethod
    def of_blk(cls, blk: int):
        """First row/col in a block"""
        b = blk - 1
        return cls(1 + 3 * (b // 3), 1 + 3 * (b % 3))

    def __str__(self) -> str:
        return f"r{self.row}c{self.col}"


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

    # the is_ methods are to use as filter(Node.is_draft, nodes)

    @classmethod
    def is_empty(cls, node: Self) -> bool:
        return node.cell.is_empty

    @classmethod
    def is_final(cls, node: Self) -> bool:
        return node.cell.is_final

    @classmethod
    def is_draft(cls, node: Self) -> bool:
        return node.cell.is_draft

    def __str__(self):
        return f"{self.cell}@{self.loc}"

    def __iter__(self):
        raise TypeError()


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

    def slice(self, locs: Iterable[Loc]) -> Iterable[Node]:
        return (self.get(loc) for loc in locs)

    def __getitem__(self, loc: Loc | Iterable[Loc]) -> Node | Iterable[Node]:
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
        """Apply transformer to all nodes"""

        def t(node) -> Node:
            return node if node.cell.is_final else trans(node)

        new = cls()
        new.cells = tuple(Cell(t(node).cell) for node in orig)
        return new
