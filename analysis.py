from functools import reduce
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
    digits: Digits

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

    def loc(self) -> Loc:
        assert self.is_cellular
        return self.zone.loc()

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


class MultiNode(frozenset[Node]):
    # TODO
    pass


class Link(tuple[Node, Node]):
    """Ordered immutable pair of nodes"""

    # ordered for chains, unordered for comparision

    CHAR = "~"

    @property
    def is_casual(self):
        return self[0].is_casual and self[1].is_casual

    @property
    def is_bival(self):
        n1, n2 = self
        return self.is_casual and n1.loc() == n2.loc() and n1.dig() != n2.dig()

    @property
    def is_biloc(self):
        n1, n2 = self
        return self.is_casual and n1.loc() != n2.loc() and n1.dig() == n2.dig()

    def reversed(self) -> Self:
        return self.__class__((self[1], self[0]))

    def __eq__(self, other):
        return frozenset(self) == frozenset(other)

    def __hash__(self):
        return hash(frozenset((self)))

    def __repr__(self):
        return f"{self.__class__.__name__}(({self[0]!r}, {self[1]!r},))"

    def __str__(self):
        return f"({self[0]} {self.CHAR} {self[1]})"


class HLink(Link):
    CHAR = "⊻"


class SLink(Link):
    CHAR = "⊼"


class Chain(tuple[Link, ...]):
    """Chain of alterating links"""

    # totally ordered, unordered for comparision

    ALTERATING = [HLink, SLink]

    @property
    def edges(self) -> tuple[Node, Node]:
        return (self[0][0], self[-1][-1])

    @property
    def is_loop(self):
        e1, e2 = self.edges
        return e1 == e2

    @property
    def is_hardend(self):
        return isinstance(self[0], HLink) and isinstance(self[-1], HLink)

    @classmethod
    def extend(cls, chain: Self, *links: Link) -> Self:
        """Add some links to end of the chain"""
        assert all(isinstance(lnk, cls.ALTERATING[i % 2]) for i, lnk in enumerate(links, 1))
        assert chain[-1][-1] == links[0][0]
        return cls((*chain, *links))

    @classmethod
    def extendhead(cls, chain: Self, *links: Link) -> Self:
        assert all(isinstance(lnk, cls.ALTERATING[i % 2]) for i, lnk in enumerate(links))
        assert chain[0][0] == links[-1][-1]
        return cls((*links, *chain))

    def anchors(self) -> set[Node]:
        """All anchor points in the chain"""
        return set(iterflat(self))

    def __eq__(self, other: Self):
        return frozenset(self) == frozenset(other)

    def __hash__(self):
        return hash(frozenset(self))

    def __str__(self):
        def strtail(lnk):
            return f" {lnk.CHAR} {lnk[1]}"

        joined = reduce(lambda a, lnk: a + strtail(lnk), self, str(self[0][0]))

        if self.is_loop:
            return f"(… {joined} …)"
        else:
            return f"({joined})"
