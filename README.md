# Let the games begin!

From 2017 to 2021, I worked as a head TA for
[*COMP30024 Artificial Intellience*](https://handbook.unimelb.edu.au/subjects/comp30024/print),
an introductory AI class at the University of Melbourne.

Each year, I develop an original board game for the students to play. Well,
it's for their computers to play, but, if I do say so myself, some of the
games end up being fun for humans too!

Anyway, over a few weeks, the students work in pairs on the challenging and
open-ended task of creating a Python program capable of playing the game as
adeptly as possible.
We typically run an official *tournament* at the end of the semester to find
out which teams have achieved this goal most convincingly.
Alongside the project, we also provide an online *battleground server*,
enabling the students to compete during the semester without sharing code.

This repository documents these games, and the projects, and includes some
of the associated code.

> #### Status:
> 
> The games from my tenure as head TA, back to 2017, are more-or-less
> documented, with only a few missing pieces.
> More details of this semester's game are forthcoming.
> 
> I am considering compiling a 'hall of fame' with information about the
> winners of each year's tournament, and linking to other repositories
> around GitHub with exemplary students' code, if I can find it.
> If you want to be listed, contact me or raise an issue.


## Contents

* [2021 game: *RoPaSci 360*](#ropasci-360)
* [2020 game: *Expendibots*](#expendibots)
* [2019 game: *Chexers*](#chexers)
* [2018 game: *Watch Your Back!*](#watch-your-back)
* [2017 game: *Slider*](#slider)
* [2016 game: *Hexifence*](#hexifence)


## RoPaSci 360

> *RoPaSci 360* is a simultaneous-play board game of chance and anticipation
> in the spirit of the storied hand-game known by many names throughout the
> world, including *Roshambo*, *Jan-Ken*, and, of course,
> *Rock-Paper-Scissors*.
> Throw down a team of tokens with which to crush, cover, and cut through
> your opponent. Attack them when and where they least expect it, but be
> quick to slip away or you won't escape their retaliation!
> Have you anticipated your opponent's next move, or are you thinking
> exactly what they want you to think? *Rock, paper, scissors, throw!*

In 2021, we will play *RoPaSci 360*, a simultaneous-play board game inspired
by the hand-game classic.

Contents:

* The rules of the Game of *RoPaSci360*
  \[[rules pdf](2021-rps360/game-rules/game-rules.pdf)\]
* A javascript implementation courtesy of
  [Rowan Warneke](https://github.com/rwarneke)
  \[[hosted version](https://ropasci360.herokuapp.com)\]
  \[[source repository](https://github.com/rwarneke/RoPaSci360)\]
* The warmup project, to solve a single-player variant using non-adversarial
  search algorithms
  \[[specification pdf](2021-rps360/warmup/specification.pdf)\]
  \[[template code](2021-rps360/warmup/template/)\]
  \[[test cases and creator](2021-rps360/warmup/tests/)\]
  \[[sample solution](2021-rps360/warmup/sample-solution/)\]
* My *bonus lecture* on extending adversarial search techniques to
  simultaneous-play games
  \[[slides pdf](2021-rps360/lecture/slides.pdf)\]
  \[[recording](2021-rps360/lecture/recording.mp4)\]

Later, I will add:

* The main project, to build a program to play the game
  \[[specification pdf](#)\]
  \[[driver and template code](#)\]
* The online RoPaSci 360 *battleground* implementing the Random Online
  Portable Adversary Server Connection Interface (ROPASCI) protocol
  \[[client and server code](#)\]


## Expendibots

> *Expendibots* is a fast paced action game where assembling and
> disassembling powerful stacks of bots will be the key to your survival.
> Sneak behind enemy lines and cause chain reactions to do huge damage,
> but watch out for friendly fire!
> Can you successfully fend off your opponent's attacks and emerge
> victorious?

In 2020, as I completed an exchange semester when I would normally be
teaching COMP30024. Over summer, I teamed up with my replacement head TA
Adam Kues to design and implement *Expendibots*, one of our most dynamic,
challenging, and exciting AI games since my first semester.

Contents:

* The rules of the Game of *Expendibots*
  \[[rules pdf](2020-expendibots/game-rules/game-rules.pdf)\]
* The warmup project, to solve a single-player variant using
  non-adversarial search algorithms
  \[[specification pdf](2020-expendibots/warmup/specification.pdf)\]
  \[[template code](2020-expendibots/warmup/)\]
  \[[sample solution](2020-expendibots/warmup/)\]
* The main project, to build a program to play the game
  \[[specification pdf](2020-expendibots/project/specification.pdf)\]
  \[[driver and template code](2020-expendibots/project/)\]
* The online Expendibots *battleground* implementing the
  Battle-Oriented Online Match (BOOM) protocol
  \[[client and server code](2020-expendibots/project/)\]
* TODO: Add Expendibots concept art or animation.


## Chexers

> Chexers is a three-player hexagonal turn-based race game.
> Test the loyalty of your band of two-faced checkerpieces as you charge
> them through a twisting and treacherous battleground.
> Will all your pieces stay true to your cause?
> Can you earn yourself some new followers in the chaos?
> To win this tumultuous chase, you must double-cross and triple-cross your
> way across the finish line before your opponents---three, two, one... go!

In 2019, we played *Chexers*, a three-player hexagonal board game where
players can convert their opponent's pieces as they race across the board.
The game turned out to be pretty playable, with the three-player dynamic
making it especially fun.

Contents:

* The rules of the Game of *Chexers*
  \[[rules pdf](2019-chexers/game-rules/game-rules.pdf)\]
* The warmup project, to solve a single-player variant using
  non-adversarial search algorithms
  \[[specification pdf](2019-chexers/warmup/specification.pdf)\]
  \[[template code](2019-chexers/warmup/template/)\]
  \[[test cases](2019-chexers/warmup/test-cases/)\]
  \[[sample solution](2019-chexers/warmup/sample-solution/)\]
* My *bonus lecture* on extending adversarial search techniques to
  *n*-player games
  \[[slides pdf](2019-chexers/maxn-lecture.pdf)\]
* The main project, to build a program to play the game
  \[[specification pdf](2019-chexers/project/specification.pdf)\]
  \[[driver and template code](2019-chexers/project/)\]
* The online Chexers *battleground* implementing the
  Centrally Connected Competitive Chexers Client Control (C-hex)
  protocol
  \[[client and server code](2019-chexers/project/)\]
* TODO: Add Chexers animation


## Watch Your Back!

> *Watch Your Back!* is a fast-paced combat board game.
> You control a team of ruthless rogues engaged in a fight to the death
> against your enemies.
> Within the confines of a checkerboard there is no rulebook and no
> referee, and the easiest way to a cut down an enemy is to stab
> them in the back.
> Control your lawless warriors to jump and slash their way around
> the board surrounding and silencing your enemies until none remain.
> And, of course, *watch your back!*

In 2018, we played *Watch Your Back!*, a two-player board game based loosely
on the ancient
[Ludus latruncolorum](https://en.wikipedia.org/wiki/Ludus_latrunculorum).

* The rules of the Game of *Watch Your Back!*
  \[[rules pdf](2018-wub/game-rules/game-rules.pdf)\]
* The warmup project, to solve a single-player variant using
  non-adversarial search algorithms
  \[[specification pdf](2018-wub/warmup/specification.pdf)\]
  \[[test cases](2018-wub/warmup/test-cases/)\]
  \[[sample solution](2018-wub/warmup/sample/solution/)\]
* The main project, to build a program to play the game
  \[[specification pdf](2019-wub/project/specification.pdf)\]
  \[[driver program](2019-wub/project/referee.py)\]
* TODO: Is the original battleground code lost forever?
* TODO: Add concept art
* TODO: Dig up tournament recording


## Slider

In 2017, we played *Slider*, a two-player race and blocking game. I did not
design this game, but it served as an inspiration for
[*Chexers*](#chexers) of 2019.

* The rules of the Game of *Slider*
  \[[rules pdf](2017-slider/game-rules/game-rules.pdf)\]
* The warmup project, to analyse a static game state
  \[[specification pdf](2017-slider/warmup/specification.pdf)\]
* The main project, to build a (Java) program to play the game
  \[[specification pdf](2017-slider/project/specification.pdf)\]
  \[[driver program](2017-slider/project/Referee.java)\]
* TODO: Dig up tournament recording

## Hexifence

In 2016, I was not the TA for COMP30024, in fact I was one of its students.
The game this year was *Hexifence*, a hexagonal variant of the pen-and-paper
game [Dots and Boxes](https://en.wikipedia.org/wiki/Dots_and_Boxes), and the
project was completed in Java.

I worked with my project partner Julian Tran to develop a program using basic
adversarial search techniques, some specialised game tactics ('double boxing')
and a high-level represetation of the board (*chunking* the board into
tactically-relevant 'chains' rather than searching over individual edges).
With our high-level representation, we were able to obtain excellent search
depth and to out-perform our cohort.

Contents:
* Our project work is, somewhat cringingly, publicly available in [another
  repository](https://github.com/matomatical/AI-projectB).
* That repository also includes the rules of the game and the project
  specification.
* TODO: Add animation of our program

