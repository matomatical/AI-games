package aiproj.slider.net;

import java.io.IOException;

import aiproj.slider.Move;
import aiproj.slider.SliderPlayer;

public class RemotePlayer implements SliderPlayer {
	SliderProtocol p;
	public RemotePlayer(SliderProtocol p) {
		this.p = p;
	}

	public void init(int dimension, String board, char player) throws DisconnectException {
		INITMessage init = new INITMessage(dimension, board, player);
		p.sendMessage(init);

		// wait for OKAY message reply
		OKAYMessage okay = (OKAYMessage)p.getMessage();
	}

	public void update(Move move) {
		UPD8Message upd8 = new UPD8Message(move);
		p.sendMessage(upd8);

		// wait for OKAY message reply
		OKAYMessage okay = (OKAYMessage)p.getMessage();
	}

	public Move move() {
		MOVEMessage requestMove = new MOVEMessage();
		p.sendMessage(requestMove);

		// wait for move to come back
		UPD8Message upd8 = (UPD8Message)p.getMessage();
		return upd8.move;
	}
}