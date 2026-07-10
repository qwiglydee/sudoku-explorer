from itertools import chain as iterchain
from typing import Iterable, NamedTuple, Self

from board import Digits, Loc, Cell
from topology import EVERY, Zone

iterflat = iterchain.from_iterable


class Node(NamedTuple):
    """Node of relation
    Generalized representation of draft assignments:
    - one or multiple cells
    - one or multiple digits
    """

    zone: Zone
    digits: Digits  # why tho ?

    @property
    def is_cellular(self) -> bool:
        return self.zone.is_cell

    @property
    def is_singular(self) -> bool:
        return len(self.digits) == 1

    @property
    def is_casual(self) -> bool:
        return self.is_cellular and self.is_singular

    @property
    def is_triplet(self) -> bool:
        return self.zone.box is not EVERY and (self.zone.row is not EVERY or self.zone.col is not EVERY)

    @classmethod
    def C(cls, cell: Cell):
        return cls(Zone.L(cell.loc), cell.digits)

    @property
    def loc(self) -> Loc:
        assert self.is_cellular
        return self.zone.loc()

    @property
    def dig(self) -> int:
        assert self.is_singular
        return tuple(self.digits)[0]

    def cell(self):
        assert self.is_cellular
        return Cell(self.zone.loc(), self.digits)

    @classmethod
    def at(cls, where: Loc | Zone | Cell, what: int | Iterable[int]) -> Self:
        digits = Digits((what,)) if isinstance(what, int) else Digits(what)

        if isinstance(where, Zone):
            return cls(where, digits)
        if isinstance(where, Loc):
            return cls(Zone.L(where), digits)
        if isinstance(where, Cell):
            return cls(Zone.L(where.loc), digits)
        raise TypeError()

    @classmethod
    def forz(cls, where: Loc | Zone) -> Self:
        if isinstance(where, Zone):
            return cls(where, Digits())
        if isinstance(where, Loc):
            return cls(Zone.L(where), Digits())
        raise TypeError()

    def __str__(self):
        cont = "".join(map(str, sorted(self.digits)))
        return f"{cont}@{self.zone}"

    def matching(self, cell: Cell) -> Cell:
        """Check if a cell has some digits targeted by the node"""
        return Cell(cell.loc, Digits(cell.digits & self.digits))

    def spoiling(self, cell: Cell) -> Cell:
        """Check if a cell has digits not targeted by the node"""
        return Cell(cell.loc, Digits(cell.digits - self.digits))


def cellmatching(node: Node, cells: Iterable[Cell]) -> Iterable[Cell]:
    matching = (node.matching(cell) for cell in cells)
    return (res for res in matching if len(res))


def cellspoiling(node: Node, cells: Iterable[Cell]) -> Iterable[Cell]:
    matching = (node.spoiling(cell) for cell in cells)
    return (res for res in matching if len(res))
