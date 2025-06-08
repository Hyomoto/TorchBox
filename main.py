from game import instantiate_game, userMemory
from tinder.crucible import Crucible, NO_SHADOWING
from torchbox import Message, ConnectionHandler, Shutdown
from constants import RESET
import copy

class LocalUser(ConnectionHandler):
    def __init__(self, queue, logger):
        super().__init__(None, queue, logger)
        env = Crucible(NO_SHADOWING).update(copy.copy(userMemory))
        env["SCENE"] = "login"
        self.userEnv = env
        self.localEnv = None
        self.change = True

    def login(self):
        self.queue.put(Message(self, "__LOGIN__"))

    def receive(self):
        pass

    def send(self, output: str, _input = None):
        print(output)
        _input = input((_input if _input else "") + " ")
        self.queue.put(Message(self, _input))

    def close(self):
        raise Shutdown()

    def __repr__(self):
        return f"<LocalUser>"

def debug():
    torchbox = instantiate_game(debug = True)
    torchbox.compile("./scripts/coin.v2.tinder")
    local = LocalUser(torchbox.queue, torchbox.log)
    local.userEnv["SCENE"] = "coin"
    local.login()
    torchbox.run()
    print(RESET)

def main():
    torchbox = instantiate_game()
    local = LocalUser(torchbox.queue, torchbox.log)
    local.login()
    torchbox.run()
    print(RESET)

if __name__ == "__main__":
    debug()
