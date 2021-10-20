package aiproj.slider.net;

public class Log {
	public static boolean logging = false;
	public static void log(String msg){
		if (logging) {
			long t = Thread.currentThread().getId();
			System.out.println("thread " + t + ": " + msg);
			System.out.flush();
		}
	}
	public static void error(String msg){
		if (logging) {
			long t = Thread.currentThread().getId();
			System.err.println("thread " + t + ": " + msg);
			System.err.flush();
		}
	}
}
