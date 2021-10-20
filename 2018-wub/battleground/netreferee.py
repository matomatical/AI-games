"""
Networked Watch Your Back! client for COMP30024: Artificial Intelligence, 2018

version 1.0

by Matt Farrugia (based on referee by Matt Farrugia and Shreyash Patodia)
"""

import argparse
import importlib
from wubpp import connect, WUBPlayerProtocol
from wubpp import DisconnectException, ProtocolException

VERSION_INFO = """NetReferee version 1.0 (released May 06 2018)
Coordinate a game of Watch Your Back! between your Player class and the server.
Run `python netreferee.py -h` for help and additional usage information
"""

def main():
    """
    Coordinate a game of Watch Your Back! between your Player class and the 
    server.
    """

    # load command-line options for the game and print welcome message
    options = _Options()
    print(VERSION_INFO)

    # play the game, catching any errors and displaying them to the user
    try:
        play(options)
    except KeyboardInterrupt:
        print("\nbye!")
    except DisconnectException as e:
        print(e)
    except ProtocolException as e:
        print(e)
    # (if it's another kind of error it might be coming from the player itself)


def play(options):
    print("welcome,", options.name)
    
    # SET UP GAME

    # attempt to connect to the server
    print("attempting to connect to the server...")
    socket = connect(options.host, options.port)
    server = WUBPlayerProtocol(socket)
    print("connection established!")

    
    # we would like to play a game!
    keystr = f" with key '{options.key}')" if options.key else ""
    print(f"submitting game request for player '{options.name}'{keystr}...")
    server.sendmsg('PLAY', options.name, options.key)
    okaymsg = server.recvmsg()
    print("game request submitted!")
    
    # wait for the server to begin a game for us...
    keystr = f"key '{options.key}')" if options.key else "default key"
    print(f"waiting for an opponent (with {keystr})")
    print("press ^C to stop waiting")
    gamemsg = server.recvmsg()

    # when we get the message, it's time to play!
    print("opponent found! beginning game")
    print("white player:", gamemsg['white'])
    print("black player:", gamemsg['black'])
    server.sendmsg('OKAY')

    # PLAY THE GAME

    # initialise our player
    initmsg = server.recvmsg()
    player = _Player(options.player, initmsg['colour'])
    server.sendmsg('OKAY')

    # now, play the game!
    game = _Game()
    print(game)

    while True:
        msg = server.recvmsg()
        if msg['head'] == 'TURN':
            # it's our turn!
    
            # decide on action
            action = player.action(msg['turns'])

            # submit to server
            actiontype, actionargs = format_action(action)
            server.sendmsg('ACTN', actiontype, *actionargs)

        elif msg['head'] == 'UPD8':
            # opponent made a move!

            # update our player
            if msg['type'] == 'pass':
                action = None
            elif msg['type'] == 'place':
                action = (msg['x'], msg['y'])
            elif msg['type'] == 'move':
                action = ((msg['xa'], msg['ya']), (msg['xb'], msg['yb']))
            player.update(action)

            # and notify server we are ready to continue
            server.sendmsg('OKAY')
        
        elif msg['head'] == 'ERRO':
            # we or the opponent made an illegal move :'(
            # print out error message and end the game
            print('game over!')
            print(msg['loser'], 'loses:')
            print(msg['reason'])
            break

        elif msg['head'] == 'OVER':
            # the game ended
            # print out a message and end the game
            print('game over!')
            print(msg['winner'], 'wins!')
            break
    
        # finally, at the end of each turn, update our game for printing
        game.update(action)
        print(game)


def format_action(action):
    if action is None:
        return 'pass', []
    try:
        (xa, ya), (xb, yb) = action
        return 'move', [xa, ya, xb, yb]
    except:
        pass
    try:
        (x, y) = action
        return 'place', [x, y]
    except:
        pass
    raise Exception(f'Invalid action return value format: {action!r}')

# --------------------------------------------------------------------------- #

# OPTIONS

# default values (to use if flag is not provided)
PORT_DEFAULT = 7979
HOST_DEFAULT = 'wub.aiproj.net'
KEY_DEFAULT  = ''

# missing values (to use if flag is provided, but with no value)
# ... none at the moment

class _Options:
    """
    Parse and contain command-line arguments.

    --- help message: ---
    usage: client.py [-h] [--host HOST] [--port PORT]
                     player_module player_name [game_key]

    Plays a game of Watch Your Back! between your Player class and another, over
    the network

    positional arguments:
      player_module  full name of module containing Player class
      player_name    team name or name of Player (no spaces)
      game_key       only play games against players with the same key (leave it
                     blank to play against anyone)

    optional arguments:
      -h, --help     show this help message and exit
      --host HOST    name of referee server to connect to
      --port PORT    port to contact the referee server on
    ---------------------
    """
    def __init__(self):
        parser = argparse.ArgumentParser(
                description="Plays a game of Watch Your Back! between your "
                    "Player class and another, over the network")
        parser.add_argument('player_module',
                help="full name of module containing Player class")
        parser.add_argument('player_name',
                help="team name or name of Player (no spaces)")
        parser.add_argument('game_key', default=KEY_DEFAULT, nargs="?",
                help="only play games against players with the same "
                "key (leave it blank to play against anyone)")
        parser.add_argument('--host', type=str, default=HOST_DEFAULT,
                help="name of referee server to connect to")
        parser.add_argument('--port', type=int, default=PORT_DEFAULT,
                help="port to contact the referee server on")

        args = parser.parse_args()

        self.player = _load_player(args.player_module)
        self.host, self.port = args.host, args.port
        self.name = _no_spaces(args.player_name, replace_with='_')
        self.key  = _no_spaces(args.game_key,    replace_with='_')

# HELPER FUNCTIONS

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

def _no_spaces(string, replace_with='_'):
    """
    Remove whitespace from a string, replacing chunks of whitespace with a
    particular character combination (replace_with, default is underscore)
    """
    return replace_with.join(string.split())

# --------------------------------------------------------------------------- #

# CLIENT'S INTERNAL GAME STATE REPRESENTATION

#                        NOT INTENDED FOR STUDENT USE
# 
# This part of the referee is designed to store the state of a game for the
# purpose of displaying the current state of the game at the end of each turn.
# It is not intended to be used by Players. You should design and use your own 
# representation of the game and board state, optimised with your specific usage
# in mind: deciding which action to to choose each turn.

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
        
    _DISPLAY = {'B': '@', 'W': 'O', 'X': 'X', '-': '-', ' ': ' '}
    def __str__(self):
        """String representation of the current game state."""
        displayboard = [[_Game._DISPLAY[p] for p in row] for row in self.board]
        board = '\n'.join(' '.join(row) for row in displayboard)
        progress = f'after {self.turns} turns into the {self.phase} phase'
        return f'{board}\n{progress}'

    def update(self, action):
        """
        Validate an action and update the current state accordingly.

        :raises _InvalidActionException: for any action that is not legal
        according to the rules of the game
        """
        # update the board
        if self.phase == 'placing':
            try:
                self._place(action)
            except:
                pass
        elif self.phase == 'moving':
            if action is not None:
                try:
                    self._move(action)
                except:
                    pass

        # progress the game
        self.turns += 1
        if self.phase == 'placing':
            if self.turns == 24:
                # time to enter the moving phase!
                self.phase = 'moving'
                self.turns = 0
        if self.phase == 'moving':
            # TODO: fix bug when you win RIGHT before a shrink!
            # need to restore counting remaining pieces?
            if self.turns in [128, 192]:
                self._shrink_board()

    def _place(self, place):
        """Update board configuration accordng to a 'place' action."""
        x, y = place
        piece = self._piece()

        self.board[y][x] = piece
        self._eliminate_about((x, y))

    def _move(self, move):
        """Update board configuration according to a 'move' action (a -> b)"""
        (xa, ya), (xb, yb) = a, b = move
        piece = self._piece()

        self.board[yb][xb] = piece
        self.board[ya][xa] = '-'
        self._eliminate_about(b)

    def _piece(self):
        """:return: the piece of the player with the current turn"""
        return 'W' if self.turns % 2 == 0  else 'B'

    def _shrink_board(self):
        """
        Shrink the board, eliminating all pieces along the outermost layer,
        and replacing the corners.

        This method should be called up to two times only.
        """
        s = self.n_shrinks # number of shrinks so far, or 's' for short
        
        # remove edges
        for i in range(s, 8 - s):
            for square in [(i, s), (s, i), (i, 7-s), (7-s, i)]:
                x, y = square
                piece = self.board[y][x]
                self.board[y][x] = ' '
        
        # we have now shrunk the board once more!
        self.n_shrinks = s = s + 1

        # replace the corners (and perform corner elimination)
        for corner in [(s, s), (s, 7-s), (7-s, 7-s), (7-s, s)]:
            x, y = corner
            piece = self.board[y][x]
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
        
        # check if piece in square eliminates other pieces
        for dx, dy in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
            target_x, target_y = x + dx, y + dy
            targetval = None
            if self._within_board(target_x, target_y):
                targetval = self.board[target_y][target_x]
            if targetval in targets:
                if self._surrounded(target_x, target_y, -dx, -dy):
                    self.board[target_y][target_x] = '-'

        # check if the current piece is surrounded and should be eliminated
        if self._surrounded(x, y, 1, 0) or self._surrounded(x, y, 0, 1):
            self.board[y][x] = '-'
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
        """Which pieces can eliminate a piece of this type?"""
        if piece == 'B':
            return {'W', 'X'}
        elif piece == 'W':
            return {'B', 'X'}
        return set()

    def _targets(self, piece):
        """Which pieces can a piece of this type eliminate?"""
        if piece == 'B':
            return {'W'}
        elif piece == 'W':
            return {'B'}
        elif piece == 'X':
            return {'B', 'W'}
        return set()

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

# --------------------------------------------------------------------------- #

if __name__ == '__main__':
    main()
