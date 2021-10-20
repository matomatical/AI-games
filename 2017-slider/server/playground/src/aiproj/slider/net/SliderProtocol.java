package aiproj.slider.net;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.PrintWriter;
import java.net.Socket;

import aiproj.slider.Move;

public class SliderProtocol {
	
	private static final int HEADER_LEN = 4;
	
	private BufferedReader 	i;
	private PrintWriter 	o;
	
	private Socket s;
	
	public String name = null;
	
	public SliderProtocol(Socket s) {
		this.s = s;
		try {
			i = new BufferedReader(new InputStreamReader(s.getInputStream()));
			o = new PrintWriter(s.getOutputStream());
		} catch (IOException e) {
			throw new ConnectionException("Failed to open streams: " + e.getMessage());
		}
	}

	public void sendMessage(SliderMessage message) {
		Log.log("send message: " + message.type + " " + message.toString());
		o.println(message.type + " " + message.toString());
		o.flush();
	}

	public SliderMessage getMessage() {
		
		String message = null;
		try {
			message = this.i.readLine();
			if (message == null) {
				throw new DisconnectException("Connection ended");
			}
		} catch (IOException e) {
			throw new DisconnectException("Connection broke: " + e.getMessage());
		}
		
		Log.log("recv message: " + message);

		switch(message.substring(0, HEADER_LEN)) {
			// variable number of arguments
			case "HIST":
				return new HISTMessage(message.substring(HEADER_LEN+1).split(";"));
			case "PLAY":
				return new PLAYMessage(message.substring(HEADER_LEN+1).split(";"));
			case "GAME":
				return new GAMEMessage(message.substring(HEADER_LEN+1).split(";"));
			case "INIT":
				return new INITMessage(message.substring(HEADER_LEN+1).split(";"));
			case "UPD8":
				return new UPD8Message(message.substring(HEADER_LEN+1).split(";"));
			
			// no arguments
			case "OKAY":
				return new OKAYMessage();
			case "MOVE":
				return new MOVEMessage();

			// one argument
			case "ERRO":
				return new ERROMessage(message.substring(HEADER_LEN+1));
			case "OVER":
				return new OVERMessage(message.substring(HEADER_LEN+1));
		}
		return null;
	}
	
	public void close() {
		try {
			i.close();
			o.close();
			s.close();
		} catch (IOException e) {
			throw new ConnectionException("Failed to close streams: " + e.getMessage());
		}
	}
}

class ConnectionException extends RuntimeException {
	public ConnectionException(String message) {
		super(message);
	}
}
class DisconnectException extends RuntimeException {
	public DisconnectException(String message) {
		super(message);
	}
}

abstract class SliderMessage {
	public String type;
	protected SliderMessage(String type) {
		this.type = type;
	}
	public String toString() {
		return "";
	}
}

class HISTMessage extends SliderMessage {
	public String[] games;
	public HISTMessage(String[] args) {
		super("HIST");
		this.games = args;
	}
	public String toString() {
		String string = "";
		if (this.games.length > 0) {
			string += this.games[0];
		}
		for (int i = 1; i < this.games.length; i++) {
			string += ";" + this.games[i];
		}
		return string;
	}
}

class PLAYMessage extends SliderMessage {
	public int dimension;
	public String passphrase;
	public String name;
	public PLAYMessage(String[] args) {
		super("PLAY");
		this.dimension = Integer.parseInt(args[0]);
		this.passphrase = args[1];
		this.name = args[2];
	}
	public PLAYMessage(int dimension, String passphrase, String name) {
		super("PLAY");
		this.dimension = dimension;
		this.passphrase = passphrase;
		this.name = name;
	}
	public String toString() {
		return this.dimension + ";" + this.passphrase + ";" + this.name;
	}
}

class GAMEMessage extends SliderMessage {
	public String hplayer, vplayer;
	public GAMEMessage(String[] args) {
		super("GAME");
		this.hplayer = args[0];
		this.vplayer = args[1];
	}
	public GAMEMessage(String hplayer, String vplayer) {
		super("GAME");
		this.hplayer = hplayer;
		this.vplayer = vplayer;
	}
	public String toString() {
		return this.hplayer + ";" + this.vplayer;
	}
}

class INITMessage extends SliderMessage {
	public int dimension;
	public String board;
	public char player;
	public INITMessage(String[] args) {
		super("INIT");
		this.dimension = Integer.parseInt(args[0]);
		this.board = "";
		int i = 0;
		for (int row = 0; row < this.dimension; row++) {
			for (int col = 0; col < this.dimension-1; col++) {
				this.board += args[1].charAt(i++) + " ";
			}
			this.board += args[1].charAt(i++) + "\n";
		}
		this.player = args[2].charAt(0);
	}
	public INITMessage(int dimension, String board, char player) {
		super("INIT");
		this.dimension = dimension;
		this.board = board;
		this.player = player;	
	}
	public String toString() {
		return dimension + ";" + board.replaceAll(" ", "").replaceAll("\n", "") + ";" + player;
	}
}

class OKAYMessage extends SliderMessage {
	public OKAYMessage() {
		super("OKAY");
	}
	public String toString() {
		return "";
	}
}

class UPD8Message extends SliderMessage {
	public Move move;
	public UPD8Message(String[] args) {
		super("UPD8");
		if (args.length > 1) {
			int i = Integer.parseInt(args[0]);
			int j = Integer.parseInt(args[1]);
			Move.Direction dir = null;
			switch(args[2]) {
				case "UP": 		dir = Move.Direction.UP; 	break;
				case "DOWN": 	dir = Move.Direction.DOWN; 	break;
				case "LEFT": 	dir = Move.Direction.LEFT; 	break;
				case "RIGHT": 	dir = Move.Direction.RIGHT; break;
			}
			this.move = new Move(i, j, dir);	
		} else {
			this.move = null;
		}
	}
	public UPD8Message(Move move) {
		super("UPD8");
		this.move = move;
	}
	public String toString() {
		if (this.move == null) {
			return "null";
		}
		return this.move.i + ";" + this.move.j + ";" + this.move.d;
	}
}

class MOVEMessage extends SliderMessage {
	public MOVEMessage() {
		super("MOVE");
	}
	public String toString() {
		return "";
	}
}

class ERROMessage extends SliderMessage {
	public String reason;
	public ERROMessage(String arg) {
		super("ERRO");
		this.reason = arg;
	}
	public String toString() {
		return this.reason;
	}
}

class OVERMessage extends SliderMessage {
	public String result;
	public OVERMessage(String arg) {
		super("OVER");
		this.result = arg;
	}
	public String toString() {
		return this.result;
	}
}
