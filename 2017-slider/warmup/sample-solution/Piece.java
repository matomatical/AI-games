package com.unimelb.ai2017.slider;

public class Piece {
	public enum Type { H, V, B, E }
	public final Type type;
	public final int i, j;
	public Piece(String t, int i, int j) {
		this.type = fromString(t);
		this.i = i;
		this.j = j;
	}
	private static Type fromString(String t) {
		if (t.equals("+")) {
			return Type.E;
		} else if (t.equals("H")) {
			return Type.H;
		} else if (t.equals("V")) {
			return Type.V;
		} else if (t.equals("B")) {
			return Type.B;
		} else {
			throw new RuntimeException("unknown type: " + t);
		}
	}
}