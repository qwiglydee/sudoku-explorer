"""Canvas widget to draw board"""

import math
import random
from typing import Iterable, NamedTuple, Self

from ipycanvas import Canvas, MultiCanvas, hold_canvas

from board import Loc, Board
from palette import pick_color

CANVAS_SIZE = 640
FONT_SIZE = 12
FONT = f"{FONT_SIZE}px sans-serif"
FONT_COLORS = {"": "#000000", "HIGH": "#FFFFFF", "FINAL": "#606060"}
BG_COLOR = "#808080"


def segm_rc(seg: int):
    d0 = seg - 1
    return d0 // 3, d0 % 3


class XY(NamedTuple):
    PAD = 6
    CELL = (CANVAS_SIZE - PAD * 2) / 9
    SEGM = CELL / 3

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

    @classmethod
    def ofcell(cls, loc: Loc) -> Self:
        """top-left coords of a cell"""
        return cls((loc.c - 1) * cls.CELL, (loc.r - 1) * cls.CELL)

    def loc(self) -> Loc:
        """map the xy to a cell"""
        return Loc(int(self.y / self.CELL) + 1, int(self.x / self.CELL) + 1)

    @classmethod
    def ofsect(cls, loc1: Loc, loc2: Loc) -> tuple[Self, Self]:
        """top-left and bot-right"""
        p1 = cls.ofcell(loc1)
        p2 = cls.ofcell(loc2)
        return p1, cls(p2.x + cls.CELL, p2.y + cls.CELL)

    @classmethod
    def ofsegm(cls, loc: Loc, seg: int) -> Self:
        """center of a segment"""
        r, c = segm_rc(seg)
        x0, y0 = cls.ofcell(loc)
        return cls(x0 + (c + 0.5) * cls.SEGM, y0 + (r + 0.5) * cls.SEGM)

    def locseg(self) -> tuple[Loc, int]:
        """map the xy to a cell + segm"""
        loc = self.loc()
        scol = int(self.x / self.SEGM)
        srow = int(self.y / self.SEGM)
        return loc, 1 + srow * 3 + scol


P0 = XY(XY.PAD, XY.PAD)

HIGHLIGHT_SIZE = XY.CELL / 3 - 4
HIGHLIGHT_R = HIGHLIGHT_SIZE / 2

WIDTHS = {
    "SOLID": 6,
    "HARD": 6,
    "SOFT": 6,
    "GROUP": XY.SEGM / 2,
}

HIGHLIGHT_COLOR = pick_color("blue")


XYs = tuple[XY, ...]


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
        hlight_cnv.font = FONT
        hlight_cnv.text_baseline = "middle"
        hlight_cnv.text_align = "center"
        hlight_cnv.global_alpha = 0.625
        hlight_cnv.line_cap = "round"

        self.draw_grid()

    def draw_grid(self):
        canvas = self[self.GRID_LAYER]
        fullsize = XY.CELL * 9

        canvas.clear()
        with hold_canvas():
            canvas.fill_style = BG_COLOR
            canvas.fill_rect(P0.x, P0.y, fullsize, fullsize)

            canvas.line_width = 1
            canvas.stroke_style = "rgba(0, 0, 0, 0.25)"
            for i in range(1, 9):
                p9 = XY.add(P0, XY(i * XY.CELL, i * XY.CELL))
                canvas.stroke_line(P0.x, p9.y, P0.x + fullsize, p9.y)
                canvas.stroke_line(p9.x, P0.y, p9.x, P0.y + fullsize)
            canvas.stroke_style = "rgba(0, 0, 0, 0.5)"
            for i in range(1, 3):
                p3 = XY.add(P0, XY(i * XY.CELL * 3, i * XY.CELL * 3))
                canvas.stroke_line(P0.x, p3.y, P0.x + fullsize, p3.y)
                canvas.stroke_line(p3.x, P0.y, p3.x, P0.y + fullsize)
            canvas.line_width = XY.PAD
            canvas.stroke_style = "rgba(0, 0, 0, 1.0)"
            canvas.stroke_rect(P0.x - XY.PAD / 2, P0.y - XY.PAD / 2, fullsize + XY.PAD, fullsize + XY.PAD)

    def draw_board(self, board: Board, highlight: set[int] = set()):
        canvas = self[self.DIGITS_LAYER]

        canvas.clear()
        with hold_canvas():
            for cell in iter(board):
                if cell.is_empty:
                    continue
                for dig in cell.digits:
                    p = XY.add(P0, XY.ofsegm(cell.loc, dig))
                    canvas.font = FONT
                    if cell.is_final:
                        canvas.fill_style = FONT_COLORS["FINAL"]
                    elif dig in highlight:
                        canvas.fill_style = FONT_COLORS["HIGH"]
                    else:
                        canvas.fill_style = FONT_COLORS[""]
                    canvas.fill_text(str(dig), p.x, p.y)

    def clear_highlights(self):
        canvas = self[self.HLIGHT_LAYER]
        canvas.clear()

    def highlight_segment(self, loc: Loc, seg: int, *, color: str = HIGHLIGHT_COLOR):
        canvas = self[self.HLIGHT_LAYER]
        p = XY.ofsegm(loc, seg)
        canvas.set_line_dash([])
        canvas.fill_style = pick_color(color)
        canvas.clear_rect(P0.x + p.x - HIGHLIGHT_R, P0.y + p.y - HIGHLIGHT_R, HIGHLIGHT_SIZE, HIGHLIGHT_SIZE)
        canvas.fill_circle(P0.x + p.x, P0.y + p.y, HIGHLIGHT_R)

    def highlight_link(self, loc1: Loc, seg1: int, loc2: Loc, seg2: int, *, color: str = HIGHLIGHT_COLOR, style: str = "SOLID"):
        canvas = self[self.HLIGHT_LAYER]
        p1 = XY.add(P0, XY.ofsegm(loc1, seg1))
        p2 = XY.add(P0, XY.ofsegm(loc2, seg2))
        canvas.line_width = WIDTHS[style]
        canvas.stroke_style = pick_color(color)

        length = max(1, math.ceil(XY.dist(p1, p2) / XY.CELL))

        if style == "HARD":
            points = tuple(split_line(p1, p2, n=2))
            points = tuple(jig_line(points, XY.SEGM))
            canvas.set_line_dash([])
            stroke_quadsmooth_path(canvas, points)
        elif style == "SOFT":
            points = tuple(split_line(p1, p2, n=2 * length))
            points = tuple(jig_line(points, XY.SEGM))
            canvas.set_line_dash([8, 16])
            stroke_quadsmooth_path(canvas, points)
        else:
            canvas.set_line_dash([])
            canvas.stroke_line(p1.x, p1.y, p2.x, p2.y)


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
    tng = XY((points[-1].x - points[0].x) / lng, (points[-1].y - points[0].y) / lng)
    nrm = XY(-tng.y, tng.x)

    yield points[0]
    for p in points[1:-1]:
        offset = random.uniform(-maxoffset, +maxoffset)
        yield XY(p.x + nrm.x * offset, p.y + nrm.y * offset)
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
