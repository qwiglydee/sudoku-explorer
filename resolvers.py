from typing import Iterator
from itertools import chain as iterchain, combinations as itercomb

from board import Board, Digits
from solving import Pattern, Resolving
from targeting import Node
from topology import Zone, allpeers
from utils import count_digits, draftboard, draftborhood, filt_finals, filt_havesome, grab_digits

iterflat = iterchain.from_iterable


def random_choice(board: Board) -> Resolving:
    """Just a random choice as a last resort
    Use only for non-uniq puzzles
    """
    drafts = list(draftboard(board))
    assert len(drafts)

    drafts.sort(key=lambda c: len(c))
    leastcell = drafts[0]
    counts = count_digits(drafts)

    digits = list(leastcell.digits)
    digits.sort(key=lambda d: counts[d])
    leastdig = digits[0]

    chosen = Node.at(leastcell, leastdig)
    loosen = Node.at(leastcell, leastcell.digits - chosen.digits)

    yield Pattern(
        anchors={chosen},
        spoilers={loosen},
    )


def naked_singles(board: Board) -> Resolving:
    """Basic rule of cleaning up conflicting drafts"""
    for fincell in filter(filt_finals, iter(board)):
        findig = Digits({fincell.final})
        anchor = Node.at(fincell, findig)
        spoilers = set(filter(filt_havesome(findig), board.slice(allpeers(anchor.zone))))
        if spoilers:
            yield Pattern(
                anchors={anchor},
                spoilers={Node.at(c.loc, anchor.digits) for c in spoilers},
            )


def hidden_singles(board: Board) -> Resolving:
    """Basic rule of cleaning conflicting drafts within same cell"""
    for unit in Zone.Units():
        drafts = set(draftborhood(board, unit))
        counts = count_digits(drafts)
        for dig, cnt in counts.items():
            if cnt == 1:
                [cell] = filter(lambda c: dig in c, drafts)
                anchor = Node.at(cell, dig)
                spoilers = Node.at(cell, cell.digits - {dig})
                yield Pattern(
                    space={Node.at(unit, dig)},
                    anchors={anchor},
                    spoilers={spoilers},
                )


def naked_multiples(board: Board) -> Resolving:
    for unit in Zone.Units():
        drafts = tuple(draftborhood(board, unit))
        digits = grab_digits(drafts)
        for m in range(2, 5):
            for combo in itercomb(digits, m):
                combits = Digits(combo)
                habitat = set(filter(lambda c: c.digits & combits, drafts))
                naked = set(filter(lambda c: c.digits <= combits, habitat))
                # print(unit, combits, set(map(str, naked)), "/", set(map(str, habitat)))
                if len(naked) == len(combo):
                    spoilers = set(filter(filt_havesome(combits), drafts)) - naked
                    if spoilers:
                        yield Pattern(
                            space={Node.at(unit, combits)},
                            anchors={Node.at(c, combits) for c in naked},
                            spoilers={Node.at(c, combits) for c in spoilers},
                        )


def hidden_multiples(board: Board) -> Resolving:
    for unit in Zone.Units():
        drafts = tuple(draftborhood(board, unit))
        digits = grab_digits(drafts)
        for m in range(2, 5):
            for combo in itercomb(digits, m):
                combits = Digits(combo)
                habitat = set(filter(lambda c: c.digits & combits, drafts))
                if len(habitat) == len(combo):
                    spoilers = set(filter(lambda c: c.digits > combits, habitat))
                    if spoilers:
                        yield Pattern(
                            space={Node.at(unit, combits)},
                            anchors={Node.at(c, c.digits & combits) for c in habitat},
                            spoilers={Node.at(c, c.digits - combits) for c in spoilers},
                        )


def iter_sect() -> Iterator[tuple[Zone, Zone, Zone]]:
    for box in Zone.Allbox():
        for side in Zone.across(box):
            yield box, side, box & side  # type: ignore impossible null


def locked_triplets(board: Board) -> Resolving:
    """Looking for box/row/col intersections with isolated triplets/duplets"""
    for box, side, sect in iter_sect():
        boxcounts = count_digits(draftborhood(board, box))
        sidecounts = count_digits(draftborhood(board, side))
        sectcounts = count_digits(draftborhood(board, sect))
        # print(box, side, sect, sectcounts)
        for dig, cnt in sectcounts.items():
            if cnt < 2:
                continue
            elif cnt == boxcounts[dig] and cnt < sidecounts[dig]:
                sideborhood = set(iter(side)) - set(iter(box))
                yield Pattern(
                    anchors={Node.at(sect, dig)},
                    space={Node.at(box, dig)},
                    spoilers={Node.at(z, dig) for z in sideborhood},
                )
            elif cnt == sidecounts[dig] and cnt < boxcounts[dig]:
                insideborhood = set(iter(box)) - set(iter(side))
                yield Pattern(
                    anchors={Node.at(sect, dig)},
                    space={Node.at(side, dig)},
                    spoilers={Node.at(z, dig) for z in insideborhood},
                )
