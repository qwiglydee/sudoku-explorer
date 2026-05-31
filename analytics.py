from functools import reduce
from itertools import chain as iterchain
from typing import Iterable, NamedTuple, Self

from board import DIGITS, POS9, Board, Loc, Node

iterflat = iterchain.from_iterable


def Node_has(dig: int):
    return lambda n: dig in n.cell


class Locality(NamedTuple):
    """Locality of a block, row, col, cell or their intersections"""

    # all None means whole board
    blk: int | None
    row: int | None
    col: int | None

    def iter(self) -> Iterable[Loc]:
        """Iterate all locations in the locality"""
        match tuple(self):
            case (int(b), None, None):
                r1, c1 = Loc.of_blk(b)
                yield from (Loc(r, c) for r in (r1, r1 + 1, r1 + 2) for c in (c1, c1 + 1, c1 + 2))
            case (None, int(r), None):
                yield from (Loc(r, i) for i in POS9)
            case (None, None, int(c)):
                yield from (Loc(i, c) for i in POS9)
            case (_, int(r), int(c)):
                yield Loc(r, c)
            case (int(b), int(r), None):
                r1, c1 = Loc.of_blk(b)
                assert r1 <= r <= r1 + 2, "invalid locality intersection"
                yield from (Loc(r, c) for c in (c1, c1 + 1, c1 + 2))
            case (int(b), None, int(c)):
                r1, c1 = Loc.of_blk(b)
                assert c1 <= c <= c1 + 2, "invalid locality intersection"
                yield from (Loc(r, c) for r in (r1, r1 + 1, r1 + 2))
            case (None, None, None):
                yield from (Loc(r, c) for r in POS9 for c in POS9)
            case _:
                raise TypeError()

    def locs(self) -> set[Loc]:
        return set(self.iter())

    def __contains__(self, loc: Loc) -> bool:
        """Chack if location is in the locality"""
        match tuple(self):
            case (int(b), None, None):
                return loc.blk == b
            case (None, int(r), None):
                return loc.row == r
            case (None, None, int(c)):
                return loc.col == c
            case (_, int(r), int(c)):
                return loc.row == r and loc.col == c
            case (int(b), int(r), None):
                return loc.blk == b and loc.row == r
            case (int(b), None, int(c)):
                return loc.blk == b and loc.col == c
            case (None, None, None):
                return True
            case _:
                raise TypeError()

    @classmethod
    def around(cls, loc: Loc) -> Iterable[Self]:
        """Get all major zones containing the loc"""
        return (
            cls(loc.blk, None, None),
            cls(None, loc.row, None),
            cls(None, None, loc.col),
        )

    @classmethod
    def conjunc(cls, *zones: Self) -> Iterable[Loc]:
        return reduce(lambda a, b: a & b, (z.locs() for z in zones))

    @classmethod
    def disjunc(cls, *zones: Self) -> Iterable[Loc]:
        return reduce(lambda a, b: a | b, (z.locs() for z in zones))

    @classmethod
    def intersect(cls, loc1: Self, loc2: Self) -> Self:
        def axis_fit(a1, a2):
            return a1 == a2 or a1 is None or a2 is None

        assert axis_fit(loc1.blk, loc2.blk)
        assert axis_fit(loc1.row, loc2.row)
        assert axis_fit(loc1.col, loc2.col)
        return cls(loc1.blk or loc2.blk, loc1.row or loc2.row, loc1.col or loc2.col)

    def __and__(self, other):
        return self.__class__.intersect(self, other)

    @classmethod
    def shared(cls, l1: Loc, l2: Loc) -> Iterable[Self]:
        """Get all localities containing both of the locs"""
        if l1 == l2:
            yield cls(l1.blk, l1.row, l2.col)
            return
        if l1.blk == l2.blk:
            yield cls(l1.blk, None, None)
        if l1.row == l2.row:
            yield cls(None, l1.row, None)
        if l1.col == l2.col:
            yield cls(None, None, l1.col)

    @classmethod
    def all(cls) -> Iterable[Self]:
        for i in POS9:
            yield cls(i, None, None)
        for i in POS9:
            yield cls(None, i, None)
        for i in POS9:
            yield cls(None, None, i)

    def neighborhood(self, board: Board) -> Iterable[Node]:
        """Get corresponding nodes from board"""
        return board.slice(self.iter())

    def __str__(self):
        bstr = f"b{self.blk}" if self.blk else "…"
        rstr = f"r{self.row}" if self.row else "…"
        cstr = f"c{self.col}" if self.col else "…"
        return f"{{{bstr}{rstr}{cstr}}}"


def zoneflat(zones: Iterable[Locality]) -> Iterable[Loc]:
    return iterflat(z.iter() for z in zones)


def are_visible(loc1: Loc | Locality, loc2: Loc | Locality) -> bool:
    """If they mutually visible"""
    return loc1.blk == loc2.blk or loc1.row == loc2.row or loc1.col == loc2.col


def all_visible(l1: Loc, l2: Loc) -> Iterable[Loc]:
    """All locs visible from both the locs"""

    shared = set(Locality.shared(l1, l2))
    if shared:
        # all from shared localities
        return set(zoneflat(shared))
    else:
        # intersection of their arounds
        return set(zoneflat(Locality.around(l1))) & set(zoneflat(Locality.around(l2)))


class Target(NamedTuple):
    """Target digit-segment inside a cell"""

    loc: Loc
    dig: int

    is_singular = True

    def __str__(self):
        return f"{self.dig}@{self.loc}"


# TODO: replace Target with proper API
class MultiTarget(NamedTuple):
    loc: Locality
    digs: frozenset[int]

    @property
    def is_singular(self) -> bool:
        return len(self.digs) == 1

    @property
    def dig(self) -> int:
        assert self.is_singular
        (d,) = self.digs
        return d

    def __str__(self):
        joined = "".join(map(str, self.digs))
        return f"{joined}@{self.loc}"


def are_nandable(t1: Target | MultiTarget, t2: Target | MultiTarget):
    """If they can form a soft link"""
    if t1.is_singular and t2.is_singular and t1.dig == t2.dig:
        return are_visible(t1.loc, t2.loc)
    else:
        return t1.loc == t2.loc


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

    ALTERATING = [SLink, HLink]  # for the extending

    @classmethod
    def init(cls, link: HLink):
        assert isinstance(link, HLink)
        return cls((link,))

    @classmethod
    def extend(cls, chain: Self, *links: Link) -> Self:
        """Add some links to end of the chain"""
        assert all(isinstance(lnk, cls.ALTERATING[i % 2]) for i, lnk in enumerate(links))
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
        def strtail(lnk):
            return f" {lnk.CHAR} {lnk[1]}"

        joined = reduce(lambda a, lnk: a + strtail(lnk), self, str(self[0][0]))

        if self.is_loop:
            return f"(…{joined}…)"
        else:
            return f"({joined})"


def validate(board: Board):
    if not all(Node.is_final(n) for n in board):
        return "INCOMPLETE"

    def fulfiled(zone: Locality):
        neighborhood = tuple(zone.neighborhood(board))
        return all(Node.is_final(n) for n in neighborhood) and set(n.cell.final for n in neighborhood) == DIGITS

    if all(map(fulfiled, Locality.all())):
        return "SOLVED"
    else:
        return "BROKEN"
