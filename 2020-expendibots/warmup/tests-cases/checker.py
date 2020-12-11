from enum import IntEnum
import os
import os.path
import json
import re
import subprocess

class Color(IntEnum):
    WHITE = 0
    BLACK = 1

class Stack:

    __slots__ = ['num', 'color']

    def __init__(self, num, color):
        self.num = num
        self.color = color

    def clone(self):
        return Stack(self.num, self.color)

class Board:

    def __init__(self, json_file):
        self.board = [[None for x in range(8)] for y in range(8)]
        data = None
        try:
            f = open(json_file)
            data = json.load(f)
            f.close()
        except Exception:
            raise RuntimeError("Unexpected fail loading json")
        for key in ("white", "black"):
            for p in data[key]:
                n, x, y = p
                color = (Color.WHITE if key == "white" else Color.BLACK) 
                # Overkill checks
                if len(p) != 3:
                    raise RuntimeError("Invalid json")
                if n <= 0 or x < 0 or y < 0 or x > 7 or y > 7:
                    raise RuntimeError("Invalid json")
                # Setup
                self._set((x,y), Stack(n, color))

    def debug(self):
        for y in range(7, -1, -1):
            print("  " + "+---"*8 + "+")
            print("{} |".format(y), end='')
            for x in range(8):
                sq = self._get((x,y))
                if sq is None:
                    print('   ',end='')
                elif sq.color == Color.WHITE:
                    print('({})'.format(self._sym(sq.num)),end='')
                elif sq.color == Color.BLACK:
                    print('[{}]'.format(self._sym(sq.num)),end='')
                print('|',end='')
            print()
        print("  " + "+---"*8 + "+")
        print(" ", end='')
        for x in range(8):
            print("   {}".format(x), end='')
        print()

    def is_solved(self):
        for y in range(8):
            for x in range(8):
                sq = self._get((x, y))
                if sq is not None and sq.color == Color.BLACK:
                    return False
        return True

    def _sym(self, n):
        return '0123456789ABC'[n]

    def _check_or_raise(self, coords):
        x, y = coords
        if x < 0 or x > 7 or y < 0 or y > 7:
            raise ValueError("Invalid coordinates")

    def _get(self, coords):
        self._check_or_raise(coords)
        x, y = coords
        return self.board[y][x]

    def _set(self, coords, new):
        self._check_or_raise(coords)
        x, y = coords
        self.board[y][x] = new

    def _get_all_stack_locs(self):
        result = set()
        for y in range(8):
            for x in range(8):
                if self._get((x,y)) is not None:
                    result.add((x,y))
        return result

    def _get_valid_moves(self, coords):
        cur_x, cur_y = coords
        stack = self._get(coords)
        # Stack there?
        if stack is None:
            raise ValueError("No stack")
        # Stack owned by player?
        if stack.color != Color.WHITE:
            raise ValueError("Wrong color")
        n = stack.num
        result = set()
        for x in range(cur_x - n, cur_x + n + 1):
            if 0 <= x <= 7:
                result.add((x, cur_y))
        for y in range(cur_y - n, cur_y + n + 1):
            if 0 <= y <= 7:
                result.add((cur_x, y))
        result -= {i for i in self._get_all_stack_locs() if self._get(i).color == Color.BLACK}
        return result

    def move(self, n, before, after):
        # Before occupied by white stack?
        before_stack = self._get(before)
        if before_stack is None or before_stack.color != Color.WHITE:
            raise ValueError("Bad initial move location")
        # Valid number n?
        if n <= 0 or n > before_stack.num:
            raise ValueError("Invalid number n of tokens to move")
        # Valid move?
        valid_moves = self._get_valid_moves(before)
        if after not in valid_moves:
            raise ValueError("Bad final move location")
        # Ok, let's do it.
        after_stack = before_stack.clone()
        after_stack.num = n
        if self._get(after) is not None:
            after_stack.num += self._get(after).num
        before_stack.num -= n
        # Should not happen - <0 in stack
        if before_stack.num < 0:
            raise RuntimeError("Unexpected < 0 in stack")
        if before_stack.num == 0:
            self._set(before, None)
        else:
            self._set(before, before_stack)
        self._set(after, after_stack)

    def boom(self, coords):
        # Before occupied by white stack?
        before_stack = self._get(coords)
        if before_stack is None or before_stack.color != Color.WHITE:
            raise ValueError("Bad boom location")
        # Ok, let's do it.
        self._boom(coords)

    def _boom(self, coords):
        # Should not happen - no stack at coords
        if self._get(coords) is None:
            raise RuntimeError("Unexpected None at boom location")
        self._set(coords, None)
        cur_x, cur_y = coords
        for x in range(cur_x - 1, cur_x + 2):
            for y in range(cur_y - 1, cur_y + 2):
                if 0 <= x <= 7 and 0 <= y <= 7 and self._get((x, y)) is not None:
                    self._boom((x, y)) 

def check(testcase_f, output):
    # Allow . to stand in for \n
    output = output.replace('.', '\n')
    output = re.sub(r'\n+', '\n', output)
    board = Board(testcase_f)
    # Be as liberal as possible with output
    try:
        for action in output.strip().split('\n'):
            action = action.strip()
            # Allow empty line or comment line
            if action == '' or action[0] == '#':
                continue
            print(action)
            action = re.sub(r'\((\d+),\s+(\d+)\)', r'(\1,\2)', action)
            parts = [p.strip() for p in re.split(r'[^A-Z0-9]+', action)]
            # Sanity checks, then do action
            if parts[0] == 'MOVE':
                n, x_a, y_a, x_b, y_b = [int(x) for x in parts[1:6]]
                board.move(n, (x_a, y_a), (x_b, y_b))
            elif parts[0] == 'BOOM':
                x, y = [int(x) for x in parts[1:3]]
                board.boom((x, y))
            else:
                return (False, "Invalid action (expected [MOVE|BOOM])")
        if board.is_solved():
            return (True, "Well done!")
        else:
            return (False, "Did not clear enemy pieces")
    except ValueError as e:
        return (False, str(e))

"""
Debug
"""
for f in os.listdir('private'):
    output = subprocess.check_output(['python', '../soln/search.py', 'private/{}'.format(f)]).decode()
    print(Board('private/{}'.format(f)).debug())
    print(check('private/{}'.format(f), output))

