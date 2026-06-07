from functools import reduce
from itertools import chain as iterchain
from typing import Iterable, NamedTuple, Self

from board import Cell, Digits, Loc
from topology import Zone

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

    @classmethod
    def C(cls, cell: Cell):
        return cls(Zone.L(cell.loc), cell.digits)

    def loc(self) -> Loc:
        assert self.is_cellular
        return self.zone.loc()

    def dig(self) -> int:
        assert self.is_singular
        return tuple(self.digits)[0]

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

    def __contains__(self, other: Cell | Self):
        if isinstance(other, Cell):
            return other.loc in self.zone and other.digits <= self.digits
        if isinstance(other, self.__class__):
            return other.zone <= self.zone and other.digits <= self.digits

        raise TypeError()


class Group(frozenset[Node]):
    # TODO
    pass


class Link(tuple[Node, Node]):
    """Ordered immutable pair of nodes"""

    # ordered for chains, unordered for comparision

    CHAR = "~"

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

    @classmethod
    def init(cls, link: HLink):
        assert isinstance(link, HLink)
        return cls((link,))

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

    @property
    def edges(self) -> tuple[Node, Node]:
        return (self[0][0], self[-1][1])

    @property
    def is_loop(self):
        return self[0][0] == self[-1][1]

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
