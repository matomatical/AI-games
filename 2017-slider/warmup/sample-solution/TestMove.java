package com.unimelb.ai2017.slider;

import java.util.Scanner;
import java.util.ArrayList;

class TestMove {
	public static void main(String[] args) {
		
		// suze of problem?
		Scanner s = new Scanner(System.in);
		int n = s.nextInt();
		
		// data structures
		Piece[][] grid = new Piece[n][n];
		ArrayList<Piece> hs = new ArrayList<>();
		ArrayList<Piece> vs = new ArrayList<>();
		
		// scan the board
		for (int i = n-1; i >= 0; i--) {
			for (int j = 0; j < n; j++) {
				grid[i][j] = new Piece(s.next(), i, j);
				if (grid[i][j].type == Piece.Type.H) {
					hs.add(grid[i][j]);
				} else if (grid[i][j].type == Piece.Type.V) {
					vs.add(grid[i][j]);
				}
			}
		}

		// count legal moves
		int numLegalHMoves = 0;
		for (Piece h : hs) {
			if (h.i+1 < n && grid[h.i+1][h.j].type == Piece.Type.E) {
				numLegalHMoves++;
			}
			if (h.i > 0 && grid[h.i-1][h.j].type == Piece.Type.E) {
				numLegalHMoves++;
			}
			if (h.j+1 >= n || grid[h.i][h.j+1].type == Piece.Type.E) {
				numLegalHMoves++;
			}
		}
		int numLegalVMoves = 0;
		for (Piece v : vs) {
			if (v.j+1 < n && grid[v.i][v.j+1].type == Piece.Type.E) {
				numLegalVMoves++;
			}
			if (v.j > 0 && grid[v.i][v.j-1].type == Piece.Type.E) {
				numLegalVMoves++;
			}
			if (v.i+1 >= n || grid[v.i+1][v.j].type == Piece.Type.E) {
				numLegalVMoves++;
			}
		}

		// and print output
		System.out.println(numLegalHMoves);
		System.out.println(numLegalVMoves);
	}
}