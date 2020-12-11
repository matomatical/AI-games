"""
Multi-threaded match-making Chexers game server
"""

import time
import random
import datetime
import threading
from collections import defaultdict

from referee.log import StarLog
from referee.game import Chexers, IllegalActionException

from battleground.protocol import DisconnectException, ProtocolException
from battleground.protocol import Connection, MessageType as M

HOST = ""    # allow all incoming connections
PORT = 6666  # on this particular port

def main():
    out = StarLog(level=1, time=datetime.datetime.now, star="* Thread-0")
    out.comment("initialising server")

    # set up a shared matchmaking pool
    pool = MatchmakingPool()

    # listen for connections incoming on PORT:
    connections = Connection.iter_listen(HOST, PORT)
    out.comment(f"listening on port {PORT}...")
    for connection, address in connections:
        # repeatedly accept a new connection, and hand off to a new thread
        out.comment("new client connected: ", address)
        
        out.comment("starting a new thread to handle this client...")
        handler = threading.Thread(target=servant, args=(connection, pool))
        handler.daemon = True # so that this thread exits when main exits
        handler.start()

def servant(connection, pool):
    thread_name = f"* {threading.current_thread().name}"
    out = StarLog(level=1, time=datetime.datetime.now, star=thread_name)
    out.comment("hello, world!")

    # At your service, client! let's begin the protocol
    # First thing's first, could you send me a PLAY request containing your 
    # name and matchmaking channel?
    out.section("begin communication with player")
    out.comment("waiting for PLAY request...")
    try:
        playmsg = connection.recv(M.PLAY)
        out.comment("successfully received PLAY request:", playmsg)    
        out.comment("sending OKAY back.")
        connection.send(M.OKAY)
    except DisconnectException:
        out.comment("client disconnected. bye!")
        connection.disconnect()
        return
    except ProtocolException as e:
        out.comment("protocol error! that was unexpected...? bye!")
        connection.disconnect()
        return

    # Now that you're officially a player, let's wrap you up in an object so
    # that we won't forget your name.
    player1 = NetPlayer(connection, playmsg['name'])
    
    # And we'll need to note that channel for matchmaking purposes!
    channel = playmsg['channel']
    

    # Okay then. Now, if it pleases you just to wait one moment, I'll look for
    # some suitable opponents for you to play with...
    out.section("looking for opponents...")
    try:
        player2, player3 = pool.match(channel, player1, out)
        out.comment("opponents found!")
    except NotEnoughPlayers:
        # I'm afraid this is as far as I can take you, good sir/madam.
        # If you wait here for just a short time, I'm sure another thread
        # will come by and pick you up quite soon.
        # It has been my eternal pleasure. Farewell~    Your humble servant.
        out.comment("leaving in pool for another thread. bye~!")
        return
    
    # Splendid! Between the three of you, we have enough players for a game!
    # Who will take the first turn? Let us cast the proverbial three-sided die:
    out.comment("randomly assigning colours to players...")
    colours = [ 'red',   'green', 'blue'  ]
    players = [ player1, player2, player3 ]
    random.shuffle(players)
    cols_players = list(zip(colours, players))

    # Then, shall we introduce you to one another?
    col_name_map = {colour: player.name for colour, player in cols_players}
    for colour, player in cols_players:
        player.game(col_name_map, out)
    

    # What name shall we give to this glorious playing?
    player_names = '_x_'.join(p.name for p in players)
    start_time = time.asctime().replace(' ', '-')
    game_name = f"logs/game_{player_names}_at_{start_time}.txt"

    # Without further ado, let us begin!
    try:
        result = play(cols_players, game_name, out)

        # What a delightful result! I hope that was an enjoyable game
        # for all of you. Let's share the final result.
        out.section("game over!")
        out.comment(result)
        out.comment("sending out result...")
        for player in players:
            player.game_over(result=result)
    except IllegalActionException:
        # Ah! The game has ended early. We had better
        # make sure everyone is on the same page:
        out.section("game error")
        out.comment("game error: invalid action")
        for player in players:
            player.game_over(result="game error: invalid action")
    except DisconnectException:
        # In the unfortunate event of a disconnection, we had better 
        # make sure everyone is on the same page:
        out.section("connection error")
        out.comment("a client disconnected")
        for player in players:
            try:
                player.error(reason="opponent disconnected")
            except BrokenPipeError:
                # this connection must have been the one that reset; skip it
                continue
    except ProtocolException as e:
        out.section("protocol error!")
        out.comment(e)
        out.comment("a client did something unexpected")
        for player in players:
            player.error(reason="opponent broke protocol")
    
    # One way or another, that's the end of this meeting. Until next time, my
    # good friends! It has been my deepest pleasure~
    out.section("disconnection")
    out.comment("disconnecting players...")
    for player in players:
        player.disconnect()
    out.comment("end of thread. bye~")       


def play(colours_players, logfilename, out):
    out.section("game start")
    game = Chexers(logfilename=logfilename)

    # Let's get all the players ready!
    for colour, player in colours_players:
        player.init(colour)
    _colours, players = zip(*colours_players)
    
    # Repeat the following until the game ends
    # (starting with Red as the current player, then alternating):
    curr_player, next_player, prev_player = players
    while not game.over():
        out.section(f"{curr_player.player_str}'s turn")

        # Ask the current player for their next action (calling their .action() 
        # method).
        action = curr_player.action()
        
        # Validate this action (or pass) and apply it to the game if it is 
        # allowed. Display the resulting game state.
        game.update(curr_player.colour, action)

        # Notify all three players (including the current player) of the action
        # (or pass) (using their .update() methods).
        for player in players:
            player.update(curr_player.colour, action)

        # Next player's turn!
        curr_player,next_player,prev_player=next_player,prev_player,curr_player
    
    # After that loop, the game has ended!
    return game.end()


class NetPlayer:
    def __init__(self, connection, name):
        self.connection = connection
        self.name       = name
        self.player_str = f"{self.name} (not yet initialised)"

    def ping(self, timeout=None):
        self.connection.send(M.OKAY)
        self.connection.recv(M.OKAY, timeout=timeout)

    def game(self, colour_name_map, out):
        self.out = out
        self.out.comment(self.player_str, 'sending GAME')
        self.connection.send(M.GAME, **colour_name_map)    

    def init(self, colour):
        self.colour = colour
        self.player_str = f"{self.name} ({colour})"
        self.out.comment(self.player_str, 'sending INIT')
        self.connection.send(M.INIT, colour=colour)
        self.connection.recv(M.OKAY)

    def action(self):
        self.out.comment(self.player_str, 'sending TURN')
        self.connection.send(M.TURN)
        self.out.comment(self.player_str, 'waiting for ACTN')
        actnmsg = self.connection.recv(M.ACTN)
        self.out.comment(self.player_str, 'received ACTN:', actnmsg)
        return actnmsg['action']

    def update(self, colour, action):
        self.out.comment(self.player_str, 'sending UPD8')
        self.connection.send(M.UPD8, colour=colour, action=action)
        self.out.comment(self.player_str, 'waiting for OKAY')
        self.connection.recv(M.OKAY)

    def game_over(self, result):
        self.out.comment(self.player_str, 'sending OVER')
        self.connection.send(M.OVER, result=result)

    def error(self, reason):
        self.out.comment(self.player_str, 'sending ERRO')
        self.connection.send(M.ERRO, reason=reason)

    def disconnect(self):
        self.out.comment(self.player_str, 'disconnecting')
        self.connection.disconnect()


class MatchmakingPool:
    def __init__(self):
        self.lock = threading.RLock()
        self.waiting = defaultdict(list)

    def match(self, channel, player1, out):
        with self.lock:
            out.comment("matchmaking pool before filter:", self.waiting)
            # clean out any players who have since disconnected
            waiting = self.filter(channel, out)
            
            # okay, were there enough players waiting to play a game?
            if len(waiting) < 2:
                # no; deposit THIS player in the pool, and alert the caller
                waiting.append(player1)
                out.comment("not enough players!")
                out.comment("pool after filter:", self.waiting)
                raise NotEnoughPlayers()
            else:
                # yes! extract two players and return them!
                player2 = waiting.pop()
                player3 = waiting.pop()
                # NOW clear away unused channels
                if len(waiting) == 0:
                    del self.waiting[channel]
                out.comment("match found!")
                out.comment("pool after filter:", self.waiting)
                return player2, player3

    def filter(self, channel, out=None):
        with self.lock:
            still_waiting = []
            for player in self.waiting[channel]:
                try:
                    player.ping(timeout=10)
                    # conact! they're still online! re-add them to the pool:
                    still_waiting.append(player)
                except (OSError,
                        BrokenPipeError,     # the connection has gone stale?
                        DisconnectException, # the client closed the connection
                        ProtocolException    # the client... did what?
                        ) as e:
                    # in any case, close this connection and don't keep this 
                    # client in the pool.
                    if out is not None:
                        out.comment("ditching client", player, "due to", 
                                    e.__class__.__name__, e)
                    player.connection.disconnect()
            self.waiting[channel] = still_waiting
            return still_waiting


class NotEnoughPlayers(Exception):
    """For when there are not enough players waiting in a particular channel"""


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nbye!")