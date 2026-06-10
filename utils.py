import re
from collections import Counter
from itertools import chain as iterchain
from typing import Iterable

from board import Digits, DIGITS, Loc, Board, Cell
from topology import Zone

iterflat = iterchain.from_iterable


def diff(b1: Board, b2: Board):
    return Board((c2 - c1 for c1, c2 in zip(b1.content, b2.content)))


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


def parsepic_wide(source: str):
    source = re.sub(r"[─┼│\-+|]+", " ", source)
    source = source.strip()
    cells = re.split(r"\s+", source)
    assert len(cells) == 81
    return Board(Digits(map(int, cell)) for cell in cells)


def parsepic_init(source: str):
    source = source.strip()
    source = re.sub(r"[─┼\-+]+", "", source)
    source = re.sub(r"[│|]", " ", source)
    if " " in source:
        cells = re.split(r"\s+", source)
    else:
        source = re.sub(r"\s+", "", source)
        cells = tuple(source)
    assert len(cells) == 81
    return Board(DIGITS if cell == "." else Digits(map(int, cell)) for cell in cells)


def parsepic(picture: str):
    if "." in picture:
        return parsepic_init(picture)
    else:
        return parsepic_wide(picture)


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
