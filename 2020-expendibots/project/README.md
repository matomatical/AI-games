# Expendibots project code

## Contents

* `specification.pdf`, containing full details about the project
* `referee`, Python module acting as a driver for computerised games
* `player_template`, skeleton module for implementing a player
* `battleground`, module implementing client for the online battleground
* `battleground_server`, module implementing match-making server for the same

See usage notes below, and also the
[project specification](../project-spec.pdf).

> ### Warning
> 
> This code worked for the semester, but is not maintained. See the
> most-recent semester's code for a similar but more up-to-date
> implementation.

## Expendibots driver usage

Play a game of Expendibots between two Player classes.

Invoke with:

```
python3 -m referee [<options>] <white player> <black player>
```

Full usage information:

```
usage: referee [-h] [-V] [-d [delay]] [-s [space_limit]] [-t [time_limit]]
               [-D | -v [{0,1,2,3}]] [-l [LOGFILE]] [-c | -C] [-u | -a]
               white black

conducts a game of Expendibots between 2 Player classes.

player package/class specifications (positional arguments):
  
  The first 2 arguments are 'package specifications'. These specify which Python
  package/module to import and search for a class named 'Player' (to instantiate
  for each player in the game). When we test your programs this will just be
  your top-level package (i.e. 'your_team_name').
  
  If you want to play games with another player class from another package (e.g.
  while you develop your player), you can use any absolute module name (as used
  with import statements, e.g. 'your_team_name.player2') or relative path (to a
  file or directory containing the Python module, e.g. 'your_team_name/player3'
  or 'your_team_name/players/player4.py').
  
  Either way, the referee will attempt to import the specified package/module
  and then load a class named 'Player'. If you want the referee to look for a
  class with some other name you can put the alternative class name after a ':'
  (e.g. 'your_team_name:DifferentPlayer').

  white                 location of White's Player class (e.g. package name)
  black                 location of Black's Player class (e.g. package name)

optional arguments:
  -h, --help            show this message.
  -V, --version         show program's version number and exit
  -d [delay], --delay [delay]
                        how long (float, seconds) to wait between game turns.
                        0: no delay; negative: wait for user input.
  -s [space_limit], --space [space_limit]
                        limit on memory space (float, MB) for each player.
  -t [time_limit], --time [time_limit]
                        limit on CPU time (float, seconds) for each player.
  -D, --debug           switch to printing the debug board (with coordinates)
                        (equivalent to -v or -v3).
  -v [{0,1,2,3}], --verbosity [{0,1,2,3}]
                        control the level of output (not including output from
                        players). 0: no output except result; 1: commentary,
                        but no board display; 2: (default) commentary and
                        board display; 3: (equivalent to -D) larger board
                        showing coordinates.
  -l [LOGFILE], --logfile [LOGFILE]
                        if you supply this flag the referee will create a log
                        of all game actions in a text file named LOGFILE
                        (default: game.log).
  -c, --colour          force colour display using ANSI control sequences
                        (default behaviour is automatic based on system).
  -C, --colourless      force NO colour display (see -c).
  -u, --unicode         force pretty display using unicode characters (default
                        behaviour is automatic based on system).
  -a, --ascii           force basic display using only ASCII characters (see
                        -u).
```

## Player interface

A Player is a class with the following three methods:

* `def __init__(self, colour):`:

    This method is called once at the beginning of the game to initialise
    your player. You should use this opportunity to set up your own internal
    representation of the game state, and any other information about the 
    game state you would like to maintain for the duration of the game.

    The parameter colour will be a string representing the player your 
    program will play as (White or Black). The value will be one of the 
    strings "white" or "black" correspondingly.


* `def action(self):`

    This method is called at the beginning of each of your turns to request 
    a choice of action from your program.

    Based on the current state of the game, your player should select and 
    return an allowed action to play on this turn. The action must be
    represented based on the spec's instructions for representing actions.


* `def update(self, colour, action):`

    This method is called at the end of every turn (including your player’s 
    turns) to inform your player about the most recent action. You should 
    use this opportunity to maintain your internal representation of the 
    game state and any other information about the game you are storing.

    The parameter colour will be a string representing the player whose turn
    it is (White or Black). The value will be one of the strings "white" or
    "black" correspondingly.

    The parameter action is a representation of the most recent action
    conforming to the spec's instructions for representing actions.

    You may assume that action will always correspond to an allowed action 
    for the player colour (your method does not need to validate the action
    against the game rules).


## Battleground client usage

To play a game against another teams' programs using the online
battleground.

To play a game using the battleground client, invoke it as follows, ensuring
that
the `battleground` package (the directory named `battleground`),
the `referee` package (the directory named `referee`), and
your player package (the directory named with your team name)
are all within your current directory:

```
python3 -m battleground <player package> <online name>
```

The client offers many additional command-line options,
including for
limiting the opponents matched using a 'channel'/'passphrase';
controlling output verbosity;
creating an action log;
and using other player classes (not named Player) from a package.

Full usage information (`python3 -m battleground -h`):

```
usage: battleground [-h] [-V] [-H HOST] [-P PORT] [-D | -v [{0,1,2,3}]]
                    [-l [LOGFILE]] [-c | -C] [-u | -a]
                    player name [channel]

play against your classmates on the online battleground!

player package/class specifications (positional arguments):
  player                location of your Player class (e.g. package name)
  name                  identify your player on the battleground server (e.g.
                        team name or player name)
  channel               restrict matchmaking to players specifying the same
                        channel (optional; leave blank to play against anyone)

optional arguments:
  -h, --help            show this message
  -V, --version         show program's version number and exit
  -H HOST, --host HOST  address of server (leave blank for default)
  -P PORT, --port PORT  port to contact server on (leave blank for default)
  -D, --debug           switch to printing the debug board (with coordinates)
                        (equivalent to -v or -v3)
  -v [{0,1,2,3}], --verbosity [{0,1,2,3}]
                        control the level of output (not including output from
                        player). 0: no output except result; 1: commentary,
                        but no board display; 2: (default) commentary and
                        board display; 3: (equivalent to -D) larger board
                        showing coordinates.
  -l [LOGFILE], --logfile [LOGFILE]
                        if you supply this flag the client will create a log
                        of all game actions in a text file named LOGFILE
                        (default: battle.log)
  -c, --colour          force colour display using ANSI control sequences
                        (default behaviour is automatic based on system).
  -C, --colourless      force NO colour display (see -c).
  -u, --unicode         force pretty display using unicode characters (default
                        behaviour is automatic based on system).
  -a, --ascii           force basic display using only ASCII characters (see
                        -u).
```

## Battleground server usage

Install the server module `battleground-server` alongside `battleground`
(which provides the protocol) and `referee` (which provides the game logic).

Invoke the server with a command like:

```
python3 -um battleground-server > log.txt 2>&1
disown %1
```

The server will run on port 54321, accumulating a (big) log in `log.txt`,
and individual game logs in `logs/game_{player_names}_at_{start_time}.txt`.

