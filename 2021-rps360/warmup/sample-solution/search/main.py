"""
COMP30024 Artificial Intelligence, Semester 1, 2021
    
Project Part A: Searching
    
Sample solution

Note: This solution may contain errors. This solution has room for
improvement, particularly in the choice of data structures for the
state representation and in the choice of heuristic. This solution
passes all but the final test case used in marking student programs.
"""

import sys
import json
import math
import typing
import itertools
import collections

from search.util import print_board, print_slide, print_swing
from search.pq import PriorityQueue


def main():
    # 1. validate and load input
    try:
        with open(sys.argv[1]) as file:
            state = State.from_json(file)
        state.print("Initial state")
    except (IndexError, FileNotFoundError):
        print("usage: python3 -m search path/to/input.json", file=sys.stderr)
        sys.exit(1)

    # 2. compute solution
    soln = astar_search(
        start=state,
        goal_test=goal_test,
        heuristic=heuristic,
    )

    # 3. print solution
    if soln is not None:
        for t, actions in enumerate(soln, 1):
            for a, x, y in actions:
                if a == "SLIDE":
                    print_slide(t, *x, *y)
                else:
                    print_swing(t, *x, *y)
        print("# Done!")
    else:
        print("# No solution found")

# # #
# Problem formulation: State class
# An immutable class that encapsulates the information relevant to
# a particular Board state (the position and number of tokens) and
# the logic for generating successor states.
#

class State(typing.NamedTuple):
    # Note: By subclassing namedtuple, we get efficient, immutable instances
    # and we automatically get sensible definitions for __eq__ and __hash__.

    # This class stores the game state in the format of two lists:
    # One holding the positions and symbols of all upper tokens:
    upper_tokens: tuple
    # And one for all the lower tokens:
    lower_tokens: tuple
    # There is also a set of valid hexes (all of those not blocked by
    # block tokens):
    all_hexes:    frozenset
    

    # When subclassing namedtuple, we should control creation of instances
    # using a separate classmethod, rather than overriding __init__.
    @classmethod
    def new(cls, upper_tokens, lower_tokens, all_hexes):
        return cls(
                # TODO: Instead of sorted tuples, implement a frozen bag
                upper_tokens=tuple(sorted(upper_tokens)),
                lower_tokens=tuple(sorted(lower_tokens)),
                all_hexes=all_hexes,
            )

    # Following the alternative constructor idiom, we'll create a separate
    # classmethod to allow creating our first state from the data dictionary.
    @classmethod
    def from_json(cls, file):
        data = json.load(file)
        upper_tokens = (Token(Hex(r, q), s) for s, r, q in data["upper"])
        lower_tokens = (Token(Hex(r, q), s) for s, r, q in data["lower"])
        all_hexes = ALL_HEXES - {Hex(r, q) for _s, r, q in data["block"]}
        return cls.new(upper_tokens, lower_tokens, all_hexes)


    # The core functionality of the state is to compute its available
    # actions and their corresponding successor states.
    def actions_successors(self):
        for action in self.actions():
            yield action, self.successor(action)

    def actions(self):
        """
        Generate all available 'actions' (each 'action' is actually a
        collection of actions, one for each upper token).
        """
        xs = [x for x, _s in self.upper_tokens]
        occupied_hexes = set(xs)
        def _adjacent(x):
            return self.all_hexes & {x + y for y in HEX_STEPS}
        def _token_actions(x):
            adjacent_x = _adjacent(x)
            for y in adjacent_x:
                yield "SLIDE", x, y
                if y in occupied_hexes:
                    opposite_y = _adjacent(y) - adjacent_x - {x}
                    for z in opposite_y:
                        yield "SWING", x, z
        return itertools.product(*map(_token_actions, xs))
    
    def successor(self, action):
        # move all upper tokens
        new_upper_tokens = []
        for _a, x, y in action:
            # lookup the symbol (any token on this hex will do, since all
            # tokens here will have the same symbol since the last battle)
            s = [t.symbol for t in self.upper_tokens if t.hex == x][0]
            new_upper_tokens.append(Token(y, s))

        # where tokens clash, do battle
        # TODO: only necessary to check this at destinations of actions
        # (but then will have to find another way to fill the lists)
        safe_upper_tokens = []
        safe_lower_tokens = []
        for x in self.all_hexes:
            ups_at_x = [t for t in new_upper_tokens  if t.hex == x]
            los_at_x = [t for t in self.lower_tokens if t.hex == x]
            symbols = {t.symbol for t in ups_at_x + los_at_x}
            if len(symbols) > 1:
                for s in symbols:
                    p = BEATS_WHAT[s]
                    ups_at_x = [t for t in ups_at_x if t.symbol != p]
                    los_at_x = [t for t in los_at_x if t.symbol != p]
            safe_upper_tokens.extend(ups_at_x)
            safe_lower_tokens.extend(los_at_x)
        return self.new(safe_upper_tokens, safe_lower_tokens, self.all_hexes)

    # For easier debugging, a helper method to print the current state.
    def print(self, message="", **kwargs):
        board = collections.defaultdict(str)
        for t in self.upper_tokens:
            board[t.hex] += t.symbol.upper()
        for t in self.lower_tokens:
            board[t.hex] += t.symbol.lower()
        for x, s in board.items():
            board[x] = f"({s})"
        for x in ALL_HEXES - self.all_hexes:
            board[x] = "BLOCK"
        print_board(board, message, **kwargs)

# (Some classes and constants supporting the implementation above)

class Hex(typing.NamedTuple):
    """
    Hexagonal axial coordinates with basic operations and hexagonal
    manhatten distance.
    Thanks to https://www.redblobgames.com/grids/hexagons/ for some
    of the ideas implemented here.
    """
    r: int
    q: int

    @staticmethod
    def dist(x, y):
        """
        Hexagonal manhattan distance between two hex coordinates.
        """
        z_r = x.r - y.r
        z_q = x.q - y.q
        return (abs(z_r) + abs(z_q) + abs(z_r + z_q)) // 2

    def __add__(self, other):
        # this special method is called when two Hex objects are added with +
        return Hex(self.r + other[0], self.q + other[1])

HEX_RANGE = range(-4, +4+1)
ALL_HEXES = frozenset(
        Hex(r, q) for r in HEX_RANGE for q in HEX_RANGE if -r-q in HEX_RANGE
    )
HEX_STEPS = [Hex(r, q) for r, q in [(1,-1),(1,0),(0,1),(-1,1),(-1,0),(0,-1)]]

BEATS_WHAT = {'r': 's', 'p': 'r', 's': 'p'}
WHAT_BEATS = {'r': 'p', 'p': 's', 's': 'r'}

class Token(typing.NamedTuple):
    hex:    Hex
    symbol: str



# # #
# Problem formulation: Goal test
# 

def goal_test(state):
    return len(state.lower_tokens) == 0


# # #
# Informing the search algorithm: Heuristic
# A simple calculation determines the straight-line hexagonal distance 
# of each lower token from the nearest upper token which will defeat it.
# The sum of these distances is a simple (but not necessarily admissible)
# heuristic drawing upper tokens towards lower tokens.
# The heuristic is not admissible in at least two ways:
# 1. Swing actions can reduce the effective distance between tokens, and
# 2. Moving upper tokens can reduce two minimum distances at once if the
#    lower tokens are in the same region of the board.
# The heuristic could be improved in any or all of the following ways:
# 1. Pre-computing real distances using an all-pairs-shortest-paths algorithm
#    could make the distance calculations aware of the block tokens.
# 2. Using a more sophisticated method of aggrgating the distances when there
#    are multiple tokens of the one symbol (upper or lower) such as solving
#    a small linear sum assignment problem and/or travelling salesman problem
#    could make the heuristic more accurate in more complex cases.
def heuristic(state):
    distance = 0
    for x, s in state.lower_tokens:
        r = WHAT_BEATS[s]
        ys = [y for y, r_ in state.upper_tokens if r_ == r]
        if ys:
            distance += min(Hex.dist(x, y) for y in ys)
        else:
            distance += math.inf
    return distance

# # #
# Search algorithm: AStar
# 

def astar_search(start, goal_test, heuristic, verbose=False):
    """
    Run the A star search algorithm from a given start state with a given
    goal test and heuristic.
    `start` should be a state object with `actions_successors` method
    which yields actions and successor states.
    """
    # keep track of distances and predecessor states/actions in these maps
    dist = {start: 0}
    back = {start: None}
    # start with the start state and loop through states in priority order
    queue = PriorityQueue([(start, heuristic(start))])
    for state in queue:
        if verbose: state.print(f"{dist[state]} {heuristic(state)}")
        # if this is the goal, we are done: backtrack and return path
        if goal_test(state):
            actions = []
            while back[state] is not None:
                state, action = back[state]
                actions.append(action)
            return actions[::-1]
        # otherwise, expand this node to continue the search
        dist_new = dist[state] + 1
        for (action, successor) in state.actions_successors():
            if successor not in dist or dist[successor] > dist_new:
                dist[successor] = dist_new
                back[successor] = (state, action)
                queue[successor] = dist_new + heuristic(successor)
    # priority queue empty, there must be no solution
    return None

