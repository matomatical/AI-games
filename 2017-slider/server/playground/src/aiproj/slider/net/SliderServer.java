/*
 * Server
 */

package aiproj.slider.net;

import java.io.IOException;

import java.net.ServerSocket;
import java.net.Socket;

import aiproj.slider.Move;
import aiproj.slider.SliderPlayer;

// slider server (main) class at the bottom of this file

class Servant implements Runnable {
	
	Socket client;
	public Servant(Socket client) {
		this.client = client;
	}
	
	public void run() {
		// hello! welcome to this thread!
		
		// open a new protocol for this client
		SliderProtocol proto = null;
		try {
			proto = new SliderProtocol(this.client);
		} catch (ConnectionException e) {
			// not much we can do about this, let's just close the socket
			// and end the thread
			Log.error(e.getMessage());
			try {
				client.close();
			} catch (IOException f) {
				Log.error("failed to close socket:" + f.getMessage());
			}
			Log.log("abandon thread");
			return;
		}
		
		// otherwise, try to match this client, or leave them behind for
		// another thread to pick up
		SliderProtocol match = null;
		match = matchOrLeave(proto);

		if (match == proto) {
			// if we ran into an error before matching, we just have one
			// client to close
			Log.log("closing original client");
			try {
				proto.close();
			} catch (ConnectionException e) {
				Log.error(e.getMessage());
			}
			
		} else if (match != null) {
			// if we matched and played a game, then we have to
			// clean up both clients
			Log.log("closing original and matched client");
			try {
				proto.close();
			} catch (ConnectionException e) {
				Log.error(e.getMessage());
			}
			try {
				match.close();
			} catch (ConnectionException e) {
				Log.error(e.getMessage());
			}
			
		} else {
			// otherwise, we need to leave our client open
			// for a future thread to match with
		}
		
		Log.log("end of thread");
		return;
	}
	
	public SliderProtocol matchOrLeave(SliderProtocol p) {
		
		// send HIST
		HISTMessage hist = new HISTMessage(MatchHistory.getGames());
		p.sendMessage(hist);

		// get PLAY
		PLAYMessage play = null;
		try {
			play = (PLAYMessage)p.getMessage();
		} catch (DisconnectException e) {
			// uh oh... client disconnected!
			// abandon thread before we matched!
			return p;
		}
		p.name = play.name;

		// start matchmaking
		Log.log("matchmaking...");
		boolean matching = true;
		SliderProtocol q = null;
		while (matching) {
			
			// attempt to find a match
			q = MatchMaker.match(play.dimension, play.passphrase, p);
			
			if (q == null) {
				// this proto was deposited! wait for a match later
				Log.log("match not found, player depositied with passphrase '"+play.passphrase+"'");
				matching = false;
				
			} else {
				// found a match!
				Log.log("match found!");
				matching = false;
				
				// but wait! they may have disconnected in the mean time...
				// will have to try to reach them to see
				GAMEMessage game = new GAMEMessage(p.name, q.name);
				q.sendMessage(game);
				try {
					OKAYMessage qokay = (OKAYMessage)q.getMessage();
				} catch (DisconnectException e) {
					// the other player is no longer connected!
					// okay, so we still need to try and match...
					Log.log("matched player was no longer connected!");
					try {
						// close this old thread
						q.close();
					} catch (ConnectionException f) {
						Log.error("failed to close socket:" + f.getMessage());
					}
					matching = true;
				}
				
				// if we did succeed... send the message to the other player too!
				if (matching == false) {
					
					p.sendMessage(game);
					try {
						OKAYMessage pokay = (OKAYMessage)p.getMessage();
					} catch (DisconnectException e) {
						// okay, this client disconnected... send error to other and end the thread
						Log.log("matching player disconnected right after match!");
						ERROMessage erro = new ERROMessage("partner disconnected");
						q.sendMessage(erro);
						q.close();
						
						// return q so that we can close both players
						return q;
					}
				}	
			}
		}

		// at this point, if we managed to find a player, we are ready to begin!
		if (q != null) {
			try {
				playGame(p, q, play.dimension);
			} catch (DisconnectException e) {
				// either play has disconnected
				// try to let both players know:
				ERROMessage erro = new ERROMessage("partner disconnected");
				p.sendMessage(erro);
				q.sendMessage(erro);
				
			} catch (ClassCastException e) {
				// something went wrong with the protocol
				// disconnect both players
				ERROMessage erro = new ERROMessage("unexpected message, protocol broken");
				p.sendMessage(erro);
				q.sendMessage(erro);
			}
			
			// whatever happened, return q so that we can close both players
			return q;
		} else {
			// else, wait for someone else to pick up this player and play in that thread
			// return null so that we don't close either player
			return null;
		}
	}

	private void playGame(SliderProtocol p, SliderProtocol q, int dimension) {
		
		/* * * *
		 * set up the board and initialise the board and players
		 */

		// create a new board
		Board board = new Board(dimension);
		
		// set up timer and time array for profiling
		RealTimer timer = new RealTimer(); // nanosecond real-time usage timer
		long[] times = new long[]{0, 0}; // cumulative time spent by each player
		
		// and initialise the players
		SliderPlayer[] players = new SliderPlayer[2];
		
		timer.start();
		players[Player.H] = new RemotePlayer(p);
		players[Player.H].init(dimension, board.toString(), 'H');
		times[Player.H] += timer.clock();
		
		timer.start();
		players[Player.V] = new RemotePlayer(q);
		players[Player.V].init(dimension, board.toString(), 'V');
		times[Player.V] += timer.clock();
	
		/* * * *
		 * now, play the game!
		 */

		int turn = Player.H;
		Move previousMove = null;
		String message = null;
		
		// game loop
		while (!board.finished()) {

			// calculate and time move
			timer.start();
			players[turn].update(previousMove);
			previousMove = players[turn].move();
			times[turn] += timer.clock();
			

			// validate and perform move
			try {
				board.validateAndMove(previousMove, Player.pieces[turn]);
			} catch (IllegalMoveException e) {
				// exit game due to violation, likely
				// leading to loss for players[turn]
				message = e.getMessage();
				break;
			}

			// other player's turn next
			turn = Player.other(turn);
		}
		
		/* * * *
		 * game over! send one last update message, and 
		 * display the results to both players
		 */

		OVERMessage over;
		if(board.finished()) {
			
			// send the finishing move
			timer.start();
			players[turn].update(previousMove);
			times[turn] += timer.clock();

			// calculate the result
			String winner = board.winner();
			over = new OVERMessage("winner: " + winner);

			// log the game
			if (winner == "horizontal!") {
				MatchHistory.logGame(p.name +" beat "+ q.name);
			} else if (winner == "vertical!") {
				MatchHistory.logGame(q.name +" beat "+ p.name);
			} else {
				MatchHistory.logGame(p.name +" tied "+ q.name);
			}

		} else {
			over = new OVERMessage("illegal move (" + (turn==Player.H ? "horizontal" : "vertical") + "): " + message);
			// dont log illegal-move games
		}

		// either way, send an OVER message to BOTH players
		p.sendMessage(over);
		q.sendMessage(over);
	}

	/** Collection of game helper functions and constants */
	private static interface Player {
		static final int H = 0, V = 1;
		static final Piece[] pieces = new Piece[]{Piece.HSLIDER, Piece.VSLIDER};
		static int other(int player) { return 1 - player; }
		// 1 - 0 is 1, and 1 - 1 is 0, so 1 - H is V, and 1 - V is H!
	}
}

/** Small helper class for nanosecond real timing */
class RealTimer {
	long start = 0; // nanosecond time we started timing

	/** Restart the clock to start timing again from now */
	public void start() {
		start = System.nanoTime();
	}

	/**
	 * Return time since started (clock() can be called multiple times per 
	 * start(), but start() should be called at least once before clock())
	 */
	public long clock() {
		return System.nanoTime() - start;
	}
}

public class SliderServer {

	public static void main(String[] args) {

		Log.logging = true;
		
		/* * * *
		 * first, read and validate command line options, and open the slider
		 * server on the specified port
		 */
		
		// parse command-line input
		Options options = new Options(args);

		// open arrivals socket
		ServerSocket arrivals = null;
		try {
			arrivals = new ServerSocket(options.port);
			Log.log("listening for connections on port " + options.port);
		} catch (IOException e) {
			Log.error("bind error: " + e.getMessage());
			System.exit(1);
		}

		/* * * *
		 * then, loop, accepting new connections and handing them to Servant threads
		 */
		while(arrivals.isBound()){
			
			Socket client = null;
			try {
				// wait for an incoming client connection
				client = arrivals.accept();
				Log.log("new connection established");
			
			} catch (IOException e) {
				// all right, some kind of listen/accept error now...
				Log.error("accept error: " + e.getMessage());

				// skip this client and go to the next accept
				continue;
			}
			
			// start a new handler for this socket
			Runnable r = new Servant(client);
			Thread t = new Thread(r);
			t.start();
		}
		
		/* * * *
		 * finally (never), close up and go home
		 */
		try {
			arrivals.close();
		} catch (IOException e) {
			Log.error("close error: " + e.getMessage());
			System.exit(1);
		}
	}

	private static class Options {
		public final short port;
		public Options(String[] args) {
			if (args.length < 1) {
				port = 1026;
			} else {
				port = Short.parseShort(args[0]);
			}
		}
	}
}
