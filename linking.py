from collections.abc import Iterable
from typing import Self
from functools import reduce
from itertools import chain as iterchain, combinations as itercomb


from targeting import Node

iterflat = iterchain.from_iterable


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
        return self.is_casual and n1.loc == n2.loc and n1.dig != n2.dig

    @property
    def is_biloc(self):
        n1, n2 = self
        return self.is_casual and n1.loc != n2.loc and n1.dig == n2.dig

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


ALTERATING = [HLink, SLink]


def are_alternating(links: Iterable[Link], start=0):
    return all(isinstance(lnk, ALTERATING[i % 2]) for i, lnk in enumerate(links, start))


class Chain(tuple[Link, ...]):
    """Chain of alterating links"""

    # totally ordered, unordered for comparision

    @property
    def edges(self) -> tuple[Node, Node]:
        return (self[0][0], self[-1][-1])

    @classmethod
    def extend(cls, chain: Self, *links: Link) -> Self:
        """Add some links to the end of the chain"""
        assert are_alternating(links, 1)
        assert chain[-1][-1] == links[0][0]
        return cls((*chain, *links))

    @classmethod
    def exthead(cls, chain: Self, *links: Link) -> Self:
        """Add some links to the head of the chain"""
        assert are_alternating(links, 0)
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

        if self[0][0] == self[-1][-1]:
            return f"(… {joined} …)"
        else:
            return f"({joined})"
