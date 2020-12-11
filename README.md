# Let the games begin!

From 2017 to 2021, I worked as a head TA for *COMP30024 Artificial
Intellience*, an introductory AI class at the University of Melbourne.

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

> ### TODO
> 
> This repository is under construction. More details will be added when I
> find time. If you want them sooner, remind me to find time by opening an
> issue. Thanks for your patience!
> 
> #### Status:
> 
> Chexers (2019) and Expendibots (2020) are more-or-less documented.
> Later I will dig up information on the older games and add these.
> I am also considering compiling a 'hall of fame' with information about
> the winners of each year's tournament,
> and linking to other repositories around GitHub with examplary students'
> code.


## Contents

* [2021 game: *Rock-Paper-Scissors 360*](#rock-paper-scissors-360)
* [2020 game: *Expendibots*](#expendibots)
* [2019 game: *Chexers*](#chexers)
* [2018 game: *Watch Your Back!*](#watch-your-back)
* [2017 game: *Slider*](#slider)
* [2016 game: *Hexifence*](#hexifence)
* [Licensing](#licensing)


## Rock-Paper-Scissors 360

In 2021, we will play *Rock--Paper--Scissors 360*, a simultaneous-play board
game inspired by the classic game of chance and anticipation. I'm still
developing the details, and will update this repository after the semester.

* TODO: Update after semester


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
  \[[template code](2019-chexers/warmup/)\]
  \[[sample solution](2019-chexers/warmup/)\]
* The main project, to build a program to play the game
  \[[specification pdf](2019-chexers/project/specification.pdf)\]
  \[[driver and template code](2019-chexers/project/)\]
* The online Chexers *battleground* implementing the
  Centrally Connected Competitive Chexers Client Control (C-hex)
  protocol
  \[[client and server code](2019-chexers/project/)\]
* TODO: Add Chexers animation


## Watch Your Back!

In 2018, we played *Watch Your Back!*, a two-player board game based loosely
on the ancient
[Ludus latruncolorum](https://en.wikipedia.org/wiki/Ludus_latrunculorum).

* TODO: The details of the game are somewhere... but I might have to dig
  a little to find them.
* TODO: Add the original WUB-protocol server (do I still have it?)
* TODO: Add concept art and/or tournament video?


## Slider

In 2017, we played *Slider*, a two-player race and blocking game. I did not
design this game, but it served as an inspiration for
[*Chexers*](#chexers) of 2019.

* TODO: Add some files and details about Slider.
* TODO: Add the tournament video/animation (do I still have it?)


## Hexifence

In 2016, I was not the TA for COMP30024, in fact I was one of its students.
The game this year was *Hexifence*, a hexagonal variant of the pen-and-paper
game [Dots and Boxes](https://en.wikipedia.org/wiki/Dots_and_Boxes), and the
project was completed in Java.

I worked with my project partner Julian Tran to develop a program using basic
adversarial search techniques, some specialised game tactics ('double boxing')
and a high-level represetation of the board (chunking the board into
tactically-relevant 'chains' rather than searching over individual edges).
With our high-level representation, we were able to obtain excellent search
depth and to out-perform our cohort.

* TODO: Link to files
* TODO: Add animation from our program


## Licensing

I am willing to share these teaching materials with other educators, and
with students looking for programming projects. I am willing to consider
sharing for other purposes. Please contact me to discuss a license.

* TODO: Just add a clear license to the repository
