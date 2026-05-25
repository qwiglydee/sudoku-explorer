import re
from collections.abc import Generator, Iterable
from types import EllipsisType
from typing import Callable, NamedTuple, Self

DIGITS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
POS9 = (1, 2, 3, 4, 5, 6, 7, 8, 9)
POS81 = tuple(range(1, 82))


class Loc(NamedTuple):
    """Location in a board"""

    row: int
    col: int

    @property
    def blk(self):
        br = (self.row - 1) // 3
        bc = (self.col - 1) // 3
        return 1 + br * 3 + bc

    def __str__(self) -> str:
        return f"[{self.row},{self.col}]"


class Target(NamedTuple):
    """Target digit-segment inside a cell"""

    loc: Loc
    seg: int

    def __str__(self):
        return f"{self.seg}@{self.loc}"


class Cell(tuple[int, ...]):
    """Set of digits in a cell"""

    # immutable object

    def __or__(self, other) -> Self:
        return self.__class__(set(self) | set(other))

    def __and__(self, other) -> Self:
        return self.__class__(set(self) & set(other))

    def __xor__(self, other) -> Self:
        return self.__class__(set(self) ^ set(other))

    def __sub__(self, other) -> Self:
        return self.__class__(d for d in self if d not in other)

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def is_final(self) -> bool:
        return len(self) == 1

    @property
    def final(self) -> int | None:
        return self[0] if self.is_final else None

    @property
    def is_draft(self) -> bool:
        return len(self) > 1


class Node(NamedTuple):
    """Node in a board containing digits
    Decoupled from board itself
    """

    # immutable object

    loc: Loc
    cell: Cell


class Board:
    """The container of Nodes adressed by Locs"""

    # supposed to be immutable as well

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
        return tuple(self.get(loc) for loc in locs)

    def __getitem__(self, loc: Loc | Iterable[Loc]) -> Node | Iterable[Node]:
        if isinstance(loc, Loc):
            return self.get(loc)
        else:
            return self.slice(loc)


Transformer = Callable[[Board, Node], Node]


def transform(orig: Board, trans: Transformer) -> Board:
    new = Board()
    new.cells = tuple(trans(orig, node).cell for node in orig)
    return new


def parse(literal: str):
    """Parse string dump row by row:
    spaces are ignored
    dots make empty cells
    """
    init = re.sub(r"\s+", "", literal)
    cells = [Cell((int(d),)) if d != "." else Cell() for d in init]
    board = Board()
    board.cells = tuple(cells)
    return board


def bprint(board: Board):
    for r in range(27):
        r1 = 1 + r
        r0 = r // 3
        ri = r % 3
        for c in range(27):
            c1 = 1 + c
            c0 = c // 3
            ci = c % 3
            loc = Loc(1 + r0, 1 + c0)
            cell = board.get(loc).cell
            d = ci % 3 + 1 + 3 * (ri % 3)
            end = "\n" if c1 == 27 else "║" if c1 % 9 == 0 else "│" if c1 % 3 == 0 else ""
            print(d if d in cell else " ", end=end)

        if r1 == 27:
            print()
        elif r1 % 9 == 0:
            print("═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══")
        elif r1 % 3 == 0:
            print("───┼───┼───╫───┼───┼───╫───┼───┼───")
