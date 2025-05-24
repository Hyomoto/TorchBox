from logger import Debug, Info, Warning, Error
from constants import Ansi
import os

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
    return last, level, only

def main():
    from game import game
    from game import environment
    print("OKAY")
    return
    while True:
        cmd = input(torchbox.getInput())
        if cmd == "exit":
            break
        elif cmd.startswith("debug"):
            last, level, only = debug(cmd)
            entries = torchbox.logger.filter(level, only)
            if last is not None:
                entries = entries[-int(last):]
            print("\n".join(entries))
        else:
            output, clear = torchbox.update(cmd, environment)
            if clear:
                os.system('cls' if os.name == 'nt' else 'clear')
            print(output)

if __name__ == "__main__":
    main()
