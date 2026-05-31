from functools import reduce
from itertools import chain as iterchain
from typing import Iterable, NamedTuple, Self

from board import DIGITS, POS9, Board, Loc, Node

iterflat = iterchain.from_iterable


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

    @classmethod
    def adjacent(cls, loc1, loc2) -> bool:
        """intersectable = some of them has None in c"""
        # (..., ..., ...) = invalid
        return not (loc1.blk and loc2.blk) and not (loc1.row and loc2.row) and not (loc1.col and loc2.col)

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
        # assert adjacent
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
        if not self.blk and not self.row and not self.col:
            return "@..."

        bstr = f"b{self.blk}" if self.blk else ""
        rstr = f"b{self.row}" if self.row else ""
        cstr = f"b{self.col}" if self.col else ""

        return f"@{bstr}{rstr}{cstr}"


class Target(NamedTuple):
    """Target digit-segment inside a cell"""

    loc: Loc
    dig: int

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
                return tuple(filter(lambda n: t1.dig in n.cell, zone.neighborhood(board)))

            # some shared zone has only 2 cell with the digit
            return any(len(occupied(zone)) == 2 for zone in Locality.shared(l1, l2))
        else:
            # different digits in a single cell
            return l1 == l2 and len(board.get(l1).cell) == 2

    def __str__(self):
        return f"{self.dig}{self.loc}"

    @classmethod
    def iter_node(cls, node: Node) -> Iterable[Self]:
        """target all digits of a node"""
        return (cls(node.loc, d) for d in node.cell)


# TODO: replace Target with proper API
# class MultiTarget(NamedTuple):
#     loc: Locality
#     digs: frozenset[int]
#     def __str__(self):
#         joined = "".join(map(str, self.digs))
#         return f"{joined}{self.loc}"


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
    """Hard link, XOR relation"""

    CHAR = "⊻"


class SLink(Link):
    """Soft link, NAND relation"""

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

        if self.is_loop:
            return "..." + reduce(lambda a, lnk: a + strtail(lnk), self[:-1], str(self[0][0])) + "..."
        else:
            return reduce(lambda a, lnk: a + strtail(lnk), self, str(self[0][0]))


def validate(board: Board):
    if sum(c.is_draft for c in board.cells) > 0:
        return "INCOMPLETE"

    def fulfiled(zone: Locality):
        return set(board.get(loc).cell.final for loc in zone.iter()) == DIGITS

    if all(map(fulfiled, Locality.all())):
        return "SOLVED"
    else:
        return "BROKEN"


def zoneflat(zones: Iterable[Locality]) -> Iterable[Loc]:
    return iterflat(z.iter() for z in zones)


def visible_locs(l1: Loc, l2: Loc) -> Iterable[Loc]:
    """All locs visible from both the locs"""

    # they share some localities
    visible = set(zoneflat(Locality.shared(l1, l2)))
    if visible:
        return visible

    # intersection of their arounds
    visible = set(zoneflat(Locality.around(l1))) & set(zoneflat(Locality.around(l2)))
    return visible
