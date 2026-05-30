import math
from typing import Iterable, NamedTuple, Self
from ipycanvas import MultiCanvas, hold_canvas
from palette import pick_color

from board import Board, Loc

CANVAS_SIZE = 640
PADDING = 4
CELL_SIZE = (640 - PADDING * 2) / 9
SEGM_SIZE = CELL_SIZE / 3
FONT1_SIZE = 12
FONT1 = f"{FONT1_SIZE}px sans-serif"
FONT1_COLOR = "#000"
FONT2_SIZE = 32
FONT2 = f"{FONT2_SIZE}px sans-serif"
FONT2_COLOR = "#AAA"

HIGHLIGHT_SIZE = CELL_SIZE / 3 - 4
HIGHLIGHT_R = HIGHLIGHT_SIZE / 2
FINAL_R = HIGHLIGHT_R + 3
GROUP_WIDTH = 6
LINK_WIDTH = 4

DASHES = {
    "SOLID": [],
    "HARD": [],
    "SOFT": [LINK_WIDTH * 2, LINK_WIDTH * 0.5],
}


HIGHLIGHT_COLOR = pick_color("blue")


class XY(NamedTuple):
    x: float
    y: float

    @classmethod
    def mid(cls, p1: Self, p2: Self) -> Self:
        return cls((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)

    @classmethod
    def dist(cls, p1: Self, p2: Self) -> float:
        return math.sqrt(p1.x * p2.x + p1.y * p2.y)


P0 = XY(PADDING, PADDING)


def cell_xy(loc: Loc):
    """top-bot coords of a cell"""
    return XY((loc.col - 1) * CELL_SIZE, (loc.row - 1) * CELL_SIZE)


def xy_cell(p: XY) -> Loc:
    return Loc(int(p.y / CELL_SIZE) + 1, int(p.x / CELL_SIZE) + 1)


def segm_rc(seg: int):
    """sub-loc of a segment in a cell"""
    d0 = seg - 1
    return d0 // 3, d0 % 3


def segm_xy(seg: int):
    """coords of a segment in a cell"""
    r, c = segm_rc(seg)
    return XY((c + 0.5) * SEGM_SIZE, (r + 0.5) * SEGM_SIZE)


def xy_segm(p: XY) -> int:
    c = int(p.x / SEGM_SIZE)
    r = int(p.y / SEGM_SIZE)
    return 1 + r * 3 + c


def targ_xy(loc: Loc, seg: int):
    c = cell_xy(loc)
    s = segm_xy(seg)
    return XY(c.x + s.x, c.y + s.y)


class SudokuCanvas(MultiCanvas):
    def __init__(self):
        super().__init__(3, width=CANVAS_SIZE, height=CANVAS_SIZE)

    def draw_grid(self):
        canvas = self[0]
        size = CELL_SIZE * 9

        canvas.clear()
        with hold_canvas():
            canvas.stroke_style = "rgba(0, 0, 0, 0.25)"
            for i in range(1, 9):
                c9 = XY(i * CELL_SIZE, i * CELL_SIZE)
                canvas.stroke_line(P0.x, P0.x + c9.y, P0.x + size, P0.y + c9.y)
                canvas.stroke_line(P0.x + c9.x, P0.y, P0.x + c9.x, P0.y + size)
            canvas.stroke_style = "rgba(0, 0, 0, 0.5)"
            for i in range(1, 3):
                c3 = XY(i * CELL_SIZE * 3, i * CELL_SIZE * 3)
                canvas.stroke_line(P0.x, P0.y + c3.y, P0.x + size, P0.y + c3.y)
                canvas.stroke_line(P0.x + c3.x, P0.y, P0.x + c3.x, P0.y + size)
            canvas.line_width = 3
            canvas.stroke_style = "rgba(0, 0, 0, 1.0)"
            canvas.stroke_rect(P0.x, P0.y, size, size)

    def draw_board(self, board: Board):
        canvas = self[1]
        canvas.text_baseline = "middle"
        canvas.text_align = "center"

        canvas.clear()
        with hold_canvas():
            for node in board:
                if node.cell.is_empty:
                    continue

                c = cell_xy(node.loc)
                if node.cell.is_final:
                    value = node.cell.final
                    canvas.font = FONT2
                    canvas.fill_style = FONT2_COLOR
                    canvas.fill_text(str(value), P0.x + c.x + 0.5 * CELL_SIZE, P0.x + c.y + 0.5 * CELL_SIZE)
                else:
                    for dig in range(1, 10):
                        if dig not in node.cell:
                            continue
                        s = segm_xy(dig)
                        canvas.font = FONT1
                        canvas.fill_style = FONT1_COLOR
                        # NB: text is centered
                        canvas.fill_text(str(dig), P0.x + c.x + s.x, P0.y + c.y + s.y)

    def clear_highlights(self):
        canvas = self[2]
        canvas.clear()

    def highlight_segment(self, loc: Loc, seg: int, *, color: str = HIGHLIGHT_COLOR):
        canvas = self[2]
        c = cell_xy(loc)
        s = segm_xy(seg)
        canvas.set_line_dash([])
        canvas.fill_style = pick_color(color)
        canvas.clear_rect(P0.x + c.x + s.x - HIGHLIGHT_R, P0.y + c.y + s.y - HIGHLIGHT_R, HIGHLIGHT_SIZE, HIGHLIGHT_SIZE)
        canvas.fill_circle(P0.x + c.x + s.x, P0.y + c.y + s.y, HIGHLIGHT_R)

    def highlight_segments(self, loc: Loc, segs: Iterable[int], *, color: str = HIGHLIGHT_COLOR):
        canvas = self[2]
        c = cell_xy(loc)
        for seg in segs:
            s = segm_xy(seg)
            canvas.set_line_dash([])
            canvas.fill_style = pick_color(color)
            canvas.clear_rect(P0.x + c.x + s.x - HIGHLIGHT_R, P0.y + c.y + s.y - HIGHLIGHT_R, HIGHLIGHT_SIZE, HIGHLIGHT_SIZE)
            canvas.fill_circle(P0.x + c.x + s.x, P0.y + c.y + s.y, HIGHLIGHT_R)

    def highlight_final(self, loc: Loc, seg: int, *, color: str = HIGHLIGHT_COLOR):
        canvas = self[2]
        c = cell_xy(loc)
        s = segm_xy(seg)
        canvas.set_line_dash([])
        canvas.fill_style = pick_color(color)
        canvas.fill_circle(P0.x + c.x + s.x, P0.y + c.y + s.y, FINAL_R)

    def highlight_link(self, loc1: Loc, seg1: int, loc2: Loc, seg2: int, *, color: str = HIGHLIGHT_COLOR, style: str = "SOLID"):
        canvas = self[2]
        t1 = targ_xy(loc1, seg1)
        t2 = targ_xy(loc2, seg2)
        canvas.set_line_dash(DASHES[style])
        canvas.line_width = LINK_WIDTH
        canvas.stroke_style = pick_color(color)
        canvas.stroke_line(P0.x + t1.x, P0.y + t1.y, P0.x + t2.x, P0.y + t2.y)
