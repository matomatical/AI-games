package aiproj.slider.net;

import java.util.LinkedList;

class MatchHistory {
	private static final int MAX_GAMES = 10;
	private static LinkedList<String> games = new LinkedList<String>();
	public static synchronized String[] getGames() {
		String[] games = new String[MatchHistory.games.size()];
		int i = 0;
		for (String game : MatchHistory.games) {
			games[i++] = game;
		}
		return games;
	}

	public static synchronized void logGame(String game) {
		if (games.size() >= MAX_GAMES) {
			games.remove();
		}
		games.add(game);
	}
}