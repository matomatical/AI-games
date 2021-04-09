"""
Script for solving the two calculations of COMP30024 2018's Project Part A.

This script does the following:

1. read a board configuration from standard input (stdin) using the `input()` 
   function. convert this data to a 'Board' object using our custom 
   representation.
2. read one more line from standard input containing a command to calculate:
    a. if it's the command `"Moves"`, calculate the number of legal moves
       available for each player from the board configuration, and print these
       results to the standard output (stdout)
    b. if it's the command `"Massacre"`, use an Iterative Deepening Search
       method (`ids()`) to find a sequence of moves that lead to all of the 
       Black player's pieces being eliminated. print the resulting sequence
       to the standard output (stoud) using the required format.

Along the way it uses the `log()` function to simplify the process of sending
useful debugging information to standard error output (stderr) (instead of 
standard output (stdout), which must be reserved for printing the answers).
`log(...)` is pretty much just a shorthand for `print(..., file=sys.stderr)`


Author: Matt Farrugia <matt.farrugia@unimelb.edu.au>
April 2018
"""

from watchyourback import Board, Piece

BOARD_SIZE = 8

# Main program:

def main():
    log("Please enter board state:")
    data = [input().split() for _ in range(BOARD_SIZE)]
    board = Board(data)
    log("Board received:", board, sep='\n')
    log("Please enter calculation type:")
    calc = input()
    if calc == "Moves":
        log("Calculating *Moves*")
        log("(number of legal moves for each player)")
        calc_moves(board)

    elif calc == "Massacre":
        log("Calculating *Massacre*")
        log("(sequence of moves to eliminate all enemies)")
        calc_massacre(board)

    log("Done!")

# Code for calculating "Moves":

def calc_moves(board):
    log("White player:")
    print(sum(len(piece.moves()) for piece in board.white_pieces))
    log("Black player:")
    print(sum(len(piece.moves()) for piece in board.black_pieces))

# Code for calculating "Massacre":

def calc_massacre(board):
    result = ids(board)
    log("Moves:", result)
    log(board)
    for move in result:
        piece, newpos = move
        print(f"{piece.pos} -> {newpos}")
        piece.makemove(newpos)
        log(board)

def ids(board):
    """Iterative Deepening Search (IDS) algorithm. Repeatedly run a
    depth-Limited Depth-First Search (DFSL, function `dfsl()`) with an
    ever-increasing depth-limit on a board, until we find a solution.

    The solution will come out of `dfsl()` as a sequence of moves in reverse 
    order (last move first, first move last), so reverse that and return it
    back to the caller.
    """
    depth_limit = 0
    while True:
        result = dfsl(board, depth_limit)
        if result is not None:
            return list(reversed(result))
        depth_limit += 1

def dfsl(board, depth_limit):
    """
    The real bulk of this algorithm! Run a depth-limited DFS (DFSL) looking for
    a sequence of moves that will lead to all of the Black player's pieces on
    the board `board` being eliminated.

    Return a (reversed) sequence of moves that, when applied to `board`, would
    lead to a configuration with no remaining Black pieces. If no such sequence
    is found within this depth limit, return `None` instead.

    Relies heavily on the ability to make and then _unmake_ certain moves,
    which means we can try out moves on this board without repeatedly creating
    new boards (we can mutate one board instead, and as long as we put it back
    to the way it was after we are finished trying each move, there's no harm
    done). Avoiding cloning a board so many times will probably save this 
    function a lot of computation time.
    """
    # base cases
    if all(not piece.alive for piece in board.black_pieces):
        # goal! start building a path
        return []

    elif depth_limit == 0:
        # no path found to goal with this depth limit
        return None

    # recursive case: try all possible moves for all remaining pieces
    remaining_pieces = [p for p in board.white_pieces if p.alive]
    for piece in remaining_pieces:
        for newpos in piece.moves():
            oldpos = piece.pos
            eliminated_pieces = piece.makemove(newpos)
            result = dfsl(board, depth_limit-1)
            piece.undomove(oldpos, eliminated_pieces)

            if result is not None:
                # recursively found a sequence of moves to a goal state! hooray!
                # continue building the (reversed) sequence on the way back up
                result.append((piece, newpos))
                return result
            # otherwise, continue searching

    # no sequence found using any possible move (with this depth limit)
    return None

# for logging to stderr (so as not to effect answer on stdout)
import sys
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# entry-point to program
if __name__ == '__main__':
    main()
