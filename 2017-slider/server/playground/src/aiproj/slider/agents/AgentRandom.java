package aiproj.slider.agents;

import java.util.Scanner;
import java.util.Random;
import java.util.ArrayList;

import aiproj.slider.SliderPlayer;
import aiproj.slider.Move;

public class AgentRandom implements SliderPlayer {

	// the board
	protected int n;
	protected Piece[][] grid;
	protected ArrayList<MyPiece> pieces;

	// are we transforming?
	private boolean transforming;

	public void init(int dimension, String board, char player) {
		this.n = dimension;
		
		// scan board into temporary grid
		Piece[][] grid = new Piece[n][n];
		Scanner s = new Scanner(board);
		for (int j = n-1; j >= 0; j--) {
			for (int i = 0; i < n; i++) {
				grid[i][j] = Piece.fromString(s.next());
			}
		}

		// represent board as if we were Horizontal player
		transforming = (player == 'V');
		if (transforming) {
			this.grid = new Piece[n][n];
			for (int i = 0; i < n; i++) {
				for (int j = 0; j < n; j++) {
					this.grid[i][j] = grid[j][i];
					if (this.grid[i][j] == Piece.HSLIDER) {
						this.grid[i][j] = Piece.VSLIDER;
					} else if (this.grid[i][j] == Piece.VSLIDER) {
						this.grid[i][j] = Piece.HSLIDER;
					}
				}
			}
		} else { // already Horizontal
			this.grid = grid;
		}

		// (after transforming)
		// collect my pieces and store them in 'pieces' list
		this.pieces = new ArrayList<MyPiece>(n-1);
		for (int i = 0; i < n; i++) {
			for (int j = 0; j < n; j++) {
				if(this.grid[i][j] == Piece.HSLIDER) {
					pieces.add(new MyPiece(i, j));
				}
			}
		}
	}

	public void update(Move move) {
		apply(transform(move));
	}

	public Move move() {
		Move myMove = makeMove();
		apply(myMove);
		return transform(myMove);
	}

	// helper method to transform a move coming in or out of this player to
	// our internal representation, if necessary
	private Move transform(Move move) {
		if (move == null) {
			// no move to transform
			return null;
		}
		if ( ! transforming) {
			// no need to transform
			return move;
		}
		
		// otherwise,
		// we need to reflect direction and position in up/right diagonal
		Move.Direction d = null;
		switch (move.d) {
			case UP: 	d = Move.Direction.RIGHT; 	break;
			case RIGHT: d = Move.Direction.UP; 		break;
			case DOWN: 	d = Move.Direction.LEFT; 	break;
			case LEFT: 	d = Move.Direction.DOWN; 	break;
		}
		return new Move(move.j, move.i, d);
	}

	// helper method to apply a move to our internal
	// representation of the game board
	private void apply(Move move) {
		if (move == null) {
			// no move to apply
			return;
		}

		// otherwise, where are we going?
		int toi = move.i, toj = move.j;
		switch (move.d) {
			case UP:	toj++; break;
			case DOWN:	toj--; break;
			case RIGHT:	toi++; break;
			case LEFT:	toi--; break;
		}

		// if that's on the board,
		if (toi < n && toj < n) {
			grid[toi][toj] = grid[move.i][move.j];
		}
		grid[move.i][move.j] = Piece.BLANK;

		// move this piece in the list too
		MyPiece done = null;
		for(MyPiece piece : pieces) {
			if (piece.i == move.i && piece.j == move.j) {
				piece.i = toi;
				piece.j = toj;
				if (toi == n || toj == n) {
					done = piece;
				}
			}
		}
		if (done != null) {
			pieces.remove(done);
		}
	}





	// AGENT STRATEGY BEGINS HERE

	private static Random rng = new Random();
	
	protected Move makeMove() {

		ArrayList<Move> choices = getChoices();

		if (choices.size() > 0) {
			int choice = rng.nextInt(choices.size());
			return choices.get(choice);
		} else {
			return null;
		}
	}

	// list of moves, assuming we are Horizontal (transforming taken care of)
	private ArrayList<Move> getChoices() {

		ArrayList<Move> choices = new ArrayList<Move>(3*pieces.size());
		
		Move.Direction[] directions = new Move.Direction[]{
				Move.Direction.RIGHT, Move.Direction.UP, Move.Direction.DOWN};
		
		for (Move.Direction direction : directions) {
			for (MyPiece piece : pieces) {
				int toi = piece.i, toj = piece.j;
				switch (direction) {
					case UP:	toj++; break;
					case DOWN:	toj--; break;
					case RIGHT:	toi++; break;
					case LEFT:	toi--; break; // will never happen
				}

				// we can make this move if it's a winner
				if (toi == n) {
					choices.add(new Move(piece.i, piece.j, direction));
				} else if(toj >= 0 && toj < n && grid[toi][toj] == Piece.BLANK){
					// otherwise, we can make it if it's legal
					choices.add(new Move(piece.i, piece.j, direction));
				}
			}
		}

		return choices;
	}


	// helper class to store a piece
	private static class MyPiece {
		public int i, j;
		public MyPiece(int i, int j) {
			this.i = i;
			this.j = j;
		}
	}
	private static enum Piece {
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
}
