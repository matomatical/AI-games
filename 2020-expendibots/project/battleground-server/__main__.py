"""
Multi-threaded match-making game server
"""

import os
import random
from datetime import datetime
import threading
from collections import defaultdict

from referee.log import StarLog
from referee.game import play, IllegalActionException, COLOURS, NUM_PLAYERS
from benchmark import RandomPlayer, GreedySpreadPlayer
from battleground.protocol import DisconnectException, ProtocolException
from battleground.protocol import Connection, MessageType as M
from battleground.protocol import DEFAULT_SERVER_PORT

# The following channels are reserved, and choosing them results in playing
# a game with server-controlled players:
SPECIAL_CHANNELS = {
    'random': (lambda p: [ServerPlayer(RandomPlayer, 'random_bot'), p]),
    'greedy': (lambda p: [ServerPlayer(GreedySpreadPlayer, 'greedy_bot'), p]),
}

# Print at a higher level of verbosity, including some debugging information
DEBUG = False # The matchmaking system seems to be working well from 2019.


# # # #
# Main thread: listen for incoming connections.
#
#

def main():
    out = StarLog(level=1+DEBUG, timefn=lambda: f'Thread-0 {datetime.now()}')
    out.comment("initialising server", depth=-1)

    # set up a shared matchmaking pool
    pool = MatchmakingPool(num_players=NUM_PLAYERS,
                           special_channels=SPECIAL_CHANNELS)

    # listen for connections incoming on PORT:
    try:
        # Host of "" allows all incoming connections on the chosen port
        connections = Connection.iter_listen(host="", port=DEFAULT_SERVER_PORT)
        out.comment(f"listening on port {DEFAULT_SERVER_PORT}...")
        for connection, address in connections:
            # repeatedly accept a new connection, and hand off to a new thread
            out.comment("new client connected: ", address)
            
            out.comment("starting a new thread to handle this client...")
            handler = threading.Thread(target=servant, args=(connection, pool))
            handler.daemon = True # so that this thread exits when main exits
            handler.start()
    except KeyboardInterrupt:
        print() # end line
        out.comment("bye!")

# # # #
# Worker thread: Coordinate the matchmaking process and, if the client is the
#  player that allows a game to begin, coordinate that game to conclusion.
#

def servant(connection, pool):
    # (Each thread gets own print function which includes its thread number)
    timefn = lambda: f'{threading.current_thread().name} {datetime.now()}'
    out = StarLog(level=1+DEBUG, timefn=timefn)
    out.comment("hello, world!")

    # # #
    # Initiate connection
    #

    # At your service, client! Let us begin the protocol
    # First, could you kindly send me a PLAY request containing your
    # name and matchmaking channel?
    out.comment("begin communication with player", depth=-1)
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
    new_player = NetworkPlayer(connection, playmsg['name'])

    # And we'll need to note that channel for matchmaking purposes!
    channel = playmsg['channel']
    


    # # #
    # Conduct matchmaking
    #

    # Okay then. Now, if it pleases you just to wait one moment, I'll look for
    # some suitable opponents for you to play with...
    out.comment("looking for opponents...", depth=-1)
    try:
        players = pool.match(channel, new_player, out)
        out.comment("opponents found!")
    except NotEnoughPlayers:
        # I'm afraid this is as far as I can take you, good sir/madam.
        # If you wait here for just a short time, I'm sure another thread
        # will come by and pick you up quite soon.
        # It has been my eternal pleasure. Farewell~    Your humble servant.
        out.comment("leaving in pool for another thread. bye~!")
        return
    
    # # #
    # Initialise all players, prepare for game
    # 

    # Splendid! Between the few of you, we have enough players for a game!
    # Who will take the first turn? Let us cast the proverbial die:
    out.comment("randomly assigning colours to players...")
    random.shuffle(players)
    cols_players = list(zip(COLOURS, players))

    # Then, shall we introduce you to one another?
    col_name_map = {colour: player.name for colour, player in cols_players}
    for colour, player in cols_players:
        player.game(col_name_map, out.comment)
    
    # What name shall we give to this glorious playing?
    player_names = '_and_'.join(p.name for p in players)
    timestamp = str(datetime.now())[:19].replace(' ', '_').replace(':', '-')
    game_name = f"logs/game_at_{timestamp}_with_{player_names}.txt"
    # Attempt to make sure there is a 'logs' folder ready for the game log
    try: os.mkdir('logs')
    except: pass

    # # #
    # Play game, handle result
    #

    # Without further ado, let us begin!
    try:
        result = play(players,
            logfilename=game_name,
            out_function=out.comment,
            print_state=False)

        # What a delightful result! I hope that was an enjoyable game
        # for all of you. Let's share the final result.
        out.comment("game over!", depth=-1)
        out.comment(result)
        out.comment("sending out result...")
        for player in players:
            player.game_over(result=result)
    except IllegalActionException:
        # Ah! The game has ended early. We had better
        # make sure everyone is on the same page:
        out.comment("game error", depth=-1)
        out.comment("game error: invalid action")
        for player in players:
            player.game_over(result="game error: invalid action")
    except DisconnectException:
        # In the unfortunate event of a disconnection, we had better 
        # make sure everyone is on the same page:
        out.comment("connection error", depth=-1)
        out.comment("a client disconnected")
        for player in players:
            try:
                player.error(reason="opponent disconnected")
            except BrokenPipeError:
                # this connection must have been the one that reset; skip it
                continue
    except ProtocolException as e:
        out.comment("protocol error!", depth=-1)
        out.comment(e)
        out.comment("a client did something unexpected")
        for player in players:
            player.error(reason="opponent broke protocol")
    
    # # #
    # Terminate all players
    # 

    # One way or another, that's the end of this meeting. Until next time, my
    # good friends! It has been my deepest pleasure~
    out.comment("disconnection", depth=-1)
    out.comment("disconnecting players...")
    for player in players:
        player.disconnect()
    out.comment("end of thread. bye~")       


# # #
# Player wrappers
# 

class NetworkPlayer:
    """A Player wrapper for network-controlled players"""
    def __init__(self, connection, name):
        self.connection = connection
        self.name       = name
        self.player_str = f"{self.name} (not yet initialised)"

    def ping(self, timeout=None):
        self.connection.send(M.OKAY)
        self.connection.recv(M.OKAY, timeout=timeout)

    def game(self, colour_name_map, log_function):
        self.log = log_function
        self.log(self.player_str, 'sending GAME')
        self.connection.send(M.GAME, **colour_name_map)    

    def init(self, colour):
        self.colour = colour
        self.player_str = f"{self.name} ({colour})"
        self.log(self.player_str, 'sending INIT')
        self.connection.send(M.INIT, colour=colour)
        self.connection.recv(M.OKAY)

    def action(self):
        self.log(self.player_str, 'sending TURN')
        self.connection.send(M.TURN)
        self.log(self.player_str, 'waiting for ACTN')
        actnmsg = self.connection.recv(M.ACTN)
        self.log(self.player_str, 'received ACTN:', actnmsg)
        return actnmsg['action']

    def update(self, colour, action):
        self.log(self.player_str, 'sending UPD8')
        self.connection.send(M.UPD8, colour=colour, action=action)
        self.log(self.player_str, 'waiting for OKAY')
        self.connection.recv(M.OKAY)

    def game_over(self, result):
        self.log(self.player_str, 'sending OVER')
        self.connection.send(M.OVER, result=result)

    def error(self, reason):
        self.log(self.player_str, 'sending ERRO')
        self.connection.send(M.ERRO, reason=reason)

    def disconnect(self):
        self.log(self.player_str, 'disconnecting')
        self.connection.disconnect()


class ServerPlayer:
    """A Player wrapper for locally-controlled players"""
    def __init__(self, Player, name):
        self.Player = Player
        self.name = name

    def game(self, _colour_name_map, log_function):
        self.log = log_function

    def init(self, colour):
        self.colour = colour
        self.player_str = f"{self.name} ({colour})"
        self.log(self.player_str, 'initialising', colour)
        self.player = self.Player(colour)

    def action(self):
        self.log(self.player_str, 'asking for action')
        action = self.player.action()
        self.log(self.player_str, 'got:', action)
        return action

    def update(self, colour, action):
        self.log(self.player_str, 'updating with', colour, action)
        self.player.update(colour, action)

    def game_over(self, result):
        pass

    def error(self, reason):
        pass

    def disconnect(self):
        pass


# # #
# Matchmaking code
# 

class MatchmakingPool:
    """
    A collection of per-channel waiting lists, with concurrent access control.
    Submit your player to a channel with the match method, and receive either
    a NotEnoughPlayers exception or a list of num_players previously deposited.
    
    Notes:
    * Thread safe (I think)
    * Does not automatically clear stale connections out of channel waiting
      lists until a new player is submitted to that channel. Therefore, an
      attack exists where a client can run up memory usage by repeatedly
      submitting players to obscure channels, and then disconnecting.
    """
    def __init__(self, num_players, special_channels):
        self._lock = threading.RLock()
        self._waiting = defaultdict(list)
        self.num_players = num_players
        self.special_channels = special_channels

    def match(self, channel, new_player, out):
        """
        Submit a 'new_player' (Player wrapper) to look for games on 'channel'.
        If there are already players waiting from previous match calls, or if
        'channel' is a special channel, then return a full list of players
        (including 'new_player').
        If there are not enough players yet, leave 'new_player' in the pool
        for a future match call and raise a NotEnoughPlayers exception.
        """
        # if it's a special channel, we don't need to wait for players,
        # the server can provide some:
        if channel in self.special_channels:
            return self.special_channels[channel](new_player)
        # otherwise, we do need to match-make as usual:
        with self._lock:
            out.debug("matchmaking pool before filter:", self._waiting)
            # clean out any players who have since disconnected
            channel_waiting = self._filter(channel, out)

            # deposit THIS new player in the queue too,
            channel_waiting.append(new_player)

            # okay, are there enough players waiting to play a game?
            if len(channel_waiting) < self.num_players:
                # no; alert the caller
                out.comment("not enough players!")
                out.debug("pool after filter:", self._waiting)
                raise NotEnoughPlayers()
            else:
                # yes! extract this queue from the waiting pool
                del self._waiting[channel]
                out.comment("match found!")
                out.debug("pool after filter:", self._waiting)
                # and return these players to the caller!
                return channel_waiting

    def _filter(self, channel, out=None):
        with self.lock:
            still_waiting = []
            for player in self._waiting[channel]:
                try:
                    player.ping(timeout=10)
                    # contact! they're still online! re-add them to the pool:
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
            self._waiting[channel] = still_waiting
            return still_waiting


class NotEnoughPlayers(Exception):
    """For when there are not enough players waiting in a particular channel"""



if __name__ == '__main__':
    main()
