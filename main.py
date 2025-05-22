from torchbox import TorchBox, Macro, MacroLookup
from test import Debug, Info, Warning, Error
from canvas import Ansi
import sys

torchbox = TorchBox()

def debug(cmd):
    tokens = cmd.split()
    last = None
    level = Debug
    only = False
    for token in tokens[1:]:
        if token == "debug":
            level = Debug
        elif token == "info":
            level = Info
        elif token == "warning":
            level = Warning
        elif token == "error":
            level = Error
        elif token == "only":
            only = True
        else:
            try:
                last = abs(float(token))
            except ValueError:
                continue
    entries = torchbox.logger.filter(level, only)
    if last is not None:
        entries = entries[-int(last):]
    torchbox.write("\n".join(entries), wrap=False)

def main():
    from scenes import intro
    torchbox.setScene(intro.get("creation"))
    while True:
        torchbox.clear()
        torchbox.render()
        cmd = torchbox.input()
        if cmd == "exit":
            break
        if cmd.startswith("debug"):
            debug(cmd)
            continue
        torchbox.tokens(cmd)
    print(Ansi.RESET)

if __name__ == "__main__":
    main()
