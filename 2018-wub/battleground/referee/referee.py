# Referee for COMP30024: Artificial Intelligence, 2018
# Authors: Matt Farrugia and Shreyash Patodia
# version: v1.0

import time
import argparse
import importlib

VERSION_INFO = """Referee version 1.1 (released Apr 08 2018)
Plays a basic game of Watch Your Back! between two Player classes
Run `python referee.py -h` for help and additional usage information
"""

def main():
    """Coordinate a game of Watch Your Back! between two Player classes."""

    # load command-line options for the game and print welcome message
    options = _Options()
    print(VERSION_INFO)

    # initialise the game and players
    game  = _Game()
    white = _Player(options.white_player, 'white')
    black = _Player(options.black_player, 'black')

    # now, play the game!
    player, opponent = white, black # white has first move
    print(game)
    while game.playing():
        if options.delay:
            time.sleep(options.delay)
        turns = game.turns
        action = player.action(turns)
        try:
            game.update(action)
        except _InvalidActionException as e:
            # if one of the players makes an invalid action,
            # print the error message
            print(f"invalid action ({game.loser}):", e)
            break
        print(game)
        opponent.update(action)
        # other player's turn!
        player, opponent = opponent, player

    print(f'winner: {game.winner}!')

# --------------------------------------------------------------------------- #

# OPTIONS

# default values (to use if flag is not provided)
DELAY_DEFAULT = 0

# missing values (to use if flag is provided, but with no value)
DELAY_NOVALUE = 1.0


class _Options:
    """
    Parse and contain command-line arguments.

    --- help message: ---
    usage: referee.py [-h] [-d [DELAY]] white_module black_module

    Plays a basic game of Watch Your Back! between two Player classes

    positional arguments:
      white_module          full name of module containing White Player class
      black_module          full name of module containing Black Player class

    optional arguments:
      -h, --help            show this help message and exit
      -d [DELAY], --delay [DELAY]
                            how long (float, seconds) to wait between turns
    ---------------------
    """
    def __init__(self):
        parser = argparse.ArgumentParser(
                description="Plays a game of Watch Your Back! between two "
                    "Player classes")
        parser.add_argument('white_module',
                help="full name of module containing White Player class")
        parser.add_argument('black_module',
                help="full name of module containing Black Player class")
        parser.add_argument('-d', '--delay',
                type=float, default=DELAY_DEFAULT, nargs="?",
                help="how long (float, seconds) to wait between turns")

        args = parser.parse_args()

        self.white_player = _load_player(args.white_module)
        self.black_player = _load_player(args.black_module)
        self.delay = args.delay if args.delay is not None else DELAY_NOVALUE

# HELPERS

def _load_player(modulename, package='.'):
    """
    Load a Player class given the name of a module.
    
    :param modulename: where to look for the Player class (name of a module)
    :param package: where to look for the module (relative package)
    :return: the Player class (a class object)
    """
    module = importlib.import_module(modulename, package=package)
    player_class = module.Player
    return player_class

# --------------------------------------------------------------------------- #

# REFEREE'S INTERNAL GAME STATE REPRESENTATION

#                        NOT INTENDED FOR STUDENT USE
# 
# This part of the referee is designed to store the state of a game for the
# purpose of validating actions and providing helpful error messages for when
# players suggest invalid actions. It is not intended to be used by Players.
# You should design and use your own representation of the game and board
# state, optimised with your specific usage in mind: deciding which action to
# to choose each turn.

class _Game:
    """Represent the state of a game of Watch Your Back!"""
    def __init__(self):
        """
        Initializes the representation of the game.

        This 'state' includes the current configuration of the board and 
        information pertaining to the game's progression between phases
        """
        # board configuration (initially empty)
        self.board = [['-' for _ in range(8)] for _ in range(8)]
        for square in [(0, 0), (7, 0), (7, 7), (0, 7)]:
            x, y = square
            self.board[y][x] = 'X'
        self.n_shrinks = 0

        # tracking progress through game phases
        self.turns  = 0
        self.phase  = 'placing'
        self.pieces = {'W': 0, 'B': 0}
        self.winner = None
        self.loser  = None

    _DISPLAY = {'B': '@', 'W': 'O', 'X': 'X', '-': '-', ' ': ' '}
    def __str__(self):
        """String representation of the current game state."""
        displayboard = [[_Game._DISPLAY[p] for p in row] for row in self.board]
        board = '\n'.join(' '.join(row) for row in displayboard)
        if self.playing():
            progress = f'{self.turns} turns into the {self.phase} phase'
        else:
            progress = 'game over!'
        return f'{board}\n{progress}'

    def playing(self):
        """:return: True iff the game is still in progress"""
        return self.phase == 'placing' or self.phase == 'moving'

    def update(self, action):
        """
        Validate an action and update the current state accordingly.

        :raises _InvalidActionException: for any action that is not legal
        according to the rules of the game
        """
        # update the board
        if self.phase == 'placing':
            self._place(action)
        elif self.phase == 'moving':
            if action is None:
                self._forfeit()
            else:
                self._move(action)

        # progress the game
        self.turns += 1
        if self.phase == 'placing':
            if self.turns == 24:
                # time to enter the moving phase!
                self.phase = 'moving'
                self.turns = 0
        if self.phase == 'moving':
            self._check_win()
            if self.phase != 'completed' and self.turns in [128, 192]:
                self._shrink_board()
                self._check_win()

    def _place(self, place):
        """
        Validate a 'place' action and update board configuration accordingly.
        
        :param place: (x, y) tuple representing the square on which to place
        the piece
        """
        # unpack and validate piece representation
        try:
            x, y = place
            assert(isinstance(x, int) and isinstance(y, int))
        except:
            self._invalidate(f"invalid place action representation: {place!r}")

        # validate place itself
        piece = self._piece()

        if not self._within_board(x, y):
            self._invalidate(f"player's place contained invalid coordinates: "
                f"{place}")
        if piece == 'W' and y > 5 or piece == 'B' and y < 2:
            self._invalidate(f"player tried to place outside their starting "
                f"zone: {place}")
        if not self.board[y][x] == '-':
            self._invalidate(f"player tried to place on an occupied square or "
                f"corner: {place}")

        # if that was all okay... we can carry out the place action!
        self.board[y][x] = piece
        self.pieces[piece] += 1
        self._eliminate_about((x, y))


    def _move(self, move):

        """
        Validate a move a -> b and update the board configuration accordingly.

        :param move: nested tuple ((xa, ya), (xb, yb)) representing move
        (xa, ya) -> (xb, yb)
        """
        # unpack and validate move representation
        try:
            (xa, ya), (xb, yb) = a, b = move
            assert(all(isinstance(coordinate, int) for coordinate in a+b))
        except:
            self._invalidate(f"invalid move action representation: {move!r}")
        
        # validate move itself
        piece = self._piece()
        if not (self._within_board(xa, ya) and self._within_board(xb, yb)):
            self._invalidate(f"player's move contained invalid coordinates: "
                f"({a}) -> ({b})")
        if self.board[ya][xa] != piece:
            self._invalidate(f"player tried to move from a square it doesn't "
                f"have a piece on: ({a}) -> ({b})")
        if self.board[yb][xb] != '-':
            self._invalidate(f"player tried to move to an occupied square or "
                f"corner: ({a}) -> ({b})")
        if not (self._is_jump(move) or self._is_move(move)):
            self._invalidate(f"player tried to move to a non-reachable square "
                "(a square that is neither adjacent nor opposite an adjacent "
                f"occupied square): ({a}) -> ({b})")

        # if that was all okay... we can carry out the move!
        self.board[yb][xb] = piece
        self.board[ya][xa] = '-'
        self._eliminate_about(b)

    def _forfeit(self):
        """
        Validate a 'forfeit' (no move) action, which must not be taken unless
        the player has no legal moves available.
        """
        piece = self._piece()
        message = f'player tried to forfeit a move, but had available moves'

        # check for any possible moves for any of the player's pieces
        for xa, ya in self._squares_with_piece(piece):
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                # is the adjacent square unoccupied?
                xb, yb = xa + dx, ya + dy
                if self._within_board(xb, yb) and self.board[yb][xb] == '-':
                    self._invalidate(message)
                # if not, how about the opposite square?
                xb, yb = xb + dx, yb + dy
                if self._within_board(xb, yb) and self.board[yb][xb] == '-':
                    self._invalidate(message)

        # if that was all okay... there are no available moves and so the
        # forfeit was legal! no action required.

    def _squares_with_piece(self, piece):
        """
        Generate coordinates of squares currently containing a piece

        :param piece: string representation of the piece type to check for
        """
        for x in range(8):
            for y in range(8):
                if self.board[y][x] == piece:
                    yield (x, y)

    def _piece(self):
        """:return: the piece of the player with the current turn"""
        return 'W' if self.turns % 2 == 0  else 'B'

    def _other(self):
        """:return: the piece of the other player (not the current turn)"""
        return 'W' if self._piece() == 'B' else 'B'

    def _within_board(self, x, y):
        """
        Check if a given pair of coordinates is 'on the board'.

        :param x: column value
        :param y: row value
        :return: True iff the coordinate is on the board
        """
        for coord in [y, x]:
            if coord < 0 or coord > 7:
                return False
        if self.board[y][x] == ' ':
            return False
        return True

    def _check_win(self):
        """
        Check the board to see if the game has concluded.

        Count the number of pieces remaining for each player: if either player 
        has run out of pieces, decide the winner and transition to the 
        'completed' state
        """
        n_whites = self.pieces['W']
        n_blacks = self.pieces['B']
        if n_whites >= 2 and n_blacks >= 2:
            pass # game continues...
        elif n_whites < 2 and n_blacks >= 2:
            self.winner = 'B'
            self.phase = 'completed'
        elif n_blacks < 2 and n_whites >= 2:
            self.winner = 'W'
            self.phase = 'completed'
        elif n_whites < 2 and n_blacks < 2:
            self.winner = 'draw'
            self.phase = 'completed'

    def _invalidate(self, reason):
        """
        In response to an error, invalidate the game state.
        
        Transition to the 'invalid' state, declare the non-current player
        the winner (the current player has played an invalid action), and 
        raise an exception describing the problem
        
        :param reason: message describing what went wrong (to be included in
        the exception).
        :raises _InvalidActionException: (every time)
        """
        self.phase = 'invalid'
        self.loser  = self._piece()
        self.winner = self._other()
        raise _InvalidActionException(reason)

    def _shrink_board(self):
        """
        Shrink the board, eliminating all pieces along the outermost layer,
        and replacing the corners.

        This method can be called up to two times only.
        """
        s = self.n_shrinks # number of shrinks so far, or 's' for short
        # Remove edges
        for i in range(s, 8 - s):
            for square in [(i, s), (s, i), (i, 7-s), (7-s, i)]:
                x, y = square
                piece = self.board[y][x]
                if piece in self.pieces:
                    self.pieces[piece] -= 1
                self.board[y][x] = ' '
        
        # we have now shrunk the board once more!
        self.n_shrinks = s = s + 1

        # replace the corners (and perform corner elimination)
        for corner in [(s, s), (s, 7-s), (7-s, 7-s), (7-s, s)]:
            x, y = corner
            piece = self.board[y][x]
            if piece in self.pieces:
                self.pieces[piece] -= 1
            self.board[y][x] = 'X'
            self._eliminate_about(corner)

    def _eliminate_about(self, square):
        """
        A piece has entered this square: look around to eliminate adjacent 
        (surrounded) enemy pieces, then possibly eliminate this piece too.
        
        :param square: the square to look around
        """
        x, y = square
        piece = self.board[y][x]
        targets = self._targets(piece)
        
        # Check if piece in square eliminates other pieces
        for dx, dy in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
            target_x, target_y = x + dx, y + dy
            targetval = None
            if self._within_board(target_x, target_y):
                targetval = self.board[target_y][target_x]
            if targetval in targets:
                if self._surrounded(target_x, target_y, -dx, -dy):
                    self.board[target_y][target_x] = '-'
                    self.pieces[targetval] -= 1

        # Check if the current piece is surrounded and should be eliminated
        if piece in self.pieces:
            if self._surrounded(x, y, 1, 0) or self._surrounded(x, y, 0, 1):
                self.board[y][x] = '-'
                self.pieces[piece] -= 1

    def _surrounded(self, x, y, dx, dy):
        """
        Check if piece on (x, y) is surrounded on (x + dx, y + dy) and
        (x - dx, y - dy).
        
        :param x: column of the square to be checked
        :param y: row of the square to be checked
        :param dx: 1 if adjacent cols are to be checked (dy should be 0)
        :param dy: 1 if adjacent rows are to be checked (dx should be 0)
        :return: True iff the square is surrounded
        """
        xa, ya = x + dx, y + dy
        firstval = None
        if self._within_board(xa, ya):
            firstval = self.board[ya][xa]

        xb, yb = x - dx, y - dy
        secondval = None
        if self._within_board(xb, yb):
            secondval = self.board[yb][xb]

        # If both adjacent squares have enemies then this piece is surrounded!
        piece = self.board[y][x]
        enemies = self._enemies(piece)
        return (firstval in enemies and secondval in enemies)

    def _enemies(self, piece):
        """
        Which pieces can eliminate a piece of this type?

        :param piece: the type of piece ('B', 'W', or 'X')
        :return: set of piece types that can eliminate a piece of this type
        """
        if piece == 'B':
            return {'W', 'X'}
        elif piece == 'W':
            return {'B', 'X'}
        return set()

    def _targets(self, piece):
        """
        Which pieces can a piece of this type eliminate?
        
        :param piece: the type of piece ('B', 'W', or 'X')
        :return: the set of piece types that a piece of this type can eliminate
        """
        if piece == 'B':
            return {'W'}
        elif piece == 'W':
            return {'B'}
        elif piece == 'X':
            return {'B', 'W'}
        return set()

    def _is_move(self, move):
        """
        Check if a move is a 'simple' move in terms of distance.
        
        :return: True is the move is a correct 'simple' move
        """
        (xa, ya), (xb, yb) = move
        if xa == xb and abs(ya - yb) == 1:
            return True
        if ya == yb and abs(xa - xb) == 1:
            return True
        return False

    def _is_jump(self, move):
        """
        Check if a move is a 'jump' move in terms of distance.
        
        :return: True iff the move is a correct 'jump' move
        """
        (xa, ya), (xb, yb) = move
        if xa == xb and abs(ya - yb) == 2:
            if self.board[min(ya, yb) + 1][xa] in self.pieces:
                return True
        elif ya == yb and abs(xa - xb) == 2:
            if self.board[ya][min(xa, xb) + 1] in self.pieces:
                return True
        return False

# --------------------------------------------------------------------------- #

# HELPER CLASSES

class _Player:
    """Wrapper for a Player class to simplify initialization"""
    def __init__(self, player_class, colour):
        self.player = player_class(colour)
    def update(self, move):
        self.player.update(move)
    def action(self, turns):
        action = self.player.action(turns)
        return action

class _InvalidActionException(Exception):
    """For when an action breaks the rules of the game"""

# --------------------------------------------------------------------------- #

if __name__ == '__main__':
    main()
