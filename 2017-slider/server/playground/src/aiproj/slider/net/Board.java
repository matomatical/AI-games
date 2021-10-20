package aiproj.slider.net;

import java.util.HashMap;
import java.util.Scanner;

import aiproj.slider.Move;

public class Board {

	private static java.util.Random rng = new java.util.Random();
	
	private Piece[][] grid;
	private int hsliders = 0, vsliders = 0, passes = 0;
	private final int n;
	
	private boolean loop = false;
	private static final int MAX_STATES = 5;
	private HashMap<String, Integer> stateCounts = new HashMap<String, Integer>();

	public Board(int dimension, String board) {
		this.n = dimension;
		this.grid = new Piece[n][n];

		Scanner s = new Scanner(board);
		for (int j = n-1; j >= 0; j--) {
			for (int i = 0; i < n; i++) {
				grid[i][j] = Piece.fromString(s.next());
			}
		}
		s.close();
	}
	
	public Board(int n) {
		this.n = n;
		this.grid = new Piece[n][n];

		// fill grid blank
		for (int i = 0; i < n; i++) {
			for (int j = 0; j < n; j++) {
				grid[i][j] = Piece.BLANK;
			}
		}

		// add H sliders
		for (int j = 1; j < n; j++) {
			grid[0][j] = Piece.HSLIDER;
			hsliders++;
		}

		// add V sliders
		for (int i = 1; i < n; i++) {
			grid[i][0] = Piece.VSLIDER;
			vsliders++;
		}

		// add blocked positions
		int nblocked = rng.nextInt(3);
		if (nblocked == 0) {
			// no blocked positions
		} else {
			// one or two blocked positions:
			int i = 1 + rng.nextInt(n-2);
			int j = 1 + rng.nextInt(n-2);
			if (nblocked == 1) {
				grid[i][j] = Piece.BLOCK;
			} else if (nblocked == 2) {
				if (rng.nextBoolean()) {
					grid[i][i] = Piece.BLOCK;
					grid[j][j] = Piece.BLOCK;
				} else {
					grid[i][j] = Piece.BLOCK;
					grid[j][i] = Piece.BLOCK;
				}
			}
		}
	}

	/** represent a board as text for rendering */
	private static final char[] SYMBOLS = {'+', 'B', 'H', 'V'};
	public String toString() {
		StringBuilder s = new StringBuilder(2 * n * n);
		for (int j = n-1; j >= 0; j--) {
			s.append(SYMBOLS[grid[0][j].ordinal()]);
			for (int i = 1; i < n; i++) {
				s.append(' ');
				s.append(SYMBOLS[grid[i][j].ordinal()]);
			}
			s.append('\n');
		}
		return s.toString();
	}

	/** change the board state (assumes move is valid) */
	public void justMove(Move move) {
		if (move == null) {
			// nothing to do
			return;
		}

		// where's the piece?
		Piece piece = grid[move.i][move.j];

		// where's the next space?
		int toi = move.i, toj = move.j;
		switch(move.d){
			case UP:	toj++; break;
			case DOWN:	toj--; break;
			case RIGHT:	toi++; break;
			case LEFT:	toi--; break;
		}

		// are we advancing a piece off the board?
		if (piece == Piece.HSLIDER && toi == n) {
			grid[move.i][move.j] = Piece.BLANK;
			hsliders--;
			return;

		} else if (piece == Piece.VSLIDER && toj == n){
			grid[move.i][move.j] = Piece.BLANK;
			vsliders--;
			return;
		}

		// no? all good? alright, let's make the move!
		grid[move.i][move.j] = Piece.BLANK;
		grid[toi][toj] = piece;
		return;
	}
	
	/** validate a move and change the board state */
	public void validateAndMove(Move move, Piece turn) throws IllegalMoveException {
		// detect null move (pass)
		if (move == null) {
			// we better just check that there are really no legal moves
			for (int i = 0; i < n; i++) {
				for (int j = 0; j < n; j++) {
					if (grid[i][j] == turn && canMove(i, j)) {
						throw new IllegalMoveException(
								"can't pass, moves remain!");
					}
				}
			}

			// if we make it here, there were no legal moves: pass is legal
			passes++;
			return;
		} else {
			// we haven't seen a pass, so reset pass counter
			passes = 0;
		}

		// where's the piece?
		Piece piece = grid[move.i][move.j];

		// is it the right type of piece?
		if (piece != turn) {
			throw new IllegalMoveException("not your piece!");
		}
		if (piece == Piece.BLANK || piece == Piece.BLOCK) {
			throw new IllegalMoveException("no piece here!");
		}

		// is the direction allowed?
		if ((piece == Piece.HSLIDER && move.d == Move.Direction.LEFT)
			|| (piece == Piece.VSLIDER && move.d == Move.Direction.DOWN)) {
			throw new IllegalMoveException("can't move that direction!");
		}
		
		// where's the next space?
		int toi = move.i, toj = move.j;
		switch(move.d){
			case UP:	toj++; break;
			case DOWN:	toj--; break;
			case RIGHT:	toi++; break;
			case LEFT:	toi--; break;
		}

		// are we advancing a piece off the board?
		if (piece == Piece.HSLIDER && toi == n) {
			grid[move.i][move.j] = Piece.BLANK;
			hsliders--;
			return;

		} else if (piece == Piece.VSLIDER && toj == n){
			grid[move.i][move.j] = Piece.BLANK;
			vsliders--;
			return;
		}

		// if not, is the position we are moving to on the board?
		if (toj < 0 || toj >= n || toi < 0 || toi >= n) {
			throw new IllegalMoveException("can't move off the board!");
		}

		// is the position we are moving to already occupied?
		if (grid[toi][toj] != Piece.BLANK) {
			throw new IllegalMoveException("that position is occupied!");
		}

		// no? all good? alright, let's make the move!
		grid[move.i][move.j] = Piece.BLANK;
		grid[toi][toj] = piece;

		// finally, have we seen this state a few times before? if so, maybe
		// we've entered an infinite loop
		String s = this.toString();
		if (stateCounts.containsKey(s)) {
			stateCounts.put(s, stateCounts.get(s) + 1);
		} else {
			stateCounts.put(s, 1);
		}
		if (stateCounts.get(s) > MAX_STATES) {
			loop = true;
			throw new IllegalMoveException("repeated states, loop detected!");
		}
	}

	private boolean canMove(int i, int j) {
		if (grid[i][j] == Piece.HSLIDER) {
			// for HSLIDERs, check right, up, and down
			return (i+1 == n) || (grid[i+1][j] == Piece.BLANK)
				|| (j+1 < n && grid[i][j+1] == Piece.BLANK)
				|| (j-1 >= 0 && grid[i][j-1] == Piece.BLANK);
		
		} else if (grid[i][j] == Piece.VSLIDER) {
			// for VSLIDERs, check up, right, and left
			return (j+1 == n) || (grid[i][j+1] == Piece.BLANK)
				|| (i+1 < n && grid[i+1][j] == Piece.BLANK)
				|| (i-1 >= 0 && grid[i-1][j] == Piece.BLANK);
		
		} else {
			// any other square can't be moved
			return false;
		}
	}
	
	public boolean finished() {
		return (hsliders == 0) || (vsliders == 0) || (passes > 1) || loop;
	}

	public String winner() {
		if (hsliders == 0) {
			return "horizontal!";
		} else if (vsliders == 0) {
			return "vertical!";
		} else if (passes > 1 || loop) {
			return "nobody! (tie)";
		} else {
			return "everybody!";
		}
	}
}

/** Simple exception describing a move that fails validation */
class IllegalMoveException extends Exception {
	public IllegalMoveException(String message) {
		super(message);
	}
}

/** Enumeration of all of the possible states of a board position */
enum Piece {
	// possible values
	BLANK, BLOCK, HSLIDER, VSLIDER;

	// constructor
	public static Piece fromString(String symbol) {
		switch (symbol) {
			case "+": return Piece.BLANK;
			case "H": return Piece.HSLIDER;
			case "V": return Piece.VSLIDER;
			case "B": return Piece.BLOCK;
			default: throw new RuntimeException("unknown symbol: "+ symbol);
		}
	}
}