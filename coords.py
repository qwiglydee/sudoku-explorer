"""Utils to handle coords"""

from board import Loc

POS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def box4loc(loc: Loc) -> int:
    assert 1 <= loc.r <= 9 and 1 <= loc.c <= 9
    r0 = (loc.r - 1) // 3 * 3
    c0 = (loc.c - 1) // 3
    return r0 + c0 + 1


def box4row(row: int) -> tuple[int, int, int]:
    assert 1 <= row <= 9
    b0 = (row - 1) // 3 * 3
    return (b0 + 1, b0 + 2, b0 + 3)


def box4col(col: int) -> tuple[int, int, int]:
    assert 1 <= col <= 9
    b0 = (col - 1) // 3
    return (b0 + 1, b0 + 4, b0 + 7)


def row4box(box: int) -> tuple[int, int, int]:
    assert 1 <= box <= 9
    r0 = (box - 1) // 3 * 3
    return (r0 + 1, r0 + 2, r0 + 3)


def col4box(box: int) -> tuple[int, int, int]:
    assert 1 <= box <= 9
    c0 = (box - 1) % 3 * 3
    return (c0 + 1, c0 + 2, c0 + 3)
