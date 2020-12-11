"""
Provide a class to maintain the state of an evolving game,
including validation of actions, detection of draws,
and optionally maintaining a game log.

NOTE:
This board representation is designed to be used internally by the referee
for the purposes of validating actions and displaying the result of the game.
Each player is expected to store its own internal representation of the board
for use in informing decisions about which action to choose each turn. Please
don't look to this module as an example of a useful board representation for
these purposes; you should think carefully about how to design your own data
structures for representing the state of a game.
"""

import sys
import time
from collections import Counter



# Game-specific constants for use in other modules:

GAME_NAME = "Expendibots"
COLOURS = "white", "black"
NUM_PLAYERS = 2



# Generic play function:

def play(players,
         delay=0, logfilename=None, out_function=None, print_state=True,
         use_debugboard=False, use_colour=False, use_unicode=False):
    """
    Coordinate a game, return a string describing the result.

    Arguments:
    players -- A list of Player wrappers supporting init, action and update
        methods.
    delay -- Time in seconds to wait between turns, or negative to wait for
        user input.
    logfilename -- If not None, log progress of the game at this path.
    out_function -- Function to use for printing commentary about the game.
    print_state -- If True, print a picture of the board after each update.
    use_debugboard -- If True, use a larger board during updates (if print_
        state is also True).
    use_colour -- Use ANSI colour codes for output.
    use_unicode -- Use unicode symbols for output.
    """
    # Configure behaviour of this function depending on parameters:
    out = out_function if out_function else (lambda *_, **__: None) # no-op
    if delay > 0:
        def wait(): time.sleep(delay)
    elif delay < 0:
        def wait():
            out("(press enter to continue)", end="")
            input()
    else:
        def wait(): pass
    if print_state:
        def display_state(game):
            out("displaying game info:")
            out(game, depth=1)
    else:
        def display_state(game): pass

    # Set up a new game and initialise the players (constructing the
    # Player classes including running their .__init__() methods).
    game = Game(logfilename=logfilename, debugboard=use_debugboard,
                colourboard=use_colour, unicodeboard=use_unicode)
    out("initialising players", depth=-1)
    for player, colour in zip(players, COLOURS):
        # NOTE: `player` here is actually a player wrapper. Your program should
        # still implement a method called `__init__()`, not one called `init()`.
        player.init(colour)

    # Display the initial state of the game.
    out("game start!", depth=-1)
    display_state(game)

    # Repeat the following until the game ends
    # (starting with White as the current player, then alternating):
    curr_player, next_player = players
    while not game.over():
        wait()
        out(f"{curr_player.name}'s turn", depth=-1, clear=True)

        # Ask the current player for their next action (calling their .action()
        # method).
        action = curr_player.action()

        # Validate this action (or pass) and apply it to the game if it is
        # allowed. Display the resulting game state.
        game.update(curr_player.colour, action)
        display_state(game)

        # Notify both players (including the current player) of the action
        # (using their .update() methods).
        for player in players:
            player.update(curr_player.colour, action)

        # Next player's turn!
        curr_player, next_player = next_player, curr_player

    # After that loop, the game has ended (one way or another!)
    return game.end()




# Implementation of the game:

_ALL_SQUARES = {(x, y) for x in range(8) for y in range(8)}

_BLACK_START_SQUARES = [(0,7), (1,7),   (3,7), (4,7),   (6,7), (7,7),
                        (0,6), (1,6),   (3,6), (4,6),   (6,6), (7,6)]
_WHITE_START_SQUARES = [(0,1), (1,1),   (3,1), (4,1),   (6,1), (7,1),
                        (0,0), (1,0),   (3,0), (4,0),   (6,0), (7,0)]

def _NEXT_SQUARES(square, d=1):
    x, y = square
    return {        (x,y+d),
            (x-d,y),        (x+d,y),
                    (x,y-d)        } & _ALL_SQUARES

def _NEAR_SQUARES(square):
    x, y = square
    return {(x-1,y+1),(x,y+1),(x+1,y+1),
            (x-1,y),          (x+1,y),
            (x-1,y-1),(x,y-1),(x+1,y-1)} & _ALL_SQUARES

_MAX_TURNS = 250 # per player
 


class Game:
    """
    Represent the evolving state of a game. Main useful methods
    are __init__, update, over, end, and __str__.
    """
    def __init__(self, logfilename=None, debugboard=False, unicodeboard=False,
            colourboard=False):
        # initialise game board state:
        self.board = Counter({xy: 0 for xy in _ALL_SQUARES})
        for xy in _WHITE_START_SQUARES:
            self.board[xy] = +1
        for xy in _BLACK_START_SQUARES:
            self.board[xy] = -1
        # also keep track of some other state variables for win/draw
        # detection (score, number of turns, state history)
        self.score = {'white': 12, 'black': 12}
        self.drawmsg = ""
        self.nturns  = 0
        self.history = Counter({self._snap(): 1})

        # when we print the board, should we show coordinates?
        if debugboard:
            if unicodeboard:
                self.board_template = _BOARD_TEMPLATE_UNICODE_DEBUG
            else:
                self.board_template = _BOARD_TEMPLATE_ASCII_DEBUG
        else:
            if unicodeboard:
                self.board_template = _BOARD_TEMPLATE_UNICODE_SMALL
            else:
                self.board_template = _BOARD_TEMPLATE_ASCII_SMALL
        # and should we use colour?
        if colourboard:
            self.white_stack_template = _STACK_TEMPLATE_WHITE_COLOUR
            self.black_stack_template = _STACK_TEMPLATE_BLACK_COLOUR
        else:
            self.white_stack_template = _STACK_TEMPLATE_WHITE_NORMAL
            self.black_stack_template = _STACK_TEMPLATE_BLACK_NORMAL

        # and we might like to log actions!
        if logfilename is not None:
            self._logfile = open(logfilename, 'w', 1)
            self._log("game", "Start game log at", time.asctime())
        else:
            self._logfile = None
        
    def update(self, colour, action):
        """
        Submit an action to the game for validation and application.
        If the action is not allowed, raise an InvalidActionException with
        a message describing allowed actions.
        Otherwise, apply the action to the game state.
        """
        available_actions = self._available_actions(colour)
        if action not in available_actions:
            result = f"illegal action detected ({colour}): {action!r}."
            self._log("error", result)
            # NOTE: The game instance _could_ potentially be recovered, but:
            self._end_log()
            available_actions_list_str = '\n* '.join(
                [f'{a!r} - {_FORMAT_ACTION(a)}' for a in available_actions])
            raise IllegalActionException(
                f"{colour} player's action, {action!r}, is not well-formed or "
                "not available. See specification and game rules for details, "
                "or consider currently available actions:\n"
                f"* {available_actions_list_str}")
        # otherwise, apply the action
        atype, *aargs = action
        if atype == "MOVE":
            n, a, b = aargs
            n = -n if self.board[a] < 0 else n
            self.board[a] -= n
            self.board[b] += n
        else: # atype == "BOOM":
            start_square, = aargs
            to_boom = [start_square]
            for boom_square in to_boom:
                n = self.board[boom_square]
                self.score["white" if n > 0 else "black"] -= abs(n)
                self.board[boom_square] = 0
                for near_square in _NEAR_SQUARES(boom_square):
                    if self.board[near_square] != 0:
                        to_boom.append(near_square)
        self._log(colour, _FORMAT_ACTION(action))
        self._turn_detect_draw()
        # TODO: return a sanitised version of the action?

    def _available_actions(self, colour):
        """
        A list of currently-available actions for a particular player
        (assists validation).
        """
        available_actions = []
        if colour == "white":
            stacks = +self.board
        else:
            stacks = -self.board
        for square in stacks.keys():
            available_actions.append(("BOOM", square))
        for square, n in stacks.items():
            for d in range(1, n+1):
                for next_square in _NEXT_SQUARES(square, d):
                    if next_square in stacks or self.board[next_square] == 0:
                        for m in range(1, n+1):
                            move_action = ("MOVE", m, square, next_square)
                            available_actions.append(move_action)
        return available_actions

    def _turn_detect_draw(self):
        """
        Register that a turn has passed: Update turn counts and 
        detect repeated game states.
        """
        self.nturns += 1
        if self.nturns >= _MAX_TURNS * 2:
            self.drawmsg = "maximum number of turns reached."
        
        state = self._snap()
        self.history[state] += 1
        if self.history[state] >= 4:
            self.drawmsg = "game state occurred 4 times."

    def _snap(self):
        """
        Capture the current board state in a hashable way
        (for repeated-state checking)
        """
        return (
            # same colour tokens in the same positions
            tuple((sq,n) for sq,n in self.board.items() if n),
            # on the same player's turn
            self.nturns % 2,
        )


    def over(self):
        """True iff the game over (draw or win detected)."""
        win_detected  = min(self.score.values()) == 0
        draw_detected = self.drawmsg != ""
        return win_detected or draw_detected

    def end(self):
        """
        Conclude the game, extracting a string describing result (win or draw)
        This method should always be called to conclude a game so that this
        class has a chance to close the logfile, too.
        If the game is not over this is a no-op.
        """
        if self.over():
            # possible reasons draw was detected:
            # no tokens remaining (draw)
            if max(self.score.values()) == 0:
                result = "draw detected: no tokens remaining"
            # one player's tokens remaining (win)
            elif min(self.score.values()) == 0:
                winner = max(self.score.keys(), key=self.score.get)
                result = "winner: " + winner
            # technical draw detected (draw)
            else:
                result = f"draw detected: {self.drawmsg}"
            self._log("over", result)
            self._end_log()
            return result

    def __str__(self):
        """Create and return a representation of board for printing."""
        coords = [(x,7-y) for y in range(8) for x in range(8)] # template order
        cells = []
        for square in coords:
            n = self.board[square]
            if n > 0:
                cells.append(self.white_stack_template.format(n=n))
            elif self.board[square] < 0:
                cells.append(self.black_stack_template.format(n=-n))
            else: # n == 0:
                cells.append("   ")
        score_str = "white: {white}, black: {black}".format(**self.score)
        return self.board_template.format(score_str, *cells)

    def _log(self, header, *messages):
        """Helper method to add a message to the logfile"""
        if self._logfile is not None:
            print(f"[{header:5s}] -", *messages, file=self._logfile, flush=True)
    def _end_log(self):
        if self._logfile is not None:
            self._logfile.close()
            self._logfile = None



class IllegalActionException(Exception):
    """If this action is illegal based on the current board state."""



# Display-specific constants

_STACK_TEMPLATE_WHITE_COLOUR = (
    "\033[1m"  "("               # bold "("
    "\033[96m" "{n:X}" "\033[0m" # bold, bright cyan hexadecimal n
    "\033[1m"  ")"     "\033[0m" # bold ")"
)
_STACK_TEMPLATE_BLACK_COLOUR = (
    "\033[1m"  "["     "\033[0m" # bold "["
    "\033[34m" "{n:X}" "\033[0m" # dark blue hexadecimal n
    "\033[1m"  "]"     "\033[0m" # bold "]"
)
_STACK_TEMPLATE_WHITE_NORMAL = "({n:X})"
_STACK_TEMPLATE_BLACK_NORMAL = "[{n:X}]"

_BOARD_TEMPLATE_UNICODE_SMALL = """tokens: {}
   ┌───┬───┬───┬───┬───┬───┬───┬───┐
 7 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 6 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 5 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 4 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 3 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 2 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 1 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   ├───┼───┼───┼───┼───┼───┼───┼───┤
 0 │{:}│{:}│{:}│{:}│{:}│{:}│{:}│{:}│
   └───┴───┴───┴───┴───┴───┴───┴───┘
y/x  0   1   2   3   4   5   6   7"""
_BOARD_TEMPLATE_UNICODE_DEBUG = """tokens: {}
board:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │
│ 0,7 │ 1,7 │ 2,7 │ 3,7 │ 4,7 │ 5,7 │ 6,7 │ 7,7 │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │
│ 0,6 │ 1,6 │ 2,6 │ 3,6 │ 4,6 │ 5,6 │ 6,6 │ 7,6 │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ key:
│ 0,5 │ 1,5 │ 2,5 │ 3,5 │ 4,5 │ 5,5 │ 6,5 │ 7,5 │
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤ white
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ stack:
│ 0,4 │ 1,4 │ 2,4 │ 3,4 │ 4,4 │ 5,4 │ 6,4 │ 7,4 │ ┌─────┐
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤ │ (n) │
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ │ x,y │
│ 0,3 │ 1,3 │ 2,3 │ 3,3 │ 4,3 │ 5,3 │ 6,3 │ 7,3 │ └─────┘
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤ black
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ stack:
│ 0,2 │ 1,2 │ 2,2 │ 3,2 │ 4,2 │ 5,2 │ 6,2 │ 7,2 │ ┌─────┐
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤ │ [n] │
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ │ x,y │
│ 0,1 │ 1,1 │ 2,1 │ 3,1 │ 4,1 │ 5,1 │ 6,1 │ 7,1 │ └─────┘
├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤ n > 9:
│ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │ {:} │  A: 10
│ 0,0 │ 1,0 │ 2,0 │ 3,0 │ 4,0 │ 5,0 │ 6,0 │ 7,0 │  B: 11
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘  C: 12"""
_BOARD_TEMPLATE_ASCII_SMALL = """tokens: {}
   +---+---+---+---+---+---+---+---+
 7 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
 6 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
 5 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
 4 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
 3 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
 2 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
 1 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
 0 |{:}|{:}|{:}|{:}|{:}|{:}|{:}|{:}|
   +---+---+---+---+---+---+---+---+
y/x  0   1   2   3   4   5   6   7"""
_BOARD_TEMPLATE_ASCII_DEBUG = """tokens: {}
board:
+-----+-----+-----+-----+-----+-----+-----+-----+
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} |
| 0,7 | 1,7 | 2,7 | 3,7 | 4,7 | 5,7 | 6,7 | 7,7 |
+-----+-----+-----+-----+-----+-----+-----+-----+
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} |
| 0,6 | 1,6 | 2,6 | 3,6 | 4,6 | 5,6 | 6,6 | 7,6 |
+-----+-----+-----+-----+-----+-----+-----+-----+
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} | key:
| 0,5 | 1,5 | 2,5 | 3,5 | 4,5 | 5,5 | 6,5 | 7,5 |
+-----+-----+-----+-----+-----+-----+-----+-----+ white
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} | stack:
| 0,4 | 1,4 | 2,4 | 3,4 | 4,4 | 5,4 | 6,4 | 7,4 | +-----+
+-----+-----+-----+-----+-----+-----+-----+-----+ | (n) |
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} | | x,y |
| 0,3 | 1,3 | 2,3 | 3,3 | 4,3 | 5,3 | 6,3 | 7,3 | +-----+
+-----+-----+-----+-----+-----+-----+-----+-----+ black
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} | stack:
| 0,2 | 1,2 | 2,2 | 3,2 | 4,2 | 5,2 | 6,2 | 7,2 | +-----+
+-----+-----+-----+-----+-----+-----+-----+-----+ | [n] |
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} | | x,y |
| 0,1 | 1,1 | 2,1 | 3,1 | 4,1 | 5,1 | 6,1 | 7,1 | +-----+
+-----+-----+-----+-----+-----+-----+-----+-----+ n > 9:
| {:} | {:} | {:} | {:} | {:} | {:} | {:} | {:} |  A: 10
| 0,0 | 1,0 | 2,0 | 3,0 | 4,0 | 5,0 | 6,0 | 7,0 |  B: 11
+-----+-----+-----+-----+-----+-----+-----+-----+  C: 12"""

def _FORMAT_ACTION(action):
    atype, *aargs = action
    if atype == "MOVE":
        return "MOVE {} from {} to {}.".format(*aargs)
    else: # atype == "BOOM":
        return "BOOM at {}.".format(*aargs)
