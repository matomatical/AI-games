"""
Helper module, simplifying configurable-verbosity logging
with uniform formatting accross multiple parts of a program
"""

import sys

class StarLog:
    def __init__(self, level=1, file=sys.stdout, timefn=None,
                star='*', pad='  ', ansi=False):
        self.level = level
        self.timefn = timefn
        self.star = star
        self.pad = pad
        self.kwargs = {"file": file, "flush": True}
        if ansi:
            self.clear = "\033[H\033[2J" # ANSI code to clear the terminal
        else:   
            self.clear = ""

    # log
    def log(self, *args, level=None, depth=0, clear=False, **kwargs):
        """Log a message if warranted by this log's verbosity level setting."""
        # skip messages that are too verbose
        if level is not None and level > self.level:
            return
        # combine the message components
        sep = kwargs.get('sep', ' ')
        msg = sep.join(map(str, args))
        # skip empty messages
        if not msg:
            return
        # output each line of message
        if depth >= 0:
            start = self.star + depth*self.pad
        else:
            start = self.star * (1-depth)
        if clear:
            start = self.clear + start
        if self.timefn is not None:
            start += sep + f"[{self.timefn()}]"
        for line in msg.splitlines():
            print(start, line, **kwargs, **self.kwargs)

    # shortcuts
    def print(self, *args, **kwargs):
        """Shortcut to log at level 0 (always)."""
        self.log(*args, level=0, **kwargs)

    def comment(self, *args, **kwargs):
        """Shortcut to log at level 1 (commentary/info)."""
        self.log(*args, level=1, **kwargs)

    def debug(self, *args, **kwargs):
        """Shortcut to log at level 2 (debug)."""
        self.log(*args, level=2, **kwargs)
