import re
import sys
import json

def main():
    try:
        with open(sys.argv[1]) as data_file:
            data_text = data_file.read()
        with open(sys.argv[2]) as soln_file:
            soln_text = soln_file.read()
    except (IndexError, FileNotFoundError):
        print("usage: python3 check INPUT.json OUTPUT.txt", file=sys.stderr)
        sys.exit(1)
    try:
        check(data_text, soln_text, verbose=True)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(2)

def check(data_text, soln_text, verbose=False):
    # read the solution text
    soln = Soln(parse(soln_text.splitlines()))
    # load the board state
    board = Board(json.loads(data_text))
    if verbose: board.print("initial board from data file:")
    for actions in soln:
        # TODO: Add turn number to errors?
        board.update(actions)
        if verbose: board.print(f"after {actions}:")
    if not board.iscomplete():
        raise Exception("Invalid solution (enemy tokens remain at end)")

LINE_RE = re.compile(
        r"Turn (?P<n>\d+):\s*"
        r"(?P<action>\w+)\s*from\s*\("
            r"\s*(?P<ra>-?\d+),"
            r"\s*(?P<qa>-?\d+)"
        r"\)\s*to\s*\("
            r"\s*(?P<rb>-?\d+),"
            r"\s*(?P<qb>-?\d+)"
        r"\)"
    )
def parse(lines):
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = LINE_RE.match(line)
        if match is None:
            raise Exception(f"Invalid format (failed to parse line {line!r})")
        yield match.groupdict()
    # TODO: might should be able to get away with 'matchall' on full file
    # for cases with linebreak issues...? see how we go!

class Soln:
    def __init__(self, soln):
        self.steps = {}
        for step in soln:
            # validate data within step
            n = int(step['n'])
            assert (n >= 0), f"Invalid turn number ({n})"
            a = step['action'].upper()
            assert a == "SLIDE" or a == "SWING", f"Invalid action type ({a})"
            ra, qa, rb, qb = [int(step[k]) for k in ["ra","qa","rb","qb"]]
            for i in ra, qa, rb, qb:
                assert i in range(-4, +4+1), f"Invalid hex coordinate ({i})"
            if n not in self.steps:
                self.steps[n] = []
            self.steps[n].append((a, (ra, qa), (rb, qb)))
        # validate step sequence
        # NOTE: disregarding order and contiguity
        self.sequence = []
        for n in sorted(self.steps.keys()):
            self.sequence.append(self.steps[n])
    def __iter__(self):
        return iter(self.sequence)

class Board:
    def __init__(self, data):
        # keep track of where the tokens are
        self.tokens  = [((r, q), s) for s, r, q in data["upper"]]
        self.targets = [((r, q), s) for s, r, q in data["lower"]]
        # keep track of where the tokens are allowed to go
        ran = range(-4, +4+1)
        blocks = {(r, q) for _s, r, q in data["block"]}
        hexes = {(r, q) for r in ran for q in ran if -r-q in ran}
        self.hexes = hexes - blocks

    def iscomplete(self):
        return self.targets == []

    def update(self, actions):
        # validate that the game is still ongoing
        assert not self.iscomplete(), "Invalid turn (game already over)"

        # validate that each move is from a hex with a token,
        # and that each token gets exactly one move
        token_hexes = sorted([x for x, _s in self.tokens])
        action_hexes = sorted([x for _a, x, _y in actions])
        assert sorted(token_hexes) == sorted(action_hexes), \
            f"Invalid actions (remaining tokens at {token_hexes}, " \
            f"suggested actions from {action_hexes})"

        # validate that each action is valid according to the rules
        valid_actions = set(_valid_actions(set(token_hexes), self.hexes))
        for action in actions:
            assert action in valid_actions, f"Invalid action ({action})"

        # perform the moves
        new_tokens = []
        for _a, x, y in actions:
            # lookup the symbol (any will do, since all tokens on the
            # hex will have the same symbol after battles resolve)
            symbol = [s for x_, s in self.tokens if x_ == x][0]
            new_tokens.append((y, symbol))
        self.tokens = new_tokens

        # let the tokens fight eachother and enemies (simultaneously),
        # updating the state
        surviving_tokens  = []
        surviving_targets = []
        for x in self.hexes:
            ups = [t for t in self.tokens  if t[0] == x]
            los = [t for t in self.targets if t[0] == x] 
            symbols = {s for _x, s in ups + los}
            for s in symbols:
                # remove symbols defeated by this
                ups = [t for t in ups if t[1] != _DEFEAT_MAP[s]]
                los = [t for t in los if t[1] != _DEFEAT_MAP[s]]
            surviving_tokens.extend(ups)
            surviving_targets.extend(los)
        self.tokens = surviving_tokens
        self.targets = surviving_targets

        # TODO:
        # if there are still targets, check that there are still enough
        # tokens to defeat them. (NOTE: This is somewhere the students
        # will have to be careful, but this script doesn't have to check
        # it explicitly, because it is covered by the fact that no action
        # is possible after all tokens are removed).

    def print(self, message):
        template = """# {00:}
#              .-'-._.-'-._.-'-._.-'-._.-'-.
#             |{57:}|{58:}|{59:}|{60:}|{61:}|
#           .-'-._.-'-._.-'-._.-'-._.-'-._.-'-.
#          |{51:}|{52:}|{53:}|{54:}|{55:}|{56:}|
#        .-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-.
#       |{44:}|{45:}|{46:}|{47:}|{48:}|{49:}|{50:}|
#     .-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-.
#    |{36:}|{37:}|{38:}|{39:}|{40:}|{41:}|{42:}|{43:}|
#  .-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-.
# |{27:}|{28:}|{29:}|{30:}|{31:}|{32:}|{33:}|{34:}|{35:}|
# '-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'
#    |{19:}|{20:}|{21:}|{22:}|{23:}|{24:}|{25:}|{26:}|
#    '-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'
#       |{12:}|{13:}|{14:}|{15:}|{16:}|{17:}|{18:}|
#       '-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'
#          |{06:}|{07:}|{08:}|{09:}|{10:}|{11:}|
#          '-._.-'-._.-'-._.-'-._.-'-._.-'-._.-'
#             |{01:}|{02:}|{03:}|{04:}|{05:}|
#             '-._.-'-._.-'-._.-'-._.-'-._.-'"""
        import collections
        board = collections.defaultdict(str)
        for x, s in self.tokens:
            board[x] += s.upper()
        for x, s in self.targets:
            board[x] += s.lower()
        ran = range(-4, +4+1)
        cells = []
        for x in [(r,q) for r in ran for q in ran if -r-q in ran]:
            if x in self.hexes:
                cell = board[x].center(5)
            else:
                cell = "BLOCK"
            cells.append(cell)
        print(template.format(message, *cells))

_DEFEAT_MAP = {
    'r': 's',
    'p': 'r',
    's': 'p',
}

def _valid_actions(token_hexes, valid_hexes):
    for x in token_hexes:
        adjacent_x = _adjacent(x) & valid_hexes
        for y in adjacent_x:
            yield "SLIDE", x, y
            if y in token_hexes:
                opposite_y = valid_hexes & _adjacent(y) - adjacent_x - {x}
                for z in opposite_y:
                    yield "SWING", x, z

def _adjacent(x):
    r, q = x
    return {
            (r+1, q-1),
            (r+1, q+0),
            (r+0, q+1),
            (r-1, q+1),
            (r-1, q+0),
            (r+0, q-1),
        }

if __name__ == "__main__":
    main()

