"""Structures for coordslogical analysis"""

from functools import reduce
from itertools import chain as iterchain, product as iterprod
from types import EllipsisType
from typing import Iterable, Iterator, NamedTuple, Self

from board import Loc, Cell
import coords

iterflat = iterchain.from_iterable

Every = EllipsisType
EVERY = Ellipsis


def coords_valid(box: int | Every, row: int | Every, col: int | Every) -> bool:
    # hard constraints
    assert box is EVERY or 1 <= box <= 9  # type: ignore
    assert row is EVERY or 1 <= row <= 9  # type: ignore
    assert col is EVERY or 1 <= col <= 9  # type: ignore

    # soft constraints
    try:
        if isinstance(box, int):
            if isinstance(row, int):
                assert row in coords.row4box(box)
            if isinstance(col, int):
                assert col in coords.col4box(box)
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

    box: int | EllipsisType
    row: int | EllipsisType
    col: int | EllipsisType

    @classmethod
    def B(cls, box: int) -> Self:
        assert 1 <= box <= 9
        return cls(box, ..., ...)

    @classmethod
    def R(cls, row: int) -> Self:
        assert 1 <= row <= 9
        return cls(..., row, ...)

    @classmethod
    def C(cls, col: int) -> Self:
        assert 1 <= col <= 9
        return cls(..., ..., col)

    @classmethod
    def L(cls, loc: Loc) -> Self:
        assert 1 <= loc.r <= 9 and 1 <= loc.c <= 9
        return cls(coords.box4loc(loc), loc.r, loc.c)

    @classmethod
    def Allbox(cls) -> Iterable[Self]:
        return (cls(b, ..., ...) for b in coords.POS)

    @classmethod
    def Allrow(cls) -> Iterable[Self]:
        return (cls(..., r, ...) for r in coords.POS)

    @classmethod
    def Allcol(cls) -> Iterable[Self]:
        return (cls(..., ..., c) for c in coords.POS)

    @classmethod
    def All(cls) -> Iterable[Self]:
        yield from cls.Allbox()
        yield from cls.Allrow()
        yield from cls.Allcol()

    # invalid box may occur because of all the mess around

    def valid(self) -> bool:
        return coords_valid(self.box, self.row, self.col)

    @property
    def is_everything(self):
        # it may appear in some calculations
        return self.box is EVERY and self.row is EVERY and self.col is EVERY

    @property
    def is_cellular(self):
        return self.row is not EVERY and self.col is not EVERY

    @property
    def is_major(self):
        return sum(a is not EVERY for a in (self.box, self.row, self.col)) == 1

    @classmethod
    def of(cls, what: Self | Loc | Cell):
        if isinstance(what, cls):
            return what
        if isinstance(what, Loc):
            return cls(coords.box4loc(what), what.r, what.c)
        if isinstance(what, Cell):
            loc = what.loc
            return cls(coords.box4loc(loc), loc.r, loc.c)
        raise TypeError()

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
            return (zone.box == EVERY or zone.box == cell.box) and (zone.row == EVERY or zone.row == cell.row) and (zone.col is EVERY or zone.col == cell.col)

        if zone1.is_cellular:
            return zone1 if eqe(zone1, zone2) else None
        if zone2.is_cellular:
            return zone2 if eqe(zone2, zone1) else None

        def validated(b, r, c):
            return cls(b, r, c) if coords_valid(b, r, c) else None

        # TODO: optimize the shit
        match zone1.box, zone1.row, zone1.col, zone2.box, zone2.row, zone2.col:
            case Every(), int(r1), Every(), Every(), Every(), int(c2):  # R & C
                return cls(coords.box4loc(Loc(r1, c2)), r1, c2)
            case Every(), Every(), int(c1), Every(), int(r2), Every():  # C & R
                return cls(coords.box4loc(Loc(r2, c1)), r2, c1)
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

        match self.box, self.row, self.col, other.box, other.row, other.col:
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

        match zone.box, zone.row, zone.col:
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

        match zone.box, zone.row, zone.col:
            case int(b), Every(), Every():
                yield from (cls(..., r, ...) for r in coords.row4box(b))
                yield from (cls(..., ..., c) for c in coords.col4box(b))
            case Every(), int(r), Every():
                yield from (cls(b, ..., ...) for b in coords.box4row(r))
            case Every(), Every(), int(c):
                yield from (cls(b, ..., ...) for b in coords.box4col(c))
            case int(b), int(r), Every():
                yield from (cls(..., ..., c) for c in coords.col4box(b))
            case int(b), Every(), int(c):
                yield from (cls(..., r, ...) for r in coords.row4box(b))

    @classmethod
    def aside(cls, zone: Self, subzone: Self) -> Iterable[Self]:
        return set(cls.around(subzone)) - {zone}

    @classmethod
    def partitions(cls, majzone: Self) -> Iterable[Self]:
        """All subzones of a major zone, partitioned by intersections with others"""
        assert majzone.valid() and majzone.is_major

        # quick stuff without nested iterations and redundant overlappency
        match majzone.box, majzone.row, majzone.col:
            case int(b), Every(), Every():
                yield from (cls(b, r, ...) for r in coords.row4box(b))
                yield from (cls(b, ..., c) for c in coords.col4box(b))
            case Every(), int(r), Every():
                yield from (cls(b, r, ...) for b in coords.box4row(r))
            case Every(), Every(), int(c):
                yield from (cls(b, ..., c) for b in coords.box4col(c))

    def __iter__(self) -> Iterator[Loc]:
        """Iterate all cell locations in the zone"""

        assert self.valid()

        match self.box, self.row, self.col:
            case Every(), Every(), Every():  # WHY ?
                yield from (Loc(r, c) for r in coords.POS for c in coords.POS)
            case _, int(r), int(c):
                yield Loc(r, c)
            case Every(), int(r), Every():
                yield from (Loc(r, c) for c in coords.POS)
            case Every(), Every(), int(c):
                yield from (Loc(r, c) for r in coords.POS)
            case int(b), Every(), Every():
                yield from (Loc(r, c) for r in coords.row4box(b) for c in coords.col4box(b))
            case int(b), int(r), Every():
                yield from (Loc(r, c) for c in coords.col4box(b))
            case int(b), Every(), int(c):
                yield from (Loc(r, c) for r in coords.row4box(b))

    def __contains__(self, loc: Loc) -> bool:
        """If the zone contains specific location"""

        match self.box, self.row, self.col:
            case Every(), Every(), Every():
                return True
            case int(b), Every(), Every():
                return loc.r in coords.row4box(b) and loc.c in coords.col4box(b)
            case Every(), int(r), Every():
                return loc.r == r
            case Every(), Every(), int(c):
                return loc.c == c
            case int(b), int(r), Every():
                return loc.r == r and loc.c in coords.col4box(b)
            case int(b), Every(), int(c):
                return loc.c == c and loc.r in coords.row4box(b)
            case _, int(r), int(c):
                return loc.r == r and loc.c == c

    def __len__(self):
        if self.is_cellular:
            return 1
        elif self.is_major:
            return 9
        else:
            return 3

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
            return f"{rstr}{cstr}"
        else:
            bstr = "…" if self.box is EVERY else f"b{self.box}"
            return f"{bstr}{rstr}{cstr}"


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


class Node(NamedTuple):
    """A single-digit draft placed in some locality"""

    zone: Zone
    dig: int

    @property
    def is_cellular(self) -> bool:
        return self.zone.is_cellular

    @classmethod
    def at(cls, where: Loc | Zone | Cell, what: int) -> Self:
        if isinstance(where, Zone):
            return cls(where, what)
        elif isinstance(where, Loc):
            return cls(Zone.L(where), what)
        elif isinstance(where, Cell):
            return cls(Zone.L(where.loc), what)
        raise TypeError()

    def __str__(self):
        return f"{self.dig}{self.zone}"


class Group(NamedTuple):
    zones: tuple[Zone, Zone]
    dig: int
    cells: frozenset[Cell]

    def cross(self):
        return self.zones[0] & self.zones[1]

    def node(self):
        if len(self.cells) == 1:
            [lonesome] = self.cells
            return Node.at(lonesome, self.dig)
        elif len(self.cells) > 1:
            subzone = self.cross()
            assert subzone is not None
            return Node.at(subzone, self.dig)
        else:
            raise ValueError()


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
