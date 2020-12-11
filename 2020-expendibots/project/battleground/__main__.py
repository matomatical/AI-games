"""
Client program to instantiate a player class and 
conduct a game of Chexers through the online battleground
"""

from referee.log import StarLog
from referee.game import Game
from referee.player import PlayerWrapper, set_space_line

from battleground.options import get_options
from battleground.protocol import Connection as Server, ConnectingException 
from battleground.protocol import MessageType as M, ProtocolException
from battleground.protocol import DisconnectException


def main():
    # Parse command-line options into a namespace for use throughout this
    # program
    options = get_options()

    # Create a star-log for controlling the format of output from within this
    # program
    out = StarLog(level=options.verbosity, ansi=options.use_colour)
    out.comment("all messages printed by the client after this begin with a *")
    out.comment("(any other lines of output must be from your Player class).")
    out.comment()
    
    try:
        # Import player classes
        player = PlayerWrapper("your player", options.player_loc,
                logfn=out.comment)
    
        # Even though we're not limiting space, the display
        # may still be useful for some users
        set_space_line()

        # Play the game, catching any errors and displaying them to the 
        # user:
        result = connect_and_play(player,
            options.name,
            options.channel,
            options.host,
            options.port,
            logfilename=options.logfile,
            out_function=out.comment,
            print_state=(options.verbosity>1),
            use_debugboard=(options.verbosity>2),
            use_colour=options.use_colour,
            use_unicode=options.use_unicode)
        
        out.comment("game over!", depth=-1)
        out.print(result)

    except KeyboardInterrupt:
        print() # (end the line)
        out.comment("bye!")
    except ConnectingException as e:
        out.print("error connecting to server")
        out.comment(e)
    except DisconnectException as e:
        out.print("connection lost", depth=-1)
        out.comment(e)
    except ProtocolException as e:
        out.print("protocol error!", depth=-1)
        out.comment(e)
    except ServerEncounteredError as e:
        out.print("server encountered error!", depth=-1)
        out.comment(e)
    # If it's another kind of error then it might be coming from the player
    # itself? Then, a traceback will be more helpful.


def connect_and_play(player, name, channel, host, port,
        logfilename=None, out_function=None, print_state=True,
        use_debugboard=False, use_colour=False, use_unicode=False):
    """
    Connect to and coordinate a game with a server, return a string describing
    the result.
    """
    # Configure behaviour of this function depending on parameters:
    out = out_function if out_function else (lambda *_, **__: None) # no-op
    if print_state:
        def display_state(players_str, game):
            out("displaying game info:")
            out(players_str, depth=1)
            out(game, depth=1)
    else:
        def display_state(players, game): pass


    # Set up a connection with the server
    out("connecting to battleground", depth=-1)
    out("attempting to connect to the server...")
    server = Server.from_address(host, port)
    out("connection established!")
    
    # Wait for some matching players
    out("looking for a game", depth=-1)
    channel_str = f"channel '{channel}'" if channel else "open channel"
    out(f"submitting game request as '{name}' in {channel_str}...")
    server.send(M.PLAY, name=name, channel=channel)
    server.recv(M.OKAY)
    out("game request submitted.")
    out(f"waiting for opponents in {channel_str}...")
    out("(press ^C to stop waiting)")
    # (wait through some OKAY-OKAY msg exchanges until a GAME message comes---
    # the server is asking if we are still here waiting, or have disconnected)
    gamemsg = server.recv(M.OKAY|M.GAME)
    while gamemsg['mtype'] is not M.GAME:
        server.send(M.OKAY)
        gamemsg = server.recv(M.OKAY|M.GAME)
    # when we get a game message, it's time to play!
    out("setting up game", depth=-1, clear=True)
    out("opponents found!")
    out("white player:", gamemsg['white'])
    out("black player:", gamemsg['black'])

    # Initialise the player
    out("initialising player", depth=-1)
    out("waiting for colour assignment...")
    initmsg = server.recv(M.INIT)
    out("playing as", initmsg['colour'], depth=1)
    out("initialising your player class...")
    player.init(initmsg['colour'])
    out("ready to play!")
    server.send(M.OKAY)
    
    # Set up a new game and display the initial state and players
    out("game start", depth=-1)
    players_str = format_players_str(gamemsg, player.colour)
    game = Game(logfilename=logfilename, debugboard=use_debugboard,
                colourboard=use_colour, unicodeboard=use_unicode)
    display_state(players_str, game)

    # Now wait for messages from the sever and respond accordingly
    while True:
        msg = server.recv(M.TURN|M.UPD8|M.OVER|M.ERRO)
        if msg['mtype'] is M.TURN:
            # it's our turn!
            out("your turn!", depth=-1, clear=True)
            display_state(players_str, game)

            # decide on action and submit it to server
            action = player.action()
            server.send(M.ACTN, action=action)

        elif msg['mtype'] is M.UPD8:
            # someone made a move!
            colour = msg['colour']
            action = msg['action']
            # update our local state,
            out("receiving update", depth=-1, clear=True)
            game.update(colour, action)
            display_state(players_str, game)
            player.update(colour, action)
            # then notify server we are ready to continue:
            server.send(M.OKAY)
        
        elif msg['mtype'] is M.OVER:
            # the game ended!
            return msg['result']
        
        elif msg['mtype'] is M.ERRO:
            # seems like the server encountered an error, but not
            # with our connection
            raise ServerEncounteredError(msg['reason'])


def format_players_str(gamemsg, your_colour):
    players = []
    for colour, name in gamemsg.items():
        if colour == 'mtype':
            continue # not a colour!
        if colour == your_colour:
            prefix = "you -> " + colour
        else:
            prefix = colour
        players.append(f"{prefix:>12} player: {name}")
    return '\n'.join(players)


class ServerEncounteredError(Exception):
    """
    The server encountered and is duly informing us of some kind of error,
    e.g. an invalid action, opponent disconnection, or protocol violation.
    """

if __name__ == '__main__':
    main()
