import math
import random
from typing import Iterable, NamedTuple, Self

from ipycanvas import Canvas, MultiCanvas, hold_canvas

from board import Board, Loc
from palette import pick_color

CANVAS_SIZE = 640
PADDING = 4
CELL_SIZE = (640 - PADDING * 2) / 9
SEGM_SIZE = CELL_SIZE / 3
FONT1_SIZE = 12
FONT1 = f"{FONT1_SIZE}px sans-serif"
FONT2_SIZE = 32
FONT2 = f"{FONT2_SIZE}px sans-serif"
FONT_COLOR = "#000000"
BG_COLOR = "#808080"

HIGHLIGHT_SIZE = CELL_SIZE / 3
HIGHLIGHT_R = HIGHLIGHT_SIZE / 2 - 2

WIDTHS = {
    "HARD": 6,
    "SOFT": 6,
    "SOLID": 6,
    "GROUP": SEGM_SIZE - 2,
}

DASHES = {
    "SOLID": [],
    "HARD": [],
    "SOFT": [3, 3],
}


HIGHLIGHT_COLOR = pick_color("blue")


class XY(NamedTuple):
    x: float
    y: float

    @classmethod
    def mid(cls, p1: Self, p2: Self) -> Self:
        return cls((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)

    @classmethod
    def add(cls, p1: Self, p2: Self) -> Self:
        return cls(p1.x + p2.x, p1.y + p2.y)

    @classmethod
    def dist(cls, p1: Self, p2: Self) -> float:
        v = XY(p2.x - p1.x, p2.y - p1.y)
        return math.sqrt(v.x * v.x + v.y * v.y)


XYs = tuple[XY, ...]


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
    GRID_LAYER = 0
    DIGITS_LAYER = 2
    HLIGHT_LAYER = 1

    def __init__(self):
        super().__init__(3, width=CANVAS_SIZE, height=CANVAS_SIZE)
        self.on_client_ready(self.setup)

    def setup(self):
        digits_cnv = self[self.DIGITS_LAYER]
        digits_cnv.text_baseline = "middle"
        digits_cnv.text_align = "center"

        hlight_cnv = self[self.HLIGHT_LAYER]
        hlight_cnv.font = FONT1
        hlight_cnv.text_baseline = "middle"
        hlight_cnv.text_align = "center"
        hlight_cnv.global_alpha = 0.625

        self.draw_grid()

    def draw_grid(self):
        canvas = self[self.GRID_LAYER]
        size = CELL_SIZE * 9

        canvas.clear()
        with hold_canvas():
            canvas.fill_style = BG_COLOR
            canvas.fill_rect(P0.x, P0.y, size, size)

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
        canvas = self[self.DIGITS_LAYER]

        canvas.clear()
        with hold_canvas():
            for node in board:
                if node.cell.is_empty:
                    continue

                c = cell_xy(node.loc)
                if node.cell.is_final:
                    value = node.cell.final
                    canvas.font = FONT2
                    canvas.fill_style = FONT_COLOR
                    canvas.fill_text(str(value), P0.x + c.x + 0.5 * CELL_SIZE, P0.x + c.y + 0.5 * CELL_SIZE)
                else:
                    for dig in range(1, 10):
                        if dig not in node.cell:
                            continue
                        s = segm_xy(dig)
                        canvas.font = FONT1
                        canvas.fill_style = FONT_COLOR
                        canvas.fill_text(str(dig), P0.x + c.x + s.x, P0.y + c.y + s.y)

    def highlight_digit(self, loc: Loc, seg: int, text: str):
        canvas = self[self.HLIGHT_LAYER]
        c = cell_xy(loc)
        s = segm_xy(seg)
        canvas.fill_style = FONT_COLOR
        # NB: text is centered
        canvas.fill_text(text, P0.x + c.x + s.x, P0.y + c.y + s.y)

    def clear_highlights(self):
        canvas = self[self.HLIGHT_LAYER]
        canvas.clear()

    def highlight_segment(self, loc: Loc, seg: int, *, color: str = HIGHLIGHT_COLOR):
        canvas = self[self.HLIGHT_LAYER]
        c = cell_xy(loc)
        s = segm_xy(seg)
        canvas.set_line_dash([])
        canvas.fill_style = pick_color(color)
        canvas.clear_rect(P0.x + c.x + s.x - HIGHLIGHT_R, P0.y + c.y + s.y - HIGHLIGHT_R, HIGHLIGHT_SIZE, HIGHLIGHT_SIZE)
        canvas.fill_circle(P0.x + c.x + s.x, P0.y + c.y + s.y, HIGHLIGHT_R)

    def highlight_link(self, loc1: Loc, seg1: int, loc2: Loc, seg2: int, *, color: str = HIGHLIGHT_COLOR, style: str = "SOLID"):
        canvas = self[self.HLIGHT_LAYER]
        t1 = XY.add(P0, targ_xy(loc1, seg1))
        t2 = XY.add(P0, targ_xy(loc2, seg2))
        canvas.set_line_dash(DASHES[style])
        canvas.line_width = WIDTHS[style]
        canvas.stroke_style = pick_color(color)

        length = max(1, math.ceil(XY.dist(t1, t2) / CELL_SIZE))

        if style == "HARD":
            points = tuple(split_line(t1, t2, n=1 + length // 2))
            points = tuple(jig_line(points, SEGM_SIZE))
            stroke_quadsmooth_path(canvas, points)
        elif style == "SOFT":
            points = tuple(split_line(t1, t2, n=2 * length))
            points = tuple(jig_line(points, SEGM_SIZE))
            stroke_quadsmooth_path(canvas, points)
        else:
            canvas.stroke_line(t1.x, t1.y, t2.x, t2.y)


def split_line(p1: XY, p2: XY, n: int) -> Iterable[XY]:
    """Split line into n segments"""
    dx = (p2.x - p1.x) / n
    dy = (p2.y - p1.y) / n
    yield p1
    for i in range(1, n):
        yield XY(p1.x + dx * i, p1.y + dy * i)
    yield p2


def jig_line(points: XYs, maxoffset: float) -> Iterable[XY]:
    """Shift internal points to ±offset perpendicular to main line"""

    lng = XY.dist(points[0], points[-1])
    dir = XY((points[-1].x - points[0].x) / lng, (points[-1].y - points[0].y) / lng)
    tng = XY(-dir.y, dir.x)

    yield points[0]
    for p in points[1:-1]:
        offset = random.uniform(-maxoffset, +maxoffset)
        yield XY(p.x + tng.x * offset, p.y + tng.y * offset)
    yield points[-1]


def stroke_quadsmooth_path(canvas: Canvas, points: XYs):
    """Stroking through midpoints using original points as controls"""
    midpoints = [XY.mid(points[i], points[i + 1]) for i in range(len(points) - 1)]
    canvas.begin_path()
    canvas.move_to(points[0].x, points[0].y)
    canvas.line_to(midpoints[0].x, midpoints[0].y)
    for p, m in zip(points[1:], midpoints[1:]):
        canvas.quadratic_curve_to(p.x, p.y, m.x, m.y)
    canvas.line_to(points[-1].x, points[-1].y)
    canvas.stroke()
