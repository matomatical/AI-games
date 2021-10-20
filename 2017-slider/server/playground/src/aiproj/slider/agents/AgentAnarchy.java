package aiproj.slider.agents;

import java.util.Scanner;
import java.util.Random;
import java.util.ArrayList;

import aiproj.slider.SliderPlayer;
import aiproj.slider.Move;

public class AgentAnarchy implements SliderPlayer {

	protected int n;
	public void init(int dimension, String board, char player) {
		this.n = dimension;

		// don't listen to them!
	}

	public void update(Move move) {
		// ignore what they tell you
	}

	private static Random rng = new Random();
	public Move move() {
		// do what you want
		int i = rng.nextInt(n);
		int j = rng.nextInt(n);
		int dir = rng.nextInt(4);
		Move.Direction d = null;
		switch (dir) {
			case 0: d = Move.Direction.RIGHT; 	break;
			case 1: d = Move.Direction.UP; 		break;
			case 2: d = Move.Direction.LEFT; 	break;
			case 3: d = Move.Direction.DOWN; 	break;
		}

		// not what they tell you to do
		return new Move(i, j, d);
	}
}
