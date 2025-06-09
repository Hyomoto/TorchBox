from typing import Tuple, Callable, Optional
from torchbox import TorchBox, Ember, ConnectionHandler, SocketHandler, Shutdown
from torchbox.realm import Realm, User
from firestarter import FirestarterError
from tinder import Tinderstarter, Tinder, TinderBurn, JumpTo, Yield, ReturnTo
from tinder.crucible import Crucible, PROTECTED, READ_ONLY, NO_SHADOWING
from torchbox.logger import Logger, Log, Critical, Warning, Info, Debug
from constants import RESET
from memory.protected import map as protectedMemory
from memory.globals import map as globalMemory
from memory.user import map as userMemory
from memory.user import UserData
import random
import threading
import queue
import socket
import copy
import time
import os

QueueEmpty = queue.Empty

def get_file(path: str):
    with open(path, "r") as f:
        return f.read()

realm = Realm("Socks & Sorcery Realm", "A realm for Socks & Sorcery users.")
user = realm.addUser(User("admin", "default"))

tinderstarter = Tinderstarter()

def get_user(username: str):
    try:
        return realm.getUser(username)
    except Exception as e:
        return None

loginAPI = {
    "find_user": get_user,
    "check_password": lambda user, password: user.checkPassword(password),
    "set_password": lambda user, password: user.setPassword(password),
    "set_nickname": lambda user, nickname: user.setNickname(nickname),
    "new_user": lambda username, password: realm.addUser(User(username, password, UserData())),
}
randomAPI = {
    "randint": lambda a, b: random.randint(a, b),
    "random": lambda: random.random(),
    "choice": lambda x: random.choice(x),
    "shuffle": lambda x: random.shuffle(x),
}
baseApi = {
    "random" : randomAPI,
    "debug" : lambda x: print(f"[debug] {x}"),
    "length" : lambda x: len(x),
}
protectedMemory.update({"login" : loginAPI})
protectedMemory.update(baseApi)

def getAllScripts():
    scripts = []
    for root, _, files in os.walk("./scripts"):
        for file in files:
            if file.endswith(".tinder"):
                scripts.append(os.path.join(root, file))
    return scripts

class SocketUser(SocketHandler):
    def __init__(self, client: socket.socket, queue: queue.Queue, logger: Callable = None):
        super().__init__(client, queue, logger)
        env = Crucible(NO_SHADOWING).update(copy.copy(userMemory))
        env["SCENE"] = "login"
        self.userEnv = env
        self.localEnv = None
        self.change = True

class Game(TorchBox):
    def __init__(self, realm: Realm, env: Crucible):
        super().__init__(realm, env, Logger(length = 255, output="./logs/torchbox.log"))
        self.scenes = {}
        # build the memory environment
        self.shared = Crucible(PROTECTED, parent=Crucible(READ_ONLY).update(protectedMemory)).update(globalMemory)
        self.env = None
        self.running = True
        self.debug = False

    def run(self):
        def gameLoop():
            queue = self.queue
            while self.running:
                try:
                    message = queue.get(timeout=1) # blocking
                    while True:
                        user: SocketUser = message.user
                        scene = user.userEnv["SCENE"]
                        script = self.get(scene)
                        env = user.userEnv
                        if user.change:
                            lastline = 0
                            user.change = False
                            env.parent = self.shared
                            if not user.localEnv or "SAVE_LOCAL" not in user.localEnv:
                                user.localEnv = Crucible(NO_SHADOWING, parent=user.userEnv)
                            env["LINE"] = 0
                            script.writeJumpTable(user.localEnv)
                        env["INPUT"] = message.content
                        line = env["LINE"]
                        while True:
                            try:
                                line = script.run(line, user.localEnv)
                            except JumpTo as e:
                                print(f"Jumping to line {script.instructions[e.line][0]}")
                                lastline = e.last + 1
                                line = e.line + 1
                                continue
                            except ReturnTo:
                                print(f"Returning to line {script.instructions[lastline][0]}")
                                line = lastline
                                continue
                            except Yield as e:
                                line = e.line + 1
                            break # exit the inner loop
                        self.env = user.localEnv
                        output = self.substitute(env["OUTPUT"].replace("\\n", "\n"))
                        if env["SCENE"] == "exit":
                            user.send(output)
                            user.close()
                        input = self.substitute(env["INPUT"].replace("\\n", "\n"))
                        env["OUTPUT"] = ""
                        env["LINE"] = line
                        if env["SCENE"] != scene:
                            user.change = True
                            continue
                        user.send(output, input)
                        break
                except (Shutdown, EOFError):
                    self.running = False
                except TinderBurn as e:
                    error = f"Error in scene '{user.userEnv['SCENE']}': {e}"
                    self.log(Warning(error))
                    user.send(error + "\n")
                    user.close() # close the connection on error
                except QueueEmpty:
                    continue
                except Exception as e:
                    self.log(Critical(f"{e.__class__.__name__}: {e}"))
                    self.log(Critical("Unhandled exception, shutting down server."))
                    self.running = False
                    raise e
        
        threading.Thread(target=gameLoop).start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print("\n")
            self.log(Info("Server shutting down due to KeyboardInterrupt."))
        self.logger.write(clear=True)

    def getHandler(self, client, of: str) -> ConnectionHandler:
        match of:
            case "socket":
                return SocketUser(client, self.queue, self.log)
        super().getHandler(client, of)

    def compile(self, filepath: str):
        """Compile a script and add it to the game."""
        keyname, filename = os.path.split(filepath)
        filename = filename.split(".")
        keyname = os.path.normpath(keyname).replace("\\", "/").removeprefix("scripts")
        keyname = keyname.removeprefix("/")
        keyname += "/" if keyname else ""
        version = filename[-2]
        script = get_file(filepath)
        try:
            tinder = tinderstarter.compile(script, version)
        except FirestarterError as e:
            raise Ember(f"Error compiling '{filepath}':\n{e}")
        print(tinder)
        self.add(keyname + filename[0], tinder)
    
    def add(self, name: str, scene: Tinder):
        self.scenes[name] = scene
        return self

    def get(self, name: str):
        if name in self.scenes:
            return self.scenes[name]
        raise ValueError(f"Tinder '{name}' not found.")

def instantiate_game(debug: bool = False):
    """
    Instantiate the game, compile all scripts, and return the game instance.
    
    If debug is True, script compilation is skipped.
    """
    game = Game(realm, protectedMemory)
    game.debug = debug
    if not debug:
        scripts = getAllScripts()
        game.log(Info(f"Found {len(scripts)} scripts."))
        count = 0
        game.logger.show = False
        for script in scripts:
            try:
                game.compile(script)
                count += 1
            except Ember as e:
                text = str(Warning(e))
                print(f"{text[:text.index(":")]}{RESET}")
                game.log(Warning(e))
        game.logger.show = True
        game.log(Info(f"Compiled {count} scripts."))
    return game

def start_server(torchbox: TorchBox):
    torchbox.listen()
    try:
        torchbox.run()
    except Exception:
        torchbox.logger.log(Critical("Unhandled exception, shutting down server."))
        torchbox.logger.write(clear=True)
        exit(1)
    
if __name__ == "__main__":
    try:
        game = instantiate_game()
    except Ember as e:
        print(e)
        exit(1)
    start_server(game)
    
    #game.run("login")