from typing import Optional
from game import Game, instantiate_game, start_server, Scene, SocketUser
from tinder.crucible import Crucible, NO_SHADOWING
from torchbox import Message, ConnectionHandler, Shutdown
from constants import RESET
import copy

getInput = input

class LocalUser(SocketUser):
    def login(self):
        self.queue.put(Message(self, "__LOGIN__", "login"))

    def receive(self):
        pass

    def send(self, output: str, input: Optional[str] = None):
        print(output)
        input = getInput((input if input else "") + " ")
        self.queue.put(Message(self, input))

    def close(self, output: Optional[str] = None):
        if output:
            print(output)
        raise Shutdown("Close called on LocalUser.")

    def __repr__(self):
        return "<LocalUser>"

def debug():
    path = ""
    #path = "home/start.v2.tinder"
    torchbox: Game = instantiate_game(path, debug = True)
    player = LocalUser(None, torchbox.queue, torchbox.log)
    #print( torchbox.scenes["home/start"])
    #exit()
    player.environment["STACK"] = [(0,"login/faststart",None)]
    player.login()
    torchbox.run()
    print(RESET)

def server():
    torchbox: Game = instantiate_game()
    start_server(torchbox)
    print(RESET)

def main():
    torchbox: Game = instantiate_game()
    local = LocalUser(None, torchbox.queue, torchbox.log)
    local.login()
    torchbox.run()
    print(RESET)

if __name__ == "__main__":
    debug()
