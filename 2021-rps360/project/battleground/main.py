"""
Client program to instantiate a player class and 
conduct a game of Chexers through the online battleground
"""
import logging

from referee.log import config, print, _print, comment
from referee.game import Game, _RENDER, COLOURS, _FORMAT_ACTION
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
    out = config(level=options.verbosity, ansi=options.use_colour)
    comment("all messages printed by the client after this begin with a *")
    comment("(any other lines of output must be from your Player class).")
    comment()

    try:
        # Import player classes
        player = PlayerWrapper(
            "your player",
            options.player_loc,
        )

        # Even though we're not limiting space, the display
        # may still be useful for some users
        set_space_line()

        # Play the game, catching any errors and displaying them to the
        # user:
        result = connect_and_play(
            player=player,
            name=options.name,
            channel=options.channel,
            host=options.host,
            port=options.port,
            log_filename=options.logfile,
            print_state=(options.verbosity > 1),
            use_debugboard=(options.verbosity > 2),
            use_colour=options.use_colour,
            use_unicode=options.use_unicode,
        )
        comment("game over!", depth=-1)
        print(result)
    except KeyboardInterrupt:
        _print()  # (end the line)
        comment("bye!")
    except ConnectingException as e:
        print("error connecting to server")
        comment(e)
    except DisconnectException as e:
        print("connection lost", depth=-1)
        comment(e)
    except ProtocolException as e:
        print("protocol error!", depth=-1)
        comment(e)
    except ServerEncounteredError as e:
        print("server encountered error!", depth=-1)
        comment(e)
    # If it's another kind of error then it might be coming from the player
    # itself? Then, a traceback will be more helpful.


def connect_and_play(
    player,
    name,
    channel,
    host,
    port,
    log_filename=None,
    out_function=None,
    print_state=True,
    use_debugboard=False,
    use_colour=False,
    use_unicode=False,
):
    """
    Connect to and coordinate a game with a server, return a string describing
    the result.

    Parameters:
    * player         -- Your player's wrapped object (supporting 'init',
                        'update' and 'action' methods).
    * name           -- Your player's name on the server
    * channel        -- The matchmaking channel string
    * host           -- The server address
    * port           -- The server port
    * log_filename   -- If not None, log all game actions to this path.
    * print_state    -- If True, print a picture of the board after each
                        update.
    * use_debugboard -- If True, use a larger board during updates (if
                        print_state is also True).
    * use_colour     -- Use ANSI colour codes for output.
    * use_unicode    -- Use unicode symbols for output.
    """
    # Configure behaviour of this function depending on parameters:
    if print_state:

        def display_state(players_str, game):
            comment("displaying game info:")
            comment(
                _RENDER(
                    game,
                    message=players_str,
                    use_debugboard=use_debugboard,
                    use_colour=use_colour,
                    use_unicode=use_unicode,
                ),
                depth=1,
            )

    else:

        def display_state(players_str, game):
            pass

    # Set up a connection with the server
    comment("connecting to battleground", depth=-1)
    comment("attempting to connect to the server...")
    server = Server.from_address(host, port)
    comment("connection established!")

    # Wait for some matching players
    comment("looking for a game", depth=-1)
    channel_str = f"channel '{channel}'" if channel else "open channel"
    comment(f"submitting game request as '{name}' in {channel_str}...")
    server.send(M.PLAY, name=name, channel=channel)
    server.recv(M.OKAY)
    comment("game request submitted.")
    comment(f"waiting for opponents in {channel_str}...")
    comment("(press ^C to stop waiting)")
    # (wait through some OKAY-OKAY msg exchanges until a GAME message comes---
    # the server is asking if we are still here waiting, or have disconnected)
    gamemsg = server.recv(M.OKAY | M.GAME)
    while gamemsg["mtype"] is not M.GAME:
        server.send(M.OKAY)
        gamemsg = server.recv(M.OKAY | M.GAME)
    # when we get a game message, it's time to play!
    comment("setting up game", depth=-1, clear=True)
    comment("opponents found!")
    for colour in COLOURS:
        comment(f"{colour} player:", gamemsg[colour])

    # Initialise the player
    comment("initialising player", depth=-1)
    comment("waiting for colour assignment...")
    initmsg = server.recv(M.INIT)
    comment("playing as", initmsg["colour"], depth=1)
    comment("initialising your player class...")
    player.init(initmsg["colour"])
    comment("ready to play!")
    server.send(M.OKAY)

    # Set up a new game and display the initial state and players
    comment("game start", depth=-1)
    players_str = format_players_str(gamemsg, player.colour)
    game = Game(log_filename)
    display_state(players_str, game)

    # Now wait for messages from the sever and respond accordingly
    while True:
        msg = server.recv(M.TURN | M.UPD8 | M.OVER | M.ERRO)
        if msg["mtype"] is M.TURN:
            # TODO: For simultaneous play, there's no need to display the
            # state again at the start of the turn...
            # comment("your turn!", depth=-1, clear=True)
            # display_state(players_str, game)
            # decide on action and submit it to server
            action = player.action()
            server.send(M.ACTN, action=action)

        elif msg["mtype"] is M.UPD8:
            player_action = msg["player_action"]
            opponent_action = msg["opponent_action"]
            comment("receiving update", depth=-1, clear=True)
            if player.colour == "upper":
                game.update(
                    upper_action=player_action,
                    lower_action=opponent_action,
                )
            else:
                game.update(
                    upper_action=opponent_action,
                    lower_action=player_action,
                )
            display_state(players_str, game)
            player.update(
                player_action=player_action,
                opponent_action=opponent_action,
            )
            # then notify server we are ready to continue:
            server.send(M.OKAY)

        elif msg["mtype"] is M.OVER:
            # the game ended!
            return msg["result"]

        elif msg["mtype"] is M.ERRO:
            # seems like the server encountered an error, but not
            # with our connection
            raise ServerEncounteredError(msg["reason"])


def format_players_str(gamemsg, your_colour):
    players = []
    for colour, name in gamemsg.items():
        if colour == "mtype":
            continue  # not a colour!
        if colour == your_colour:
            prefix = "you -> " + colour
        else:
            prefix = colour
        players.append(f"{prefix:>12} player: {name}")
    return "\n".join(players)


class ServerEncounteredError(Exception):
    """
    The server encountered and is duly informing us of some kind of error,
    e.g. an invalid action, opponent disconnection, or protocol violation.
    """
