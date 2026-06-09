import re
from collections import Counter
from itertools import chain as iterchain
from typing import Iterable

from board import Digits, DIGITS, Loc, Board, Cell
from topology import Zone

iterflat = iterchain.from_iterable


def diff(b1: Board, b2: Board):
    return Board((c2 - c1 for c1, c2 in zip(b1.content, b2.content)))


def bparse(literal: str):
    """Parse string dump row by row:
    spaces are ignored
    dots make empty cells
    """
    init = re.sub(r"\s+", "", literal)
    return Board({int(d)} if d != "." else {} for d in init)


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
            cell = board.get(loc)
            d = ci % 3 + 1 + 3 * (ri % 3)
            end = "\n" if c1 == 27 else "║" if c1 % 9 == 0 else "│" if c1 % 3 == 0 else ""
            print(d if d in cell else " ", end=end)

        if r1 == 27:
            print()
        elif r1 % 9 == 0:
            print("═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══")
        elif r1 % 3 == 0:
            print("───┼───┼───╫───┼───┼───╫───┼───┼───")


def picture(board: Board) -> str:
    """Convert a Grid to a Picture string, one line at a time."""

    def val(cell) -> str:
        if cell.is_virgin:
            return "."
        else:
            return "".join(map(str, sorted(cell.digits)))

    maxwidth = max(len(val(cell)) for cell in board)
    dash1 = "─" * (maxwidth * 3 + 2)
    dash3 = "\n" + "┼".join(3 * [dash1])

    def cell(r, c):
        return val(board.get(Loc(r, c))).center(maxwidth) + ("│" if c in (3, 6) else " ")

    def line(r):
        return "".join(cell(r, c) for c in range(1, 10)) + (dash3 if r in (3, 6) else "")

    return "\n".join(map(line, range(1, 10)))


def neighborhood(board: Board, zone: Zone | Iterable[Loc]) -> Iterable[Cell]:
    return board.slice(iter(zone))


def draftborhood(board: Board, zone: Zone | Iterable[Loc]) -> Iterable[Cell]:
    return filter(lambda c: c.is_draft, board.slice(iter(zone)))


def draftboard(board: Board) -> Iterable[Cell]:
    return filter(lambda c: c.is_draft, iter(board))


def finalborhood(board: Board, zone: Zone | Iterable[Loc]) -> Iterable[Cell]:
    return filter(lambda c: c.is_final, board.slice(iter(zone)))


def count_finals(cells: Board | Iterable[Cell]) -> Counter[int]:
    return Counter(c.final for c in iter(cells) if c.is_final)  # type: ignore impossible None's


def count_digits(cells: Board | Iterable[Cell]) -> Counter[int]:
    return Counter(iterflat(c.digits for c in iter(cells)))


def fillempty(cell: Cell):
    return Cell(cell.loc, Digits(DIGITS)) if cell.is_empty else cell


def filt_finals(c: Cell):
    return c.is_final


def filt_drafts(c: Cell):
    return c.is_draft


def filt_having(d: int | Iterable[int]):
    if isinstance(d, int):
        return lambda c: d in c.digits
    else:
        dd = Digits(d)
        return lambda c: dd <= c.digits


def filt_havesome(d: int | Iterable[int]):
    if isinstance(d, int):
        return lambda c: d in c.digits
    else:
        dd = Digits(d)
        return lambda c: len(dd & c.digits)


def flat_cells(cc: Iterable[Cell]):
    return iterflat(c.digits for c in cc)
