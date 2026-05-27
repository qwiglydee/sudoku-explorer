import re
from typing import Iterable

from board import POS9, Board, Cell, Loc, Locality, Node, Target


def diff(b1: Board, b2: Board):
    new = Board()
    new.cells = tuple(Cell(set(c1) ^ set(c2)) for c1, c2 in zip(b1.cells, b2.cells))
    return new


def filter_empty(node: Node):
    return node.cell.is_empty


def filter_drafts(node: Node):
    return node.cell.is_draft


def filter_finals(node: Node):
    return node.cell.is_final


def filter_digit(digit: int):
    def filtering(node: Node):
        return digit in node.cell

    return filtering


def iter_layer(board: Board, digit: int) -> Iterable[Target]:
    return tuple(Target(node.loc, digit) for node in board if digit in node.cell)


def iter_allzones():
    for i in POS9:
        yield Locality(i, ..., ...)
    for i in POS9:
        yield Locality(..., i, ...)
    for i in POS9:
        yield Locality(..., ..., i)


def zerotransformer(_: Board, node: Node):
    return node


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
