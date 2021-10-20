Here are some answers to previously asked questions on the LMS Discussion Board. A reminder to continually check the Discussion Board to keep up with clarifications and answers to questions about the game and the project.

Project Part A
==============

Board format
------------

**Why don't the example input and the corresponding board diagram (figure 1) match up properly in the Project Part A specification?**

Sorry, there is a small error in figure 1: the board diagram (right of the figure) should have an additional Black piece on square (7, 3) (close to the top right corner).

There is another error: both the input and the board diagram contain 13 White pieces. This should not have been the case: the maximum number of White pieces the board can contain (according to the rules of the game) is 12.

You can assume that the input to your program will never specify a board with more than 12 of either type of piece.


Calculating Massacre
--------------------

**Can we assume all Black pieces will be killable?**

Yes, there will always be a path from the starting board configuration to a 'goal' configuration (a board configuration with no Black pieces). We will **not** test your program with 'impossible' situations such as a group of four Black pieces in a 2 by 2 square formation:

    X - - - - - - X
    - - - O O - - -
    - O O O O O O -
    - O O - - O O -
    - - - - - - - -
    - - - @ @ - - -
    - - - @ @ - - -
    X - - - - - - X



**Do we need to account for the board shrinking after a certain number of moves?**

No. You should assume that the board will not shrink while calculating Massacre.


**What is the maximum sequence length and number of pieces we should be able to calculate in a reasonable amount of time?**

Please see the submission instructions.


**Do we need to account for Black pieces eliminating White pieces?**

Yes. Black pieces cannot make moves, but they can still eliminate White pieces.

For example, from the following board, the move '(1, 1) -> (1, 0)' (the leftmost White piece moves upwards) will result in this White piece being eliminated:

    X - @ - O - - X
    - O - - - - - -
    - - - - - - - -
    - - - - - - - -
    - - - - - - - -
    - - - - - - - -
    - - - - - - - -
    X - - - - - - X

Therefore, the sequence of moves:

    (1, 1) -> (1, 0)
    (4, 0) -> (3, 0)

Is **not** a correct output sequence (it does not result in all Black pieces being eliminated).

