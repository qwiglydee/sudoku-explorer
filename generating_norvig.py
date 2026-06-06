"""Generating puzzles
Algo by Peter Norwig
https://norvig.com/sudoku.html

No guarentee it's solvable or uniq
"""

import random

from board import DIGITS, Loc, Board
import coords

Values = list[set[int]]


def get(values: Values, loc: Loc):
    return values[Board._idx(loc)]


def put(values: Values, loc: Loc, vals: set[int]):
    values[Board._idx(loc)] = vals


def choose(values: Values, loc: Loc):
    return random.choice(tuple(get(values, loc)))


def pick(values: set[int]):
    [v] = values
    return v


units = {
    Loc(row, col): [
        set(Loc(r, c) for r in coords.row4box(box) for c in coords.col4box(box)),
        set(Loc(row, c) for c in coords.POS),
        set(Loc(r, col) for r in coords.POS),
    ]
    for box, row, col in coords.all()
}

peers = {loc: (locs[0] | locs[1] | locs[2]) - {loc} for loc, locs in units.items()}


def generate_puzzle(n=17):
    while True:
        values = generate(n)
        if values:
            return Board([v if len(v) == 1 else set() for v in values])


def generate(N=17) -> Values | None:
    """Make a random puzzle with N or more assignments. Restart on contradictions.
    Note the resulting puzzle is not guaranteed to be solvable, but empirically
    about 99.8% of them are solvable. Some have multiple solutions."""
    values = [set(DIGITS) for _ in coords.all()]

    locs = [Loc(r, c) for b, r, c in coords.all()]
    random.shuffle(locs)

    for loc in locs:
        if not assign(values, loc, choose(values, loc)):
            break
        finals = [pick(v) for v in values if len(v) == 1]
        if len(finals) >= N and len(set(finals)) >= 8:
            return values

    # give up and return None


def assign(values: Values, loc: Loc, val: int):
    """Eliminate all the other values (except d) from values[s] and propagate.
    Return values, except return None if a contradiction is detected."""
    others = get(values, loc) - {val}
    # print(f"{loc} := {val} ...")
    return all(eliminate(values, loc, v2) for v2 in others)


def eliminate(values: Values, loc: Loc, val: int):
    """Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return None if a contradiction is detected."""
    # print(f"{loc} -= {val} ...")

    thecell = get(values, loc)
    if val not in thecell:
        return True  ## Already eliminated

    thecell -= {val}
    put(values, loc, thecell)

    if len(thecell) == 0:
        return False

    ## (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
    if len(thecell) == 1:
        [v2] = thecell
        if not all(eliminate(values, l2, v2) for l2 in peers[loc]):
            return False

    for u in units[loc]:
        occupied = [s for s in u if val in get(values, s)]
        if len(occupied) == 0:
            return False  ## Contradiction: no place for this value
        elif len(occupied) == 1:
            # d can only be in one place in unit; assign it there
            if not assign(values, occupied[0], val):
                return False

    return True
