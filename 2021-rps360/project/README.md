# RoPaSci 360 project code

## Contents

* `specification.pdf`, containing full details about the project
* `referee`, Python module acting as a driver for computerised games
* `player_template`, skeleton module for implementing a player
* `battleground.pdf`, instructions for using the online battleground client
* `battleground`, module implementing client for the online battleground
* `server`, module implementing match-making server for the same

See usage notes below, and also the
[project specification](specification.pdf) and
[battleground instructions](battleground.pdf).

> ### Warning
> 
> This code worked for the semester, but is not maintained. See the
> most-recent semester's code for a similar but more up-to-date
> implementation.

## RoPaSci 360 driver usage

Play a game of RoPaSci 360 between two Player classes.

Invoke with:

```
python3 -m referee [<options>] <upper player> <lower player>
```

Full usage information:

```
usage: referee [-h] [-V] [-d [delay]] [-s [space_limit]] [-t [time_limit]]
               [-D | -v [{0,1,2,3}]] [-l [LOGFILE]] [-c | -C] [-u | -a]
               upper lower

conduct a game of RoPaSci 360 between 2 Player classes.

player package/class specifications (positional args):

  The first 2 arguments are 'package specifications'. These specify which
  Python package/module to import and search for a class named 'Player' (to
  instantiate for each player in the game). When we test your programs this
  will just be your top-level package (i.e. 'your_team_name').

  If you want to play games with another player class from another package
  (e.g. while you develop your player), you can use any absolute module name
  (as used with import statements, e.g. 'your_team_name.player2') or relative
  path (to a file or directory containing the Python module, e.g. 'your_team_
  name/player3' or 'your_team_name/players/player4.py').

  Either way, the referee will attempt to import the specified package/module
  and then load a class named 'Player'. If you want the referee to look for a
  class with some other name you can put the alternative class name after a
  colon symbol ':' (e.g. 'your_team_name:DifferentPlayer').

  upper                 location of Upper's Player class (e.g. package name)
  lower                 location of Lower's Player class (e.g. package name)

optional arguments:
  -h, --help            show this message.
  -V, --version         show program's version number and exit
  -d [delay], --delay [delay]
                        how long (float, seconds) to wait between game
                        turns. 0: no delay; negative: wait for user input.
  -s [space_limit], --space [space_limit]
                        limit on memory space (float, MB) for each player.
  -t [time_limit], --time [time_limit]
                        limit on CPU time (float, seconds) for each player.
  -D, --debug           switch to printing the debug board (with
                        coordinates) (equivalent to -v or -v3).
  -v [{0,1,2,3}], --verbosity [{0,1,2,3}]
                        control the level of output (not including output
                        from players). 0: no output except result; 1:
                        commentary, but no board display; 2: (default)
                        commentary and board display; 3: (equivalent to -D)
                        larger board showing coordinates.
  -l [LOGFILE], --logfile [LOGFILE]
                        if you supply this flag the referee will create a
                        log of all game actions in a text file named LOGFILE
                        (default: game.log).
  -c, --colour          force colour display using ANSI control sequences
                        (default behaviour is automatic based on system).
  -C, --colourless      force NO colour display (see -c).
  -u, --unicode         force pretty display using unicode characters
                        (default behaviour is automatic based on system).
  -a, --ascii           force basic display using only ASCII characters (see
                        -u).
```

## Player interface

A Player is a class with the following three methods:

* `def __init__(self, player):`:

    Called once at the beginning of a game to initialise this player.
    Set up an internal representation of the game state.

    The parameter player is the string "upper" (if the instance will
    play as Upper), or the string "lower" (if the instance will play
    as Lower).


* `def action(self):`

    Called at the beginning of each turn. Based on the current state
    of the game, select an action to play this turn.


* `def update(self, opponent_action, player_action):`

    Called at the end of each turn to inform this player of both
    players' chosen actions. Update your internal representation
    of the game state.

    The parameter opponent_action is the opponent's chosen action,
    and player_action is this instance's latest chosen action.


## Battleground client usage

To play a game against another teams' programs using the online
battleground. See `battleground.pdf` for full instructions, or the usage below.

```
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
```

## Battleground server usage

Install the server module `server` alongside `battleground` (which provides the
protocol) and `referee` (which provides the game logic).

You should also install a module called `cpu` which provides the automatic opponents
in special channels, or remove/change the imports and `SPECIAL_CHANNELS` dictionary
atop `server/__main__.py`.

Invoke the server with a command like:

```
python3 -um server > log.txt 2>&1 & disown %1
```

The server will run on port 12360, accumulating a (big) log in `log.txt`,
and individual game logs in `logs/game_{player_names}_at_{start_time}.txt`.

