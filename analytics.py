from typing import Iterable, NamedTuple, Self

from board import Board, Loc, Locality, Node
from utils import iterflat, zoneflat


def visible_locs(l1: Loc, l2: Loc) -> Iterable[Loc]:
    """All locs visible from both the locs"""

    # they share some localities
    visible = set(zoneflat(Locality.shared(l1, l2)))
    if visible:
        return visible

    # intersection of their arounds
    visible = set(zoneflat(Locality.around(l1))) & set(zoneflat(Locality.around(l2)))
    return visible


class Target(NamedTuple):
    """Target digit-segment inside a cell"""

    loc: Loc
    dig: int

    def __contains__(self, dig: int) -> bool:
        return dig == self.dig

    @classmethod
    def check_nand(cls, t1: Self, t2: Self) -> bool:
        l1, l2 = t1.loc, t2.loc
        if t1.dig == t2.dig:
            return l1.blk == l2.blk or l1.row == l2.row or l1.col == l2.col
        else:
            return l1 == l2

    @classmethod
    def check_xor(cls, board: Board, t1: Self, t2: Self) -> bool:
        l1, l2 = t1.loc, t2.loc
        if t1.dig == t2.dig:

            def occupied(zone):
                return tuple(board.slice(zone, lambda n: t1.dig in n.cell))

            # some shared zone has only 2 cell with the digit
            return any(len(occupied(zone)) == 2 for zone in Locality.shared(l1, l2))
        else:
            # different digits in a single cell
            return l1 == l2 and len(board.get(l1).cell) == 2

    def __str__(self):
        return f"{self.dig}{self.loc}"

    @classmethod
    def iter_node(cls, node: Node) -> Iterable[Self]:
        return (cls(node.loc, d) for d in node.cell)


class MultiTarget(NamedTuple):
    """Target multiple digit-segment inside a cell"""

    loc: Loc
    digs: frozenset[int]

    def __str__(self):
        joined = "".join(map(str, self.digs))
        return f"{joined}{self.loc}"


class Link(tuple[Target, Target]):
    """Ordered immutable pair of targets"""

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
        return f"{self[0]}{self.CHAR}{self[1]}"


class HLink(Link):
    """Hard link, XOR relation"""

    CHAR = "⟺"


class SLink(Link):
    """Soft link, NAND relation"""

    CHAR = "⟷"


class Chain(tuple[Link, ...]):
    """Chain of alterating links"""

    # totally ordered, unordered for comparision

    ALTERATING = [SLink, HLink]

    @classmethod
    def init(cls, link: HLink):
        assert isinstance(link, HLink)
        return cls((link,))

    @classmethod
    def extend(cls, chain: Self, *links: Link) -> Self:
        """Add some links to end of the chain"""
        assert all(isinstance(l, cls.ALTERATING[i % 2]) for i, l in enumerate(links))
        assert chain[-1][-1] == links[0][0]
        return cls((*chain, *links))

    def anchors(self) -> set[Target]:
        """All anchor points in the chain"""
        return set(iterflat(self))

    @property
    def edges(self) -> tuple[Target, Target]:
        return (self[0][0], self[-1][1])

    @property
    def is_loop(self):
        return self[0][0] == self[-1][1]

    def __eq__(self, other: Self):
        return frozenset(self) == frozenset(other)

    def __hash__(self):
        return hash(frozenset(self))

    def __str__(self):
        return "".join((str(self[0][0]), *(f"{lnk.CHAR}{lnk[1]}" for lnk in self[1:])))
