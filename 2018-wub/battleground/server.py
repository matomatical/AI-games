"""
Multi-threaded match-making Watch Your Back! game referee server

by Matt Farrugia, created May 2018
"""

import threading
from collections import deque

from wubpp import listen, WUBPlayerProtocol
from wub import Game, InvalidActionException

HOST = ""    # allow all incoming connections
PORT = 7979  # on this particular port

def main():

    # initialise new logfile
    log(",~* new logfile started *~'")

    # listen for connections incoming on port
    welcome_socket = listen(HOST, PORT)
    log(f"listening on port {PORT}...")


    # set up the matchmaking pool
    matchmaking = MatchmakingPool()

    while True:
        # accept a new connection
        client_socket, client_address = welcome_socket.accept()
        log("new client connected: ", client_address)

        # create a new thread to handle them
        log("starting them a new thread...")
        handler = threading.Thread(
            target=servant,
            args=(client_socket, matchmaking))
        handler.start()



# HANDLING THREADS

def servant(client_socket, matchmaking):
    log("hello, world!")

    # at your service, client!
    # let's begin the protocol
    player_client = WUBPlayerProtocol(client_socket)

    # first thing's first, could you send me a PLAY request
    # containing your name and play key?
    log("waiting for PLAY request...")
    try:
        playmsg = player_client.recvmsg()
        player_name  = playmsg['name']
        matching_key = playmsg['key']
    except Exception as e:
        log("PLAY error:", type(e), e)
        log("exiting thread, bye!")
        player_client.disconnect()
        return
    log("successfully received PLAY request:", playmsg)
    
    # great! thank you very much!
    log("sending OKAY message")
    player_client.sendmsg('OKAY')

    # okay, now just wait a moment, I'll look for a suitable opponent
    # for you to play with...
    log("waiting for matchmaking lock...")
    with matchmaking.lock:
        log("matchmaking lock acquired!")
        # look for a matching waiting client:
        while matchmaking.has_waiting(matching_key):
            log("there's someone waiting!")
            opponent_client, opponent_name = matchmaking.dequeue(matching_key)
            log("it's player:", opponent_name)

            # are they still connected?
            log("sending them a GAME message")
            opponent_client.sendmsg('GAME', opponent_name, player_name)
            log("waiting for OKAY response...")
            try:
                okaymsg = opponent_client.recvmsg()
            except Exception as e:
                # nope...
                log("OKAY error:", type(e), e)
                log("abandon this opponent")
                opponent_client.disconnect()
                log("try again.")
                continue
            log("successfully received OKAY response:", okaymsg)

            # yep! let's play with this opponent_client
            log("thus, this opponent is still connected---we found a match!")
            break

        else:
            # `else` clause on Python `while` statement
            # 
            # > The else clause is only executed when your while condition 
            # > becomes false. If you break out of the loop, or if an exception 
            # > is raised, it won't be executed.
            # 
            # https://stackoverflow.com/a/3295949/5395650

            # nobody is waiting with this passphrase, we'll have to leave our
            # client in the pool for someone else to come along
            log("no match found")
            log("deposit our client in the match pool")
            matchmaking.deposit(matching_key, (player_client, player_name))

            # this is as far as I can take you, good sir/madam. you'l have to
            # wait here for another thread to pick you up to play a game. it has
            # been my eternal pleasure. farewell...
            log("exiting thread, bye!")
            log("(releasing matchmaking lock in doing so, due to `with`)")
            log("(but NOT disconnecting the client---another thread will come)")
            return
    log("matchmaking lock released")

    # now that we have found you an opponent, I suppose I should introduce you 
    # to them!
    log("sending my client a GAME message")
    player_client.sendmsg('GAME', opponent_name, player_name)
    log("waiting for OKAY response...")
    try:
        okaymsg = player_client.recvmsg()
    except Exception as e:
        # uh oh... something's wrong
        log("OKAY error:", type(e), e)
        log("exiting thread, bye (both clients)!")
        player_client.disconnect()
        opponent_client.disconnect()
        return
    log("successfully received OKAY response:", okaymsg)

    # let's initialise a logfile so that we don't forget what happen during this 
    # glorious game between these here two players
    log("creating a new logfile just for the game")
    gamelog = new_gamelog(f"{opponent_name}_vs_{player_name}")

    # finally, after all of that, we are ready...
    # I am honoured to have been the one to take you both this far.
    # without further ado...
    log("let the game begin!")
    try:
        play(opponent_client, player_client, gamelog)
    except Exception as e:
        # something has gone wrong...?
        log("game playing error:", type(e), e)
    
    player_client.disconnect()
    opponent_client.disconnect()
    gamelog.close()

    # what a joyous game that was. thank you both!
    log("end of thread, bye!")
    return


# PLAYING A GAME

def play(white_client, black_client, gamelog):
    # initialise the game
    game = Game()

    # initialise the players
    white = NetPlayer(white_client, 'white')
    black = NetPlayer(black_client, 'black')

    # now, play the game!
    player, opponent = white, black # white has first move
    # print(game) # we don't want to print out the whole board, actually!
    while game.playing():
        turns = game.turns
        action = player.action(turns)
        log(action, logfile=gamelog)
        try:
            game.update(action)
        except InvalidActionException as e:
            # if one of the players makes an invalid action,
            # print the error message
            log(f"invalid action ({game.loser}):", e, logfile=gamelog)
            white.invalid_action(game.loser, str(e))
            black.invalid_action(game.loser, str(e))
            break
        # print(game) # we don't want to print out the whole board, actually!
        opponent.update(action)
        # other player's turn!
        player, opponent = opponent, player

    if game.loser is None:
        log(f'winner: {game.winner}!', logfile=gamelog)
        white.game_over(game.winner)
        black.game_over(game.winner)

    # done!

# --------------------------------------------------------------------------- #

# HELPER CLASSES AND FUNCTIONS

class MatchmakingPool:
    def __init__(self):
        self.lock = threading.Lock() # should be no need for an rlock
        self.pool = {}
    def deposit(self, matching_key, data):
        if matching_key not in self.pool:
            self.pool[matching_key] = deque()
        self.pool[matching_key].append(data)
    def dequeue(self, matching_key):
        if matching_key not in self.pool:
            raise KeyError(f"no waiting data with key {matching_key!r}")
        data = self.pool[matching_key].popleft()
        if len(self.pool[matching_key]) == 0:
            del self.pool[matching_key]
        return data
    def has_waiting(self, matching_key):
        return matching_key in self.pool


class NetPlayer:
    def __init__(self, client, colour):
        self.player_str = f"({colour} player)"
        self.client = client

        log(self.player_str, 'sending INIT')
        self.client.sendmsg('INIT', colour)
        
        log(self.player_str, 'waiting for OKAY')
        okaymsg = self.client.recvmsg()
        log(self.player_str, 'received OKAY:', okaymsg)

    def action(self, turns):
        log(self.player_str, 'sending TURN')
        self.client.sendmsg('TURN', turns)

        log(self.player_str, 'waiting for ACTN')
        actnmsg = self.client.recvmsg()
        log(self.player_str, 'received ACTN:', actnmsg)

        if actnmsg['type'] == 'pass':
            return None
        elif actnmsg['type'] == 'place':
            return (actnmsg['x'], actnmsg['y'])
        elif actnmsg['type'] == 'move':
            return ((actnmsg['xa'], actnmsg['ya']),
                    (actnmsg['xb'], actnmsg['yb']))

    def update(self, action):
        log(self.player_str, 'sending UPD8')
        actiontype, actionargs = format_action(action)
        self.client.sendmsg('UPD8', actiontype, *actionargs)

        log(self.player_str, 'waiting for OKAY')
        okaymsg = self.client.recvmsg()
        log(self.player_str, 'received OKAY:', okaymsg)

    def invalid_action(self, loser, reason):
        log(self.player_str, 'sending ERRO')
        self.client.sendmsg('ERRO', loser, reason)

    def game_over(self, winner):
        log(self.player_str, 'sending OVER')
        self.client.sendmsg('OVER', winner)

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

# LOGGING FUNCTIONALITY

# setup log directory and filename

import os
import datetime

LOGFILEDIRNAME  = "logs"
LOGFILEBASENAME = f"log_{datetime.datetime.now()}.txt"

os.makedirs(LOGFILEDIRNAME, exist_ok=True)
LOGFILEPATH = os.path.join(LOGFILEDIRNAME, LOGFILEBASENAME)
LOGFILE = open(LOGFILEPATH, 'w')

# function for logging to the default logfile or a custom logfile

def log(*args, logfile=LOGFILE, **kwargs):
    line = f"[{datetime.datetime.now()} {threading.current_thread().name}]"
    print(line, '-', *args, **kwargs, file=logfile)
    logfile.flush()
    # if this is to the main log, tee to stdout too
    if logfile == LOGFILE:
        print(line, '-', *args, **kwargs) # file=sys.stdout)

# and game logs go into a separate file/folder:
GAMELOGFILEDIRNAME = os.path.join(LOGFILEDIRNAME, "games")
os.makedirs(GAMELOGFILEDIRNAME, exist_ok=True)

# function for starting a logfile for a new game

def new_gamelog(name):
    gamelogfilebasename = f"game_{datetime.datetime.now()}_{name}.txt"
    gamelogfilepath = os.path.join(GAMELOGFILEDIRNAME, gamelogfilebasename)
    gamelogfile = open(gamelogfilepath, 'w')
    log(",~* new logfile started *~'",       logfile=gamelogfile)
    log(f"see `{LOGFILEPATH}` for full log", logfile=gamelogfile)
    log("let the game begin!",               logfile=gamelogfile)
    return gamelogfile

# --------------------------------------------------------------------------- #

if __name__ == '__main__':
    main()