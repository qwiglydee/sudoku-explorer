from typing import Iterable
from ipycanvas import MultiCanvas, hold_canvas

from board import Board, Loc, Node, Target

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

HIGHLIGHT_SIZE = 20
HIGHLIGHT_R = HIGHLIGHT_SIZE / 2
HIGHLIGHT_WIDTH = 3

LINK_WIDTH = 4

DASHES = {
    "SOLID": [],
    "HARD": [],
    "SOFT": [LINK_WIDTH * 2, LINK_WIDTH * 0.5],
}


# matplotlib
PALETTE_T10 = {
    "blue": "#1f77b4",
    "orange": "#ff7f0e",
    "green": "#2ca02c",
    "red": "#d62728",
    "purple": "#9467bd",
    "brown": "#8c564b",
    "pink": "#e377c2",
    "gray": "#7f7f7f",
    "olive": "#bcbd22",
    "cyan": "#17becf",
}

HIGHLIGHT_COLOR = PALETTE_T10["blue"]


def digit_rc(d: int):
    d0 = d - 1
    return d0 // 3, d0 % 3


def cell_xy(loc: Loc):
    """top-bot coords of a cell"""
    return (loc.col - 1) * CELL_SIZE, (loc.row - 1) * CELL_SIZE


def segm_rc(d: int):
    """sub-loc of a segment in a cell"""
    d0 = d - 1
    return d0 // 3, d0 % 3


def segm_xy(loc: Loc, segm: int):
    """center coords of a segment in a cell"""
    x0, y0 = cell_xy(loc)
    r, c = segm_rc(segm)
    return x0 + (c + 0.5) * SEGM_SIZE, y0 + (r + 0.5) * SEGM_SIZE


class SudokuCanvas(MultiCanvas):
    def __init__(self):
        super().__init__(3, width=CANVAS_SIZE, height=CANVAS_SIZE)

    def draw_grid(self):
        canvas = self[0]
        x0, y0 = PADDING, PADDING
        size = CELL_SIZE * 9

        canvas.clear()
        with hold_canvas():
            canvas.stroke_style = "rgba(0, 0, 0, 0.25)"
            for i in range(1, 9):
                yi = y0 + i * CELL_SIZE
                xi = x0 + i * CELL_SIZE
                canvas.stroke_line(x0, yi, x0 + size, yi)
                canvas.stroke_line(xi, y0, xi, y0 + size)
            canvas.stroke_style = "rgba(0, 0, 0, 0.5)"
            for i in range(1, 3):
                yi = y0 + i * CELL_SIZE * 3
                canvas.stroke_line(x0, yi, x0 + size, yi)
                xi = x0 + i * CELL_SIZE * 3
                canvas.stroke_line(xi, y0, xi, y0 + size)
            canvas.line_width = 3
            canvas.stroke_style = "rgba(0, 0, 0, 1.0)"
            canvas.stroke_rect(x0, y0, size, size)

    def draw_board(self, board: Board):
        x0, y0 = PADDING, PADDING
        canvas = self[1]
        canvas.text_baseline = "middle"
        canvas.text_align = "center"

        canvas.clear()
        with hold_canvas():
            for node in board:
                if node.cell.is_empty:
                    continue

                if node.cell.is_final:
                    x, y = cell_xy(node.loc)
                    value = node.cell[0]
                    canvas.font = FONT2
                    canvas.fill_style = FONT2_COLOR
                    canvas.fill_text(str(value), x0 + x + 0.5 * CELL_SIZE, y0 + y + 0.5 * CELL_SIZE)
                else:
                    for d in range(1, 10):
                        if d not in node.cell:
                            continue
                        x, y = segm_xy(node.loc, d)
                        canvas.font = FONT1
                        canvas.fill_style = FONT1_COLOR
                        canvas.fill_text(str(d), x0 + x, y0 + y + 1)

    def clear_highlights(self):
        canvas = self[2]
        canvas.clear()

    def highlight_target(self, target: Target, *, color: str = HIGHLIGHT_COLOR):
        canvas = self[2]
        x0, y0 = PADDING, PADDING
        x, y = segm_xy(target.loc, target.seg)
        x += x0
        y += y0
        canvas.set_line_dash([])
        canvas.line_width = HIGHLIGHT_WIDTH
        canvas.fill_style = color
        canvas.clear_rect(x - HIGHLIGHT_R, y - HIGHLIGHT_R, HIGHLIGHT_SIZE, HIGHLIGHT_SIZE)
        canvas.fill_circle(x, y, HIGHLIGHT_R)

    def highlight_link(self, link: tuple[Target, Target], *, color: str = HIGHLIGHT_COLOR, style: str = "SOLID"):
        canvas = self[2]
        x0, y0 = PADDING, PADDING
        t1, t2 = link
        x1, y1 = segm_xy(t1.loc, t1.seg)
        x2, y2 = segm_xy(t2.loc, t2.seg)
        canvas.set_line_dash(DASHES[style])
        canvas.line_width = LINK_WIDTH
        canvas.stroke_style = color
        canvas.stroke_line(x0 + x1, y0 + y1, x0 + x2, y0 + y2)
