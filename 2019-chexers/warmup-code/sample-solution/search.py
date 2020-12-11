"""
Sample solution to COMP30024 Project Part A 2019:

            Search Algorithm for playing single-player Chexers

This solution uses A* and a simple heuristic to solve the problem. It also 
tries to be reasonably efficient through careful choice of data structures, 
including a custom priority queue module for fast insert/update operations (see
pq.py). The level of commenting is more verbose than probably necessary for 
your own work, as it is meant to aid understanding of the code and techniques 
used.
Feel free to use any code from this solution in your Project Part B programs
(with attribution), but known that you DO SO AT YOUR OWN RISK: I do not 
guarantee that this program is 100% correct and error-free, and it is YOUR
TEAM'S RESPONSIBILITY to create a correct program for Project Part B. 
Furthermore, you may be better off if you spend some effort designing your own 
data structures and algorithms for Part B, to better suit how you want your 
Player to work.

If you have any questions about this program (or if you spot any bugs), please 
take them to the LMS discussion forum or send me an email.

Author: Matthew Farrugia-Roberts
"""

import sys
import json
import math

from pq import PriorityQueue


# # #
# Program entry-point:
#

def main():
    # load data from input file (assumed to be first argument)
    with open(sys.argv[1]) as file:
        data = json.load(file)
    colour = data["colour"]
    # we want coordinates as tuples (for immutability and hashing)
    blocks = list(map(tuple, data["blocks"]))
    # indeed we want to hash the set of pieces as part of our states, so we
    # need it to be a frozenset (immutable set) of tuples (immutable lists) of 
    # coordinates.
    pieces = frozenset(map(tuple, data["pieces"]))
    
    # time to search!
    board = Board(colour, blocks)
    initial_state = State(pieces, board)
    print("# searching...")
    action_sequence = astar_search(initial_state)
    # display the result:
    if action_sequence is not None:
        print("# search complete! here's the action sequence:")
        for action in action_sequence:
            atype, aargs = action
            if atype == 'EXIT':
                print(f"{atype} from {aargs}.")
            else: # atype == 'MOVE' or atype == 'JUMP':
                print(f"{atype} from {aargs[0]} to {aargs[1]}.")
        print("# number of actions:", len(action_sequence))
    else:
        print("# search complete! no path found :(") # (shouldn't happen)


# # #
# Heuristic and A* search algorithm:
#

def h(state):
    """
    Admissible heuristic for single-player Chexers:
    In the best case, a piece can get to the edge of the board in 
    exit_dist // 2 jump actions (plus 1 move action when the distance is 
    odd), and then can exit with 1 action. Since all pieces must exit, we
    sum these best case individual distances from each piece.
    """
    hexes = state.piece_hexes
    dist  = state.board.exit_dist
    return sum(math.ceil(dist(qr) / 2) + 1 for qr in hexes)


def astar_search(initial_state):
    """
    A* search algorithm for single-player Chexers. Conducts a full A* search to 
    the nearest goal state from `initial_state`.
    """
    # store the current best-known partial path cost to each state we have
    # encountered:
    g = {initial_state: 0}
    # store the previous state in this least-cost path, along with action
    # taken to reach each state:
    prev = {initial_state: None}

    # initialise a priority queue with initial state (f(s) = 0 + h(s)):
    queue = PriorityQueue()
    queue.update(initial_state, g[initial_state] + h(initial_state))
    
    # (concurrent iteration is allowed on this priority queue---this will loop 
    # until the queue is empty, and we may modify the queue inside)
    for state in queue:
        # if we are expanding a goal state, we can terminate the search!
        if state.is_goal():
            return reconstruct_action_sequence(state, prev)

        # else, consider all successor states for addition to the queue (if
        # we see a cheaper path)
        # for our problem, all paths through state have the same path cost,
        # so we can just compute it once now:
        g_new = g[state] + 1
        for (action, successor_state) in state.actions_successors():
            # if this is the first time we are seeing the state, or if we
            # have found a new path to the state with lower cost, we must
            # update the priority queue by inserting/modifying this state with
            # the appropriate f-cost.
            # (note: since our heuristic is consistent we should never discover
            # a better path to a previously expanded state)
            if successor_state not in g or g[successor_state] > g_new:
                # a better path! save it:
                g[successor_state] = g_new
                prev[successor_state] = (state, action)
                
                # and update the priority queue
                queue.update(successor_state, g_new + h(successor_state))
    # if the priority queue ever runs dry, then there must be no path to a goal
    # state.
    return None


def reconstruct_action_sequence(goal, prev_states_actions):
    """reconstruct action sequence by traversing a previous state/action map"""
    action_sequence = []
    state = goal
    # work our way backwards from the goal state to the start state:
    while prev_states_actions[state] is not None:
        # where did we come from, and how did we get here?
        prev_state, action = prev_states_actions[state]
        # take note of the action we took to get here
        action_sequence.append(action)
        # then repeat for the state we came from!
        state = prev_state
    # in the end, action_sequence will be backwards
    return list(reversed(action_sequence))


# # # # #
# Supporting data structures:
# Representing Boards and States as custom classes to de-clutter the 
# implementation of the search algorithm
#

class Board:
    """
    Represent an (empty) single-player Chexers game board
    (it's just a grid of hexes, some of which are blocked)
    """
    def __init__(self, colour, blocks):
        """
        Board constructor
        - colour is a string 'red', 'green', or 'blue' (determines exit edge)
        - blocks is an iterable of the coordinates of hexes occupied by blocks
        """
        self.block_hexes = set(blocks)
        self.colour = colour
        if colour == 'red':
            self.exit_hexes = {(3,-3), (3,-2), (3,-1), (3,0)}
        if colour == 'green':
            self.exit_hexes = {(-3,3), (-2,3), (-1,3), (0,3)}
        if colour == 'blue':
            self.exit_hexes = {(-3,0),(-2,-1),(-1,-2),(0,-3)}

        # set of all hexes (for easy bounds checking):
        ran = range(-3, +3+1)
        self.all_hexes = {(q,r) for q in ran for r in ran if -q-r in ran}

    def exit_dist(self, qr):
        """how many hexes away from a coordinate is the nearest exiting hex?"""
        q, r = qr
        if self.colour == 'red':
            return 3 - q
        if self.colour == 'green':
            return 3 - r
        if self.colour == 'blue':
            return 3 - (-q-r)

    def can_exit_from(self, qr):
        """can a piece exit the board from this hex?"""
        return qr in self.exit_hexes
    
    def is_blocked(self, qr):
        """is this hex occupied by a block?"""
        return qr in self.block_hexes
    
    def __contains__(self, qr):
        """allows bounds checking with e.g. `(3, -2) in board` """
        return qr in self.all_hexes


# These are the directions in which moves/jumps are allowed in the game:
HEX_STEPS = [(-1,+0),(+0,-1),(+1,-1),(+1,+0),(+0,+1),(-1,+1)]


class State:
    """
    Represent a particular configuration of a single-player
    Chexers game (consisting of a set of piece coordinates and an
    underlying board, some of whose hexes are blocked)
    """
    def __init__(self, piece_hexes, board):
        """
        State constructor
        - piece_hexes is a frozenset (immutable set) of piece coordinates
        - board is a Board representing the underlying game board
        """
        self.board = board
        self.piece_hexes = piece_hexes 
    
    def actions_successors(self):
        """
        construct and return a list of all actions available from this state
        (and their resulting successor states)
        """
        actions_successors_list = []
        for action in self._actions():
            actions_successors_list.append((action, self._apply(action)))
        return actions_successors_list
    
    def _actions(self):
        """
        construct and return a list of all actions available from this state
        """
        available_actions_list = []
        for qr in self.piece_hexes:
            # consider possible exit action:
            if self.board.can_exit_from(qr):
                available_actions_list.append(('EXIT', qr))
        
            # This (subtle!) loop computes available move/jump actions:
            # Logic: In each direction, first try to move (step by 1). If this
            # works, a jump is not possible. If the move is blocked, a jump
            # may be possible: try it. Always make sure not to fall off board.
            q, r = qr
            for step_q, step_r in HEX_STEPS:
                for atype, dist in [('MOVE', 1), ('JUMP', 2)]:
                    qr_t = q+step_q*dist, r+step_r*dist # qr_t = 'target' hex
                    if qr_t in self.board:
                        if not self.board.is_blocked(qr_t) \
                        and qr_t not in self.piece_hexes:
                            available_actions_list.append((atype, (qr, qr_t)))
                            break # only try to jump if the move IS blocked
                    else:
                        break # if a move goes off the board, a jump would too
        if not available_actions_list:
            # Note that this shouldn't happen in Part A, but:
            available_actions_list.append(('PASS', None)) 
        return available_actions_list
    
    def _apply(self, action):
        """
        compute and return the state resulting from taking a particular action 
        in this state
        """
        atype, aargs = action
        if atype == 'PASS':
            return self # no need for a new state
        elif atype == 'EXIT':
            return State(self.piece_hexes - {aargs}, self.board)
        else: # if atype == 'MOVE' or atype == 'JUMP':
            return State(self.piece_hexes - {aargs[0]} | {aargs[1]}, self.board)

    def is_goal(self):
        """Goal test: The game is won when all pieces have exited."""
        return not self.piece_hexes

    # we need to store states in sets and dictionaries, so we had better make
    # them behave well with hashing and equality checking:
    def __eq__(self, other):
        """
        states should compare equal if they have the same pieces
        (all states should share an underlying board in our program, so
        there's no need to check that)
        """
        return self.piece_hexes == other.piece_hexes
    
    def __hash__(self):
        """
        likewise, we should only consider the set of pieces relevant when 
        computing a hash value for a state
        """
        return hash(self.piece_hexes)


if __name__ == '__main__':
    main()