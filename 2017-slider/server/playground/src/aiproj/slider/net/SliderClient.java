package aiproj.slider.net;

import java.io.IOException;

import java.net.Socket;
import java.net.ConnectException;
import java.net.UnknownHostException;

import aiproj.slider.SliderPlayer;
import aiproj.slider.Move;

public class SliderClient {

	public static void main(String[] args) {

		/* * * *
		 * first, read and validate command line options, load the slider
		 * player class and connect to the game server
		 */
		
		// parse command-line input
		Options options = new Options(args);
		
		// load player class
		SliderPlayer player = null;
		try {
			player = (SliderPlayer)options.player.newInstance();
		} catch (IllegalAccessException | InstantiationException e) {
			System.err.println("player instantiation error: " + e.getMessage());
			System.exit(1);
		}

		// connect to server
		Socket server = null;
		try {
			server = new Socket(options.host, options.port);
		} catch (ConnectException e) {
			System.err.println("host unreachable: "+e.getMessage());
			System.exit(1);
		} catch (UnknownHostException e) {
			System.err.println("hostname unknown: "+e.getMessage());
			System.exit(1);
		} catch (IllegalArgumentException e) {
			System.err.println("invalid port: "+e.getMessage());
			System.exit(1);
		} catch (IOException e) {
			System.err.println("error: " + e.getMessage());
			System.exit(1);
		}
				

		/* * * *
		 * then, set up the protocol and begin playing the game with this server
		 */
		
		// establish protocol
		SliderProtocol p = null;
		try {
			p = new SliderProtocol(server);
		} catch (ConnectionException e) {
			System.err.println("error opening connection: " + e.getMessage());
			System.exit(1);
		}
		
		// play the game
		try {
			play(player, p, options);
		} catch (DisconnectException e) {
			System.err.println("lost connection with server: " + e.getMessage());
			System.exit(1);
		} catch (ClassCastException e) {
			System.err.println("error: broke protocol");
			System.exit(1);
		}
		
		/* * * *
		 * that's the end~ close the protocol and connection, and finish
		 */
		try {
			p.close();
		} catch (ConnectionException e) {
			System.err.println("error closing connection: " + e.getMessage());
			System.exit(1);
		}
		
		try {
			server.close();
		} catch (IOException e) {
			System.err.println("error closing connection: " + e.getMessage());
			System.exit(1);
		}
	}
	
	private static void play(SliderPlayer player, SliderProtocol p, Options options) {
		
		/* * * *
		 * receive a list of recent games from server, and display to user
		 */
		
		// receive a HIST message containing recent game results
		HISTMessage hist = (HISTMessage)p.getMessage();
		System.out.println("recent games:");
		for(String game : hist.games) {
			System.out.println(game);
		}
		System.out.println();

		
		/* * * *
		 * send a play request to the server and wait for a match to begin...
		 */
		
		// formulate and send PLAY message
		PLAYMessage play = new PLAYMessage(options.dimension, options.passphrase, options.playerName);
		p.sendMessage(play);

		// wait (potentially a while) for a match and subsequent GAME message
		GAMEMessage game = (GAMEMessage)p.getMessage();
		System.out.println("new game: " + game.hplayer + " as H vs " + game.vplayer + " as V");
		System.out.println();
		
		// send back OKAY message to show that we are still here
		OKAYMessage gameokay = new OKAYMessage();
		p.sendMessage(gameokay);
		
		/* * * *
		 * receive initialisation info, create the board and initialise the player
		 */

		// receive INIT message with board, player
		SliderMessage initmsg = p.getMessage();
		INITMessage init;
		if (initmsg.type.equals("INIT")) {
			init = (INITMessage)initmsg;
			player.init(options.dimension, init.board, init.player);
		
		// unless it was an error message, in which case end the thread
		} else if (initmsg.type.equals("ERRO")) {
			ERROMessage erro = (ERROMessage)initmsg;
			System.out.println("error: " + erro.reason);
			return;
		} else {
			System.out.println("error: broke protocol");
			return;
		}

		// send back OKAY message when we are ready
		OKAYMessage initokay = new OKAYMessage();
		p.sendMessage(initokay);

		// make a local version of the board
		Board localBoard = new Board(options.dimension, init.board);
		
		/* * * *
		 * now, play the game!
		 */
		boolean playing = true;
		String error = null, result = null;
		
		render(localBoard);
		while(playing) {

			// receive a message from the server, handle it depending on type
			SliderMessage message = p.getMessage();
			switch(message.type) {
				case "UPD8":
					UPD8Message upd8 = (UPD8Message)message;
					Move urmove = upd8.move;

					// update local board
					localBoard.justMove(urmove);

					// update the player
					player.update(urmove);
					
					// send back OKAY message
					OKAYMessage okay = new OKAYMessage();
					p.sendMessage(okay);

					break;
				
				case "MOVE":
					// call move() method to get move
					Move mymove = player.move();
					
					// update local board
					localBoard.justMove(mymove);
					
					// send back UPD8 (move) message
					UPD8Message move = new UPD8Message(mymove);
					p.sendMessage(move);

					break;
				
				case "ERRO":
					ERROMessage erro = (ERROMessage)message;
					error = erro.reason;
					playing = false;
					break;
				
				case "OVER":
					OVERMessage over = (OVERMessage)message;
					result = over.result;
					playing = false;
					break;

				default:
					// invalid message at this point
					error = "broke protocol!";
					playing = false;
					break;
			}

			// display the board
			render(localBoard);
		}

		// the game has ended!
		if (error != null) {
			System.out.println("error: " + error);
		}

		if (result != null) {
			System.out.println(result);
		}
	}

	// display the board to the screen
	private static void render(Board board) {
		System.out.println(board.toString());
	}

	// read command line options (player, game size, [passphrase], [host, port])
	private static class Options {
		private static final String PASSPHRASE = "";
		private static final short PORT = 1026;
		private static final String HOST = "slider.aiproj.net";

		public final int dimension;
		public final String playerName;
		public final Class player;
		public final String passphrase;
		public final String host;
		public final short port;

		static void printUsageInfoAndExit() {
			System.err.println("usage: aiproj.slider.net.SliderClient N player [phrase] [host] [port]");
			System.err.println("     N - dimension of board to use (N > 3)");
			System.err.println("player - fully qualified name of player");
			System.err.println("phrase - (optional) keyword to limit matches");
			System.err.println("  host - (optional) non-default hostname");
			System.err.println("  port - (optional) non-default port number");
			System.exit(1);
		}

		public Options(String[] args) {

			// are there enough arguments?
			if (args.length < 2) {
				printUsageInfoAndExit();
			}

			// check dimension of board
			this.dimension = Integer.parseInt(args[0]);
			if (! (dimension > 3) ) {
				System.err.println("invalid dimension: should be > 3");
				System.exit(1);
			}

			// attempt to locate classes provided by name
			String playerClassName = args[1];
			Class player = null;
			try {
				player = Class.forName(playerClassName);
			} catch (ClassNotFoundException e) {
				System.err.println("invalid class name: "+ e.getMessage());
				System.exit(1);
			}
			this.player = player;
			this.playerName = playerClassName;

			// was passphrase provided?
			if (args.length > 2) {
				this.passphrase = args[2];
			} else {
				this.passphrase = PASSPHRASE; // default: empty passphrase
			}

			// was hostname provided?
			if (args.length > 3) {
				this.host = args[3];
			} else {
				this.host = HOST; // default
			}
			
			// was port provided?
			if (args.length > 4) {
				this.port = Short.parseShort(args[4]);
			} else {
				this.port = PORT; // default
			}
			
			// all done!
		}
	}
}
