package aiproj.slider.agents;

import java.util.Scanner;
import java.util.Random;
import java.util.ArrayList;

import aiproj.slider.SliderPlayer;
import aiproj.slider.Move;

public class AgentAlpha implements SliderPlayer {

	// HELPER CLASSES
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

	// the board
	protected int n;
	protected Piece[][] grid;
	ArrayList<MyPiece> pieces;
	ArrayList<MyPiece> enemyPieces;


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
		this.enemyPieces = new ArrayList<MyPiece>(n-1);
		for (int i = 0; i < n; i++) {
			for (int j = 0; j < n; j++) {
				if(this.grid[i][j] == Piece.HSLIDER) {
					pieces.add(new MyPiece(i, j));
				} else if (this.grid[i][j] == Piece.VSLIDER) {
					enemyPieces.add(new MyPiece(i, j));
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

		int toi = move.i, toj = move.j;
		switch (move.d) {
			case UP:	toj++; break;
			case DOWN:	toj--; break;
			case RIGHT:	toi++; break;
			case LEFT:	toi--; break;
		}

		if (toi < n && toj < n) {
			grid[toi][toj] = grid[move.i][move.j];
		}
		grid[move.i][move.j] = Piece.BLANK;

		// which piece was this? update it.
		ArrayList<MyPiece> done = new ArrayList<MyPiece>();
		for(MyPiece piece : pieces) {
			if (piece.i == move.i && piece.j == move.j) {
				piece.i = toi;
				piece.j = toj;
				if (toi == n) {
					done.add(piece);
				}
			}
		}
		for(MyPiece piece : enemyPieces) {
			if (piece.i == move.i && piece.j == move.j) {
				piece.i = toi;
				piece.j = toj;
				if (toj == n) {
					done.add(piece);
				}
			}
		}

		// remove the "done" pieces
		for(MyPiece piece : done) {
			pieces.remove(piece);
			enemyPieces.remove(piece);
		}
	}

	private void unapply(Move move) {
		if (move == null) {
			// no move to apply
			return;
		}

		int toi = move.i, toj = move.j;
		switch (move.d) {
			case UP:	toj++; break;
			case DOWN:	toj--; break;
			case RIGHT:	toi++; break;
			case LEFT:	toi--; break;
		}

		if (toi < n && toj < n) {
			grid[move.i][move.j] = grid[toi][toj];
			grid[toi][toj] = Piece.BLANK;
		}

		for(MyPiece piece : pieces) {
			if (piece.i == toi && piece.j == toj) {
				piece.i = move.i;
				piece.j = move.j;
			}
		}
		for(MyPiece piece : enemyPieces) {
			if (piece.i == toi && piece.j == toj) {
				piece.i = move.i;
				piece.j = move.j;
			}
		}

		if (toi == n) {
			// this was a hslider, and was removed: add it back!
			grid[move.i][move.j] = Piece.HSLIDER;
			pieces.add(new MyPiece(move.i, move.j));
		} else if (toj == n) {
			// this was a vslider, and was removed: add it back!
			grid[move.i][move.j] = Piece.VSLIDER;
			enemyPieces.add(new MyPiece(move.i, move.j));
		}
	}














	private static final int DEPTH_LIMIT = 5;
	private Move makeMove() {
		int evalmax = n*n*n;
		SearchPair sp = minimaxMax(0, -evalmax, evalmax);
		return sp.move;
	}

	private SearchPair minimaxMax(int depth, int alpha, int beta) {

		if (depth >= DEPTH_LIMIT) {
			int score = evaluate();
			return new SearchPair(null, score);
		}

		// max over our moves
		SearchPair max = null;

		ArrayList<Move> moves = getHChoices();
		for (Move move : moves) {
			
			apply(move);
			
			// assuming enemy mins over their moves
			SearchPair min = minimaxMin(depth, alpha, beta);
			
			unapply(move);

			if (max == null || min.score > max.score) {
				max = new SearchPair(move, min.score);
				if (max.score > alpha) alpha = max.score;
				if (beta <= alpha) break;
			}
		}

		if (max == null) {
			SearchPair min = minimaxMin(depth, alpha, beta);
			max = new SearchPair(null, min.score);
		}

		return max;
	}

	private SearchPair minimaxMin(int depth, int alpha, int beta) {
		// assuming enemy maxes over their moves (min for us)
		SearchPair min = null;
		
		ArrayList<Move> counters = getVChoices();
		for(Move counter : counters) {
			apply(counter);
			
			SearchPair minimax = minimaxMax(depth + 1, alpha, beta);

			unapply(counter);

			if (min == null || minimax.score < min.score) {
				min = new SearchPair(counter, minimax.score);
				if (min.score < beta) beta = min.score;
				if (beta <= alpha) break;
			}
		}

		if (min == null) {
			SearchPair minimax = minimaxMax(depth + 1, alpha, beta);
			min = new SearchPair(null, minimax.score);
		}

		return min;
	}

	// evaluate the board from the perspective of HSLIDER (transforming taken
	// care of)
	private int evaluate() {
		int score = 0;
		for (MyPiece piece : pieces) {
			score += piece.i * piece.i;
			if (piece.i < n-1 && grid[piece.i+1][piece.j]==Piece.VSLIDER) {
				score -= piece.i * piece.i / 2;
			}
		}
		for (MyPiece piece : enemyPieces) {
			score -= piece.j * piece.j;
			if (piece.j < n-1 && grid[piece.i][piece.j+1]==Piece.HSLIDER) {
				score += piece.j * piece.j / 2;
			}
		}
		score -= (pieces.size() - enemyPieces.size())*grid.length*grid.length;
		return score;
	}

	private ArrayList<Move> getHChoices() {

		ArrayList<Move> choices = new ArrayList<Move>(3*pieces.size());
		
		Move.Direction[] directions = new Move.Direction[]{
				Move.Direction.RIGHT, Move.Direction.UP, Move.Direction.DOWN};
		
		for (Move.Direction direction : directions) {
			for (MyPiece piece : pieces) {
				int toi = piece.i, toj = piece.j;
				switch (direction) {
					case RIGHT:	toi++; break;
					case UP:	toj++; break;
					case DOWN:	toj--; break;
				}

				// we can make this move if it's a winner
				if (toi == n) {
					choices.add(new Move(piece.i, piece.j, direction));
				} else if(toj >= 0 && toj < n && grid[toi][toj] == Piece.BLANK){
					// otherwise, we can make it if it's legal
					choices.add(new Move(piece.i, piece.j, direction));
				} else {
				}
			}
		}
		return choices;
	}

	private ArrayList<Move> getVChoices() {

		ArrayList<Move> choices = new ArrayList<Move>(3*enemyPieces.size());
		
		Move.Direction[] directions = new Move.Direction[]{
				Move.Direction.UP, Move.Direction.RIGHT, Move.Direction.LEFT};

		for (Move.Direction direction : directions) {
			for (MyPiece piece : enemyPieces) {
				int toi = piece.i, toj = piece.j;
				switch (direction) {
					case UP:	toj++; break;
					case RIGHT:	toi++; break;
					case LEFT:	toi--; break;
				}

				// we can make this move if it's a winner
				if (toj == n) {
					choices.add(new Move(piece.i, piece.j, direction));
				} else if(toi >= 0 && toi < n && grid[toi][toj] == Piece.BLANK){
					// otherwise, we can make it if it's legal
					choices.add(new Move(piece.i, piece.j, direction));
				}
			}
		}
		return choices;
	}

	private static class SearchPair {
		public final Move move;
		public final int score;
		SearchPair(Move move, int score) {
			this.move = move;
			this.score = score;
		}
	}
}