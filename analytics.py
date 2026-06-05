from functools import reduce
from itertools import chain as iterchain, product as iterprod
from types import EllipsisType
from typing import Iterable, Iterator, NamedTuple, Self

from board import DIGITS, Board, Loc, Node

iterflat = iterchain.from_iterable

Every = EllipsisType
EVERY = Ellipsis


class Topo:
    """Relations between blocks/rows/cols

    Defines topology of the board
    """

    IDX = (1, 2, 3, 4, 5, 6, 7, 8, 9)

    blks = IDX
    rows = IDX
    cols = IDX

    @staticmethod
    def blk4loc(row: int, col: int) -> int:
        assert 1 <= row <= 9 and 1 <= col <= 9
        r0 = (row - 1) // 3 * 3
        c0 = (col - 1) // 3
        return r0 + c0 + 1

    @staticmethod
    def blk4row(row: int) -> tuple[int, int, int]:
        assert 1 <= row <= 9
        b0 = (row - 1) // 3 * 3
        return (b0 + 1, b0 + 2, b0 + 3)

    @staticmethod
    def blk4col(col: int) -> tuple[int, int, int]:
        assert 1 <= col <= 9
        b0 = (col - 1) // 3
        return (b0 + 1, b0 + 4, b0 + 7)

    @staticmethod
    def row4blk(blk: int) -> tuple[int, int, int]:
        assert 1 <= blk <= 9
        r0 = (blk - 1) // 3 * 3
        return (r0 + 1, r0 + 2, r0 + 3)

    @staticmethod
    def col4blk(blk: int) -> tuple[int, int, int]:
        assert 1 <= blk <= 9
        c0 = (blk - 1) % 3 * 3
        return (c0 + 1, c0 + 2, c0 + 3)

    @staticmethod
    def valid(blk: int | Every, row: int | Every, col: int | Every) -> bool:
        # hard constraints
        assert blk is EVERY or 1 <= blk <= 9  # type: ignore
        assert row is EVERY or 1 <= row <= 9  # type: ignore
        assert col is EVERY or 1 <= col <= 9  # type: ignore

        # soft constraints
        try:
            if isinstance(blk, int):
                if isinstance(row, int):
                    assert row in Topo.row4blk(blk)
                if isinstance(col, int):
                    assert col in Topo.col4blk(blk)
            else:
                assert row is EVERY or col is EVERY
            return True
        except AssertionError:
            return False


class Zone(NamedTuple):
    """Secition or subsection of the board

    Defines visibility relations.
    The class implements set-like operations
    """

    blk: int | EllipsisType
    row: int | EllipsisType
    col: int | EllipsisType

    @classmethod
    def B(cls, blk: int) -> Self:
        assert 1 <= blk <= 9
        return cls(blk, ..., ...)

    @classmethod
    def R(cls, row: int) -> Self:
        assert 1 <= row <= 9
        return cls(..., row, ...)

    @classmethod
    def C(cls, col: int) -> Self:
        assert 1 <= col <= 9
        return cls(..., ..., col)

    @classmethod
    def L(cls, row: int, col: int) -> Self:
        assert 1 <= row <= 9 and 1 <= col <= 9
        return cls(Topo.blk4loc(row, col), row, col)

    @classmethod
    def Allblk(cls) -> Iterable[Self]:
        return (cls(b, ..., ...) for b in Topo.blks)

    @classmethod
    def Allrow(cls) -> Iterable[Self]:
        return (cls(..., r, ...) for r in Topo.rows)

    @classmethod
    def Allcol(cls) -> Iterable[Self]:
        return (cls(..., ..., c) for c in Topo.cols)

    @classmethod
    def All(cls) -> Iterable[Self]:
        yield from cls.Allblk()
        yield from cls.Allrow()
        yield from cls.Allcol()

    # invalid blk may occur because of all the mess around

    def valid(self) -> bool:
        return Topo.valid(self.blk, self.row, self.col)

    @property
    def is_everything(self):
        # it may appear in some calculations
        return self.blk is EVERY and self.row is EVERY and self.col is EVERY

    @property
    def is_cellular(self):
        return self.row is not EVERY and self.col is not EVERY

    @property
    def is_major(self):
        return sum(a is not EVERY for a in (self.blk, self.row, self.col)) == 1

    @classmethod
    def of(cls, what: Node | Loc | Self):
        if isinstance(what, cls):
            return what
        if isinstance(what, Loc):
            return cls(Topo.blk4loc(what.row, what.col), what.row, what.col)
        if isinstance(what, Node):
            loc = what.loc
            return cls(Topo.blk4loc(loc.row, loc.col), loc.row, loc.col)
        raise ValueError()

    def loc(self) -> Loc:
        assert isinstance(self.row, int) and isinstance(self.col, int)
        return Loc(self.row, self.col)

    @classmethod
    def intersection(cls, zone1: Self, zone2: Self) -> Self | None:
        """Intersection of zones
        == visible from both zones
        """
        if zone1.is_everything:  # WHY?
            return zone2
        if zone2.is_everything:  # WHY?
            return zone1

        assert zone1.valid() and zone2.valid()

        if zone1 == zone2:
            return zone1

        def eqe(cell, zone):
            # if a cellular zone matches some another zone
            return (zone.blk == EVERY or zone.blk == cell.blk) and (zone.row == EVERY or zone.row == cell.row) and (zone.col is EVERY or zone.col == cell.col)

        if zone1.is_cellular:
            return zone1 if eqe(zone1, zone2) else None
        if zone2.is_cellular:
            return zone2 if eqe(zone2, zone1) else None

        def validated(b, r, c):
            return cls(b, r, c) if Topo.valid(b, r, c) else None

        # TODO: optimize the shit
        match zone1.blk, zone1.row, zone1.col, zone2.blk, zone2.row, zone2.col:
            case Every(), int(r1), Every(), Every(), Every(), int(c2):  # R & C
                return cls(Topo.blk4loc(r1, c2), r1, c2)
            case Every(), Every(), int(c1), Every(), int(r2), Every():  # C & R
                return cls(Topo.blk4loc(r2, c1), r2, c1)
            case int(b1), Every(), Every(), Every(), int(r2), Every():  # B & R
                return validated(b1, r2, ...)
            case int(b1), Every(), Every(), Every(), Every(), int(c2):  # B & C
                return validated(b1, ..., c2)
            case Every(), int(r1), Every(), int(b2), Every(), Every():  # R & B
                return validated(b2, r1, ...)
            case Every(), Every(), int(c1), int(b2), Every(), Every():  # C & B
                return validated(b2, ..., c1)
            # overlapping cases
            case int(b1), int(r1), Every(), int(b2), Every(), Every():  # BR & B
                return zone1 if b1 == b2 else None
            case int(b1), int(r1), Every(), Every(), int(r2), Every():  # BR & R
                return zone1 if r1 == r2 else None
            case int(b1), Every(), int(c1), int(b2), Every(), Every():  # BC & B
                return zone1 if b1 == b2 else None
            case int(b1), Every(), int(c1), Every(), Every(), int(c2):  # BC & C
                return zone1 if c1 == c2 else None
            case int(b1), Every(), Every(), int(b2), int(r2), Every():  # B & BR
                return zone2 if b1 == b2 else None
            case Every(), int(r1), Every(), int(b2), int(r2), Every():  # R & BR
                return zone2 if r1 == r2 else None
            case int(b1), Every(), Every(), int(b2), Every(), int(c2):  # B & BC
                return zone2 if b1 == b2 else None
            case Every(), Every(), int(c1), int(b2), Every(), int(c2):  # C & BC
                return zone2 if c1 == c2 else None
            # cellularizing
            case int(b1), int(r1), Every(), Every(), Every(), int(c2):  # BR & C
                return validated(b1, r1, c2)
            case int(b1), Every(), int(c1), Every(), int(r2), Every():  # BC & R
                return validated(b1, r2, c1)
            case int(b1), int(r1), Every(), int(b2), Every(), int(c2):  # BR & BC
                return validated(b1, r1, c2) if b1 == b2 else None
            case Every(), Every(), int(c1), int(b2), int(r2), Every():  # C & BR
                return validated(b2, r2, c1)
            case Every(), int(r1), Every(), int(b2), Every(), int(c2):  # BC & R
                return validated(b2, r1, c2)
            case int(b1), Every(), int(c1), int(b2), int(r2), Every():  # BC & BR
                return validated(b2, r2, c1) if b1 == b2 else None
            case _:
                return None

    def issubzone(self, other: Self):
        """This zone fully contained in another (or equal)
        = fully mutually visible
        """

        if self == other:
            return True

        if other.is_everything:
            return True

        if self.is_major:
            return self == other

        match self.blk, self.row, self.col, other.blk, other.row, other.col:
            case int(b1), _, _, int(b2), Every(), Every():
                return b1 == b2
            case _, int(r1), _, Every(), int(r2), Every():
                return r1 == r2
            case _, _, int(c1), Every(), Every(), int(c2):
                return c1 == c2

        return False

    @classmethod
    def around(cls, zone: Self) -> Iterable[Self]:
        """All major zones fully containing a subzone
        = visible by any cell in the subzone
        """
        assert zone.valid()

        match zone.blk, zone.row, zone.col:
            case int(b), int(r), Every():
                yield cls(b, ..., ...)
                yield cls(..., r, ...)
            case int(b), Every(), int(c):
                yield cls(b, ..., ...)
                yield cls(..., ..., c)
            case int(b), int(r), int(c):
                yield cls(b, ..., ...)
                yield cls(..., r, ...)
                yield cls(..., ..., c)

    @classmethod
    def across(cls, zone: Self) -> Iterable[Self]:
        """All major zones intersecting given
        = vizible by some cells in the zone
        """
        assert zone.valid()

        match zone.blk, zone.row, zone.col:
            case int(b), Every(), Every():
                yield from (cls(..., r, ...) for r in Topo.row4blk(b))
                yield from (cls(..., ..., c) for c in Topo.col4blk(b))
            case Every(), int(r), Every():
                yield from (cls(b, ..., ...) for b in Topo.blk4row(r))
                yield from (cls(..., ..., c) for c in Topo.cols)
            case Every(), Every(), int(c):
                yield from (cls(b, ..., ...) for b in Topo.blk4col(c))
                yield from (cls(..., r, ...) for r in Topo.rows)
            case int(b), int(r), Every():
                yield from (cls(..., ..., c) for c in Topo.col4blk(b))
            case int(b), Every(), int(c):
                yield from (cls(..., r, ...) for r in Topo.row4blk(b))

    @classmethod
    def aside(cls, zone: Self, subzone: Self) -> Iterable[Self]:
        return set(cls.around(subzone)) - {zone}

    @classmethod
    def partitions(cls, majzone: Self) -> Iterable[Self]:
        """All subzones of a major zone, partitioned by intersections with others"""
        assert majzone.valid() and majzone.is_major

        # quick stuff without nested iterations and redundant overlappency
        match majzone.blk, majzone.row, majzone.col:
            case int(b), Every(), Every():
                yield from (cls(b, r, ...) for r in Topo.row4blk(b))
                yield from (cls(b, ..., c) for c in Topo.col4blk(b))
            case Every(), int(r), Every():
                yield from (cls(b, r, ...) for b in Topo.blk4row(r))
            case Every(), Every(), int(c):
                yield from (cls(b, ..., c) for b in Topo.blk4col(c))

    def __iter__(self) -> Iterator[Loc]:
        """Iterate all cell locations in the zone"""

        assert self.valid()

        match self.blk, self.row, self.col:
            case Every(), Every(), Every():  # WHY ?
                yield from (Loc(r, c) for r in Topo.rows for c in Topo.cols)
            case _, int(r), int(c):
                yield Loc(r, c)
            case Every(), int(r), Every():
                yield from (Loc(r, c) for c in Topo.cols)
            case Every(), Every(), int(c):
                yield from (Loc(r, c) for r in Topo.rows)
            case int(b), Every(), Every():
                yield from (Loc(r, c) for r in Topo.row4blk(b) for c in Topo.col4blk(b))
            case int(b), int(r), Every():
                yield from (Loc(r, c) for c in Topo.col4blk(b))
            case int(b), Every(), int(c):
                yield from (Loc(r, c) for r in Topo.row4blk(b))

    def __contains__(self, loc: Loc) -> bool:
        """If the zone contains specific location"""

        match self.blk, self.row, self.col:
            case Every(), Every(), Every():
                return True
            case int(b), Every(), Every():
                return loc.row in Topo.row4blk(b) and loc.col in Topo.col4blk(b)
            case Every(), int(r), Every():
                return loc.row == r
            case Every(), Every(), int(c):
                return loc.col == c
            case int(b), int(r), Every():
                return loc.row == r and loc.col in Topo.col4blk(b)
            case int(b), Every(), int(c):
                return loc.col == c and loc.row in Topo.row4blk(b)
            case _, int(r), int(c):
                return loc.row == r and loc.col == c

    def __le__(self, other: Self):
        return self.issubzone(other)

    def __lt__(self, other: Self):
        return self.issubzone(other) and self != other

    def __ge__(self, other: Self):
        return other.issubzone(self)

    def __gt__(self, other: Self):
        return other.issubzone(self) and self != other

    def __and__(self, other: Self):
        return self.__class__.intersection(self, other)

    def __str__(self):
        rstr = "…" if self.row is EVERY else f"r{self.row}"
        cstr = "…" if self.col is EVERY else f"c{self.col}"
        if self.is_cellular:
            return f"[{rstr}{cstr}]"
        else:
            bstr = "…" if self.blk is EVERY else f"b{self.blk}"
            return f"[{bstr}{rstr}{cstr}]"


def visibility(z1: Zone, z2: Zone):
    """Check if the zones are fully mutually visible
    Return their common major zones
    """
    return set(Zone.around(z1)) & set(Zone.around(z2))


def allvisible(z1: Zone, z2: Zone) -> set[Zone]:
    """All zones/cells fully visible from both of the observers"""
    intervis = set(z1a & z2a for z1a, z2a in iterprod(Zone.around(z1), Zone.around(z2)))
    intervis -= {None}
    return intervis  # type: ignore


class Target(NamedTuple):
    """A draft involved in some relation"""

    zone: Zone
    dig: int

    @property
    def is_cellular(self) -> bool:
        return self.zone.is_cellular

    @classmethod
    def to(cls, where: Loc | Zone | Node, what: int) -> Self:
        if isinstance(where, Zone):
            return cls(where, what)
        elif isinstance(where, Loc):
            return cls(Zone.L(where.row, where.col), what)
        elif isinstance(where, Node):
            return cls(Zone.L(where.loc.row, where.loc.col), what)

    def __str__(self):
        return f"{self.dig}@{self.zone}"


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
        def strtail(lnk):
            return f" {lnk.CHAR} {lnk[1]}"

        joined = reduce(lambda a, lnk: a + strtail(lnk), self, str(self[0][0]))

        if self.is_loop:
            return f"(… {joined} …)"
        else:
            return f"({joined})"
