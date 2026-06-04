import re
from collections import Counter
from itertools import chain as iterchain
from typing import Iterable

from board import DIGITS, Board, Cell, Loc, Node
from analytics import Zone

iterflat = iterchain.from_iterable


def nonone(obj) -> bool:
    return obj is not None


def nodehave(dig: int):
    def filt(node: Node):
        return dig in node.cell

    return filt


def diff(b1: Board, b2: Board):
    new = Board()
    new.cells = tuple(Cell(set(c1) ^ set(c2)) for c1, c2 in zip(b1.cells, b2.cells))
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


def count_finals(nodes: Iterable[Node]) -> Counter:
    return Counter(n.cell.final for n in filter(Node.is_final, nodes))


def count_digits(nodes: Iterable[Node]):
    return Counter(iterflat(n.cell for n in nodes))


def fillempty(node: Node):
    if node.cell.is_empty:
        return Node(node.loc, Cell(DIGITS))
    else:
        return node


def neighborhood(board: Board, zone: Zone) -> Iterable[Node]:
    return board.slice(iter(zone))


def draftborhood(board: Board, zone: Zone) -> Iterable[Node]:
    return filter(Node.is_draft, board.slice(iter(zone)))


def finalborhood(board: Board, zone: Zone) -> Iterable[Node]:
    return filter(Node.is_final, board.slice(iter(zone)))


def validate(board: Board):
    if not all(Node.is_final(n) for n in board):
        return "INCOMPLETE"

    def fulfiled(zone: Zone):
        finalborhood = tuple(filter(Node.is_final, neighborhood(board, zone)))
        return set(n.cell.final for n in finalborhood) == DIGITS

    if all(map(fulfiled, Zone.All())):
        return "SOLVED"
    else:
        return "BROKEN"
