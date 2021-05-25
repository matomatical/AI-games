"""
Provide a command-line argument parsing function using argparse
(resulting in the following help message):

-----------------------------------------------------------------------------
usage: battleground [-h] [-V] [-H HOST] [-P PORT] [-D | -v [{0,1,2,3}]]
                    [-l [LOGFILE]] [-c | -C] [-u | -a]
                    player name [channel]

play against your classmates on the online battleground!

player package/class specifications (positional arguments):
  player                location of your Player class (e.g. package name)
  name                  identify your player on the battleground server
                        (e.g. team name or player name)
  channel               restrict matchmaking to players specifying the same
                        channel (optional; leave blank to play against
                        anyone)

optional arguments:
  -h, --help            show this message
  -V, --version         show program's version number and exit
  -H HOST, --host HOST  address of server (leave blank for default)
  -P PORT, --port PORT  port to contact server on (leave blank for default)
  -D, --debug           switch to printing the debug board (with
                        coordinates) (equivalent to -v or -v3)
  -v [{0,1,2,3}], --verbosity [{0,1,2,3}]
                        control the level of output (not including output
                        from player). 0: no output except result; 1:
                        commentary, but no board display; 2: (default)
                        commentary and board display; 3: (equivalent to -D)
                        larger board showing coordinates.
  -l [LOGFILE], --logfile [LOGFILE]
                        if you supply this flag the client will create a log
                        of all game actions in a text file named LOGFILE
                        (default: battle.log)
  -c, --colour          force colour display using ANSI control sequences
                        (default behaviour is automatic based on system).
  -C, --colourless      force NO colour display (see -c).
  -u, --unicode         force pretty display using unicode characters
                        (default behaviour is automatic based on system).
  -a, --ascii           force basic display using only ASCII characters (see
                        -u).
-----------------------------------------------------------------------------
"""

import sys
import argparse
from referee.game import GAME_NAME
from referee.options import PackageSpecAction
from battleground.protocol import DEFAULT_SERVER_PORT

# Program information:
PROGRAM = "battleground"
VERSION = "2021.1.0"
DESCRIP = "play against your classmates on the online battleground!"

WELCOME = f"""***************************************************************
welcome to {GAME_NAME} client version {VERSION}.

{DESCRIP}

run `python -m battleground -h` for additional usage information.
***************************************************************"""

# default values (to use if flag is not provided)
# and missing values (to use if flag is provided, but with no value)

PORT_DEFAULT = DEFAULT_SERVER_PORT
HOST_DEFAULT = "ai.far.in.net"

CHANNEL_DEFAULT = ""

VERBOSITY_LEVELS = 4
VERBOSITY_DEFAULT = 2  # normal level, normal board
VERBOSITY_NOVALUE = 3  # highest level, debug board

LOGFILE_DEFAULT = None
LOGFILE_NOVALUE = "battle.log"


def get_options():
    """
    Parse and return command-line arguments.
    """

    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=DESCRIP,
        add_help=False,  # <-- we will add it back to the optional group.
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # positional arguments used for player package specifications:
    positionals = parser.add_argument_group(
        title="player package/class specifications (positional arguments)"
    )
    positionals.add_argument(
        "player_loc",
        metavar="player",
        help="location of your Player class (e.g. package name)",
        action=PackageSpecAction,
    )

    positionals.add_argument(
        "name",
        help="identify your player on the battleground server "
        "(e.g. team name or player name)",
    )
    positionals.add_argument(
        "channel",
        default=CHANNEL_DEFAULT,
        nargs="?",
        help="restrict matchmaking to players specifying the same "
        "channel (optional; leave blank to play against anyone)",
    )

    # optional arguments used for configuration:
    optionals = parser.add_argument_group(title="optional arguments")
    optionals.add_argument(
        "-h",
        "--help",
        action="help",
        help="show this message",
    )
    optionals.add_argument(
        "-V",
        "--version",
        action="version",
        version=VERSION,
    )

    optionals.add_argument(
        "-H",
        "--host",
        type=str,
        default=HOST_DEFAULT,
        help="address of server (leave blank for default)",
    )
    optionals.add_argument(
        "-P",
        "--port",
        type=int,
        default=PORT_DEFAULT,
        help="port to contact server on (leave blank for default)",
    )

    verbosity_group = optionals.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "-D",
        "--debug",
        action="store_true",
        help="switch to printing the debug board (with coordinates) "
        "(equivalent to -v or -v3)",
    )
    verbosity_group.add_argument(
        "-v",
        "--verbosity",
        type=int,
        choices=range(0, VERBOSITY_LEVELS),
        nargs="?",
        default=VERBOSITY_DEFAULT,
        const=VERBOSITY_NOVALUE,
        help="control the level of output (not including output from "
        "player). 0: no output except result; 1: commentary, but no "
        "board display; 2: (default) commentary and board display; "
        "3: (equivalent to -D) larger board showing coordinates.",
    )

    optionals.add_argument(
        "-l",
        "--logfile",
        metavar="LOGFILE",
        type=str,
        nargs="?",
        default=LOGFILE_DEFAULT,
        const=LOGFILE_NOVALUE,
        help="if you supply this flag the client will create a log of "
        "all game actions in a text file named %(metavar)s "
        "(default: %(const)s)",
    )

    colour_group = optionals.add_mutually_exclusive_group()
    colour_group.add_argument(
        "-c",
        "--colour",
        action="store_true",
        help="force colour display using ANSI control sequences "
        "(default behaviour is automatic based on system).",
    )
    colour_group.add_argument(
        "-C",
        "--colourless",
        action="store_true",
        help="force NO colour display (see -c).",
    )

    unicode_group = optionals.add_mutually_exclusive_group()
    unicode_group.add_argument(
        "-u",
        "--unicode",
        action="store_true",
        help="force pretty display using unicode characters "
        "(default behaviour is automatic based on system).",
    )
    unicode_group.add_argument(
        "-a",
        "--ascii",
        action="store_true",
        help="force basic display using only ASCII characters (see -u).",
    )

    args = parser.parse_args()

    # post-processing to combine mutually exclusive options
    # debug => verbosity 3
    if args.debug:
        args.verbosity = 3
    del args.debug
    # colour, colourless => force colour(less), else auto-detect
    if args.colour:
        args.use_colour = True
    elif args.colourless:
        args.use_colour = False
    else:
        args.use_colour = sys.stdout.isatty() and sys.platform != "win32"
    del args.colour, args.colourless
    # unicode, ascii => force display mode unicode or ascii, else auto-detect
    if args.unicode:
        args.use_unicode = True
    elif args.ascii:
        args.use_unicode = False
    else:
        args.use_unicode = False  # was: (sys.platform != "win32")
    del args.unicode, args.ascii

    # disable delay, space limiting, time limiting for networked games:
    args.delay = 0
    args.time = 0
    args.space = 0

    # done!
    if args.verbosity > 0:
        print(WELCOME)
    return args
