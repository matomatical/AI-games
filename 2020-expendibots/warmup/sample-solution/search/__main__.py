import sys
import json
from math import inf

from search.util import print_boom, print_move, print_board
from search.pq import PriorityQueue


def main():
    """
    Read initial board configuration from file, perform search, print
    solution.
    """
    # load and analyse input
    with open(sys.argv[1]) as file:
        data = json.load(file)
    stacks = {(x,y): n for n,x,y in data["white"]}
    targets = {(x,y) for _,x,y in data["black"]}
    target_groups = find_explosion_groups(targets)

    # search for an action sequence
    start_state = State(stacks, target_groups)
    start_state.print("Starting state")
    solution = astar_search(start_state)
    
    # print solution
    if solution is None:
        print("# No solution found...!")
    else:
        print("# Solution found!")
        states, actions = solution
        for state, action in zip(states, actions):
            state.print()
            action.print()
        states[-1].print("Goal!")


def find_explosion_groups(targets):
    """
    Partition a set of targets into groups that will 'boom' together.
    'targets' is a set of coordinate pairs. Return a set of frozensets
    representing the partition.
    """
    # 'up' is a union-find tree-based data structure
    up = {t: t for t in targets}
    # find performs a root lookup with path compression in 'up'
    def find(t):
        if up[t] == t:
            return t
        top = find(up[t])
        up[t] = top
        return top
    # run disjoint set formation algorithm to identify groups
    for t in targets:
        ttop = find(t)
        for u in around_square(t):
            if u in targets:
                utop = find(u)
                if ttop != utop:
                    up[utop] = ttop
    # convert disjoint set trees into Python sets
    groups = {}
    for t in targets:
        top = find(t)
        if top in groups:
            groups[top].add(t)
        else:
            groups[top] = {t}
    # return the partition
    return {frozenset(group) for group in groups.values()}


def astar_search(start):
    """
    A* search algorithm. Conduct a full A* search to a goal state
    for some initial state 'start'.
    Return a (list of states, list of actions) representing solution,
    or None if no solution exists.

    Notes: 
    - Assume that path cost is just the number of actions.
    - For optimality, require that the state class's heuristic method
      is consistent.
    """
    # store the current best-known partial path cost to each state encountered:
    dist = {start: 0}
    # 'back' stores the previous state in this path for each state encountered,
    # along with the relevant action, for later path reconstruction
    back = {start: None}
    # for convenience, define a shorthand for f(s) = g(s) + h(s):
    def f(s):
        return dist[s] + s.heuristic()
    # begin with a priority queue containing only the initial state
    queue = PriorityQueue()
    queue.update(start, f(start))

    # (this priority queue implementation allows concurrent iteration and
    # modification---this for loop will run until the queue is exhausted)
    for state in queue:
        # if we reach a goal state, we can terminate the search!
        if state.is_goal():
            return backtrack(state, back)
        # otherwise, expand this node, updating successors in the queue if
        # we find a better path
        dist_new = dist[state] + 1
        for (action, successor_state) in state.actions_successors():
            if successor_state not in dist or dist[successor_state] > dist_new:
                # a new or cheaper path has been found: update queue and maps
                dist[successor_state] = dist_new
                back[successor_state] = (state, action)
                queue.update(successor_state, f(successor_state))
    # is the priority queue runs out, there must be no path to a goal state
    return None

def backtrack(state, backpointers):
    """
    Traverse back through a dictionary of previous states/actions
    'backpointers' from some final state 'state' to  reconstruct a
    path. Return a (list of states, list of actions) representing 
    the reconstructed path
    """
    if backpointers[state] is None:
        return [state], []
    prev, action = backpointers[state]
    states, actions = backtrack(prev, backpointers)
    states.append(state)
    actions.append(action)
    return states, actions



class State:
    """
    Wraps a game state, that is, a collection of the player's stacks
    along with a set of groups of enemy tokens to eliminate.
    """
    def __init__(self, stacks, groups, group_metrics=None, all_targets=None):
        self.stacks = stacks
        self.groups = groups
        if group_metrics is None:
            self.group_metrics = {id(g): distance_grid(g) for g in groups}
        else:
            self.group_metrics = group_metrics
        if all_targets is None:
            self.all_targets = {t: g for g in groups for t in g}
        else:
            self.all_targets = all_targets

    def print(self, message="", **kwargs):
        """Print this state to stdout using provided helpers"""
        board_dict = {}
        for sq, n in self.stacks.items():
            board_dict[sq] = "({:X})".format(n)
        for sq in self.all_targets.keys():
            board_dict[sq] = "[X]"
        print_board(board_dict, message, **kwargs)

    # for search algorithm:
    def is_goal(self):
        """Check if this state is a goal state (have all groups gone boom?)"""
        return not self.groups
    
    def heuristic(self):
        """
        Heuristic: What's the minimum number of steps away of a token from
        each remaining group?
        
        Note:
        It's NOT an admissible heuristic! Fast-moving stacks may provide
        a shorter path to a goal state. But the effect of this is small for
        the likely scenarios.
        """
        h = 0
        squares = self.stacks.keys()
        for group in self.groups:
            metric = self.group_metrics[id(group)]
            h += min((metric[sq] for sq in squares), default=inf)
        return h

    def actions_successors(self):
        """
        Generate (action, successor state) pairs for available actions
        from this state.
        """
        for sq in self.stacks.keys():
            boom_action = Boom(sq)
            boom_result = boom_action.apply_to(self)
            yield (boom_action, boom_result)
        for sq_from, n in self.stacks.items():
            for i in range(1, n+1):
                for sq_to in steps(sq_from, distance=i):
                    for m in range(1, n+1):
                        if sq_to not in self.all_targets:
                            move_action = Move(m, sq_from, sq_to)
                            move_result = move_action.apply_to(self)
                            yield (move_action, move_result)
    
    # for detecting duplicated states:
    # could speed up with hash cache if necessary
    def __hash__(self):
        return hash((frozenset(self.stacks.items()),
                frozenset(id(g) for g in self.groups)))
    def __eq__(self, other):
        return ((self.stacks, self.groups) == (other.stacks, other.groups))


class Move:
    def __init__(self, n, a, b):
        """Move n tokens from square a to square b."""
        self.n = n
        self.a = a
        self.b = b

    def apply_to(self, state):
        """Create a new state by applying this action."""
        new_stacks = state.stacks.copy()
        if new_stacks[self.a] == self.n:
            del new_stacks[self.a]
        else:
            new_stacks[self.a] -= self.n
        if self.b not in new_stacks:
            new_stacks[self.b] = self.n
        else:
            new_stacks[self.b] += self.n
        return State(new_stacks, state.groups,
                group_metrics=state.group_metrics,
                all_targets=state.all_targets)

    def print(self, **kwargs):
        """Print an action to stdout according to the format instructions."""
        print_move(self.n, *self.a, *self.b, **kwargs)


class Boom:
    def __init__(self, square):
        """Boom tokens at square."""
        self.square = square

    def apply_to(self, state): 
        """Create a new state by applying this action"""
        stacks_to_remove = set()
        groups_to_remove = set()
        def boom_stack(stack):
            stacks_to_remove.add(stack)
            for square in around_square(stack):
                if square in state.stacks.keys():
                    if square not in stacks_to_remove:
                        boom_stack(square)
                if square in state.all_targets:
                    g = state.all_targets[square]
                    if g not in groups_to_remove:
                        boom_group(g)
        def boom_group(group):
            groups_to_remove.add(group)
            for square in around_group(group):
                if square in state.stacks.keys():
                    if square not in stacks_to_remove:
                        boom_stack(square)
        # recursively compute damage
        boom_stack(self.square)
        # remove exploded tokens
        new_stacks = state.stacks.copy()
        for stack in stacks_to_remove:
            del new_stacks[stack]
        new_groups = state.groups - groups_to_remove
        new_targets = state.all_targets.copy()
        for group in groups_to_remove:
            for target in group:
                del new_targets[target]
        return State(new_stacks, new_groups,
            group_metrics=state.group_metrics,
            all_targets=new_targets)

    def print(self, **kwargs):
        print_boom(*self.square, **kwargs)


def distance_grid(group):
    """
    Precompute a Manhattan distance landscape for a particular group of
    squares---a dictionary of #steps until within explosive zone.
    """
    radius = around_group(group)
    grid = {}
    for xy in BOARD_SQUARES:
        grid[xy] = min(manhattan_distance(xy, square) for square in radius)
    return grid

def manhattan_distance(xy_a, xy_b):
    """
    Number of steps between two squares allowing only
    up, down, left and right steps.
    """
    x_a, y_a = xy_a
    x_b, y_b = xy_b
    return abs(x_a-x_b) + abs(y_a-y_b) 


BOARD_SQUARES = {(x,y) for x in range(8) for y in range(8)}

BOOM_RADIUS = [(-1,+1), (+0,+1), (+1,+1),
               (-1,+0),          (+1,+0),
               (-1,-1), (+0,-1), (+1,-1)]
def around_square(xy):
    """
    Generate the list of squares surrounding a square
    (those affected by a boom action).
    """
    x, y = xy
    for dx, dy in BOOM_RADIUS:
        square = x+dx, y+dy
        if square in BOARD_SQUARES:
            yield square

def around_group(group):
    """The set of squares in explosive range of a set of squares."""
    return set.union(set(group), *[around_square(sq) for sq in group])


MOVE_DIRECTIONS = [(+1,0), (0,+1), (-1,0), (0,-1)]
def steps(start_square, distance=1):
    """
    Generate the squares some number of steps above, below, leftwards
    and rightwards of some start_square.
    """
    x, y = start_square
    for dx, dy in MOVE_DIRECTIONS:
        new_square = x+distance*dx, y+distance*dy
        if new_square in BOARD_SQUARES:
            yield new_square


if __name__ == '__main__':
    main()
