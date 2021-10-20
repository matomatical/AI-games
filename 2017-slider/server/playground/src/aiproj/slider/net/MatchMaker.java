package aiproj.slider.net;

import java.util.HashMap;

class MatchMaker {
	private static HashMap<String, SliderProtocol> pool = new HashMap<String, SliderProtocol>();
	public static synchronized SliderProtocol match(int dimension, String passphrase, SliderProtocol p) {
		
		// cat dimension and passphrase to form unique hash key
		String key = dimension + passphrase;
		
		// is anyone else waiting with this combo?
		if (pool.containsKey(key)) {
			SliderProtocol q = pool.get(key);
			pool.remove(key);
			return q;
		} else {
			pool.put(key, p);
			return null;
		}
	}
}