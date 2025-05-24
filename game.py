from torchbox import TorchBox
from tinder import tinder
from constants import Macro, Crucible
from logger import Debug
import random

def get_file(path: str):
    with open(path, "r") as f:
        return f.read()

def api_random_number( start: int, end: int):
    return random.randint(int(start), int(end))

# protected system global functions and constants
protected = Crucible({
    "NAME": "Sock & Sorcery",
    "VERSION": "0.1",
    "random": api_random_number
}, protected=True)

# global environment, accessible to all scenes but
# new values can not be added and mutation is restricted
# to maintaining type
environment = Crucible({
    "OUTPUT": "",
    "INPUT": "",
}, parent = protected)

macros = Crucible({
    "prog_name": Macro("NAME"),
    "version": Macro("VERSION"),
    "player": Macro("PLAYER.name"),
    "var": Macro("")
})

# redirect the standard input/output keywords
tinder.macro("write", "write", ".OUTPUT %s")
tinder.macro("input", "input", ".INPUT %s")

# build the game from torchbox
class Game(TorchBox):
    def __init__(self, startAt: str, errorLevel = Debug):
        super().__init__(protected.get("NAME"), macros, errorLevel = errorLevel, first = startAt)

# import tinderboxes to the game
game = Game("battle")
game["battle"] = tinder.compile(get_file("battle.scr"))

# debug testing
line = 0
script = game["battle"]
local = tinder.makeLocalEnvironment(script, environment)
count = 0

while line < len(script):
    try:
        line = script.run(line, local)
    except Exception as e:
        raise e
    print(local.get("OUTPUT"))
    cmd = input(local.get("INPUT"))
    local.set("INPUT", cmd)
    local.set("OUTPUT", "")

print(local.variables)
print(environment.variables)
print(protected.variables)