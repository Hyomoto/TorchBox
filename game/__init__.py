from typing import List, Tuple, Callable, Optional
from torchbox import TorchBox, Ember, ConnectionHandler, SocketHandler, Shutdown
from torchbox.realm import Realm, User
from firestarter import FirestarterError
from tinder import Tinderstarter, Tinder, Kindling, TinderBurn
from tinder import Imported, Jumped, Yielded, Returned, Halted
from tinder.crucible import Crucible, PROTECTED, READ_ONLY, NO_SHADOWING
from torchbox.api import PermissionHolder, API
from torchbox.logger import Logger, Log, Critical, Warning, Info, Debug
from constants import RESET
from .memory.protected import map as protectedMemory
from .memory.globals import map as globalMemory
from .memory.user import map as userMemory, classes as user_classes
from .apis import import_api, BaseAPI
from pathlib import Path
from constants import Ansi
import threading
import queue
import socket
import copy
import time
import os

QueueEmpty = queue.Empty

SAVE_FILE = "./saves/socks.json"
classes = {}
classes.update(user_classes())

def get_file(path: str):
    with open(path, "r") as f:
        return f.read()

class Scene(Tinder, PermissionHolder):
    def __init__(self, instructions: List[Tuple[int, Kindling]], permissions: Optional[List[str]] = None):
        super().__init__(instructions=instructions, permissions=permissions)
    def __repr__(self):
        list = '\n\t'.join(repr(inst) for inst in self.instructions)
        return f"Scene[lines={len(self)}, permissions={self.permissions}](\n\t{list}\n)"

def getAllScripts():
    scripts = []
    for root, _, files in os.walk("./game/scripts"):
        for file in files:
            if file.endswith(".tinder"):
                scripts.append(os.path.join(root, file))
    return scripts

def parse(env: Crucible, value: str):
    pass

tinderstarter = Tinderstarter(Scene)

class SocketUser(SocketHandler):
    def __init__(self, client: socket.socket, queue: queue.Queue, logger: Optional[Callable] = None):
        super().__init__(client, queue, logger)
        env = Crucible(NO_SHADOWING).update(copy.copy(userMemory))
        env["STACK"].append((0, "login", None))  # Initialize with a login scene
        self.environment = env

class Game(TorchBox):
    def __init__(self, realm: Realm, env: Crucible):
        super().__init__(realm, env, Logger(length = 255, output="./logs/torchbox.log"))
        self.scenes = {}
        # build the memory environment
        self.baseApi = BaseAPI(self)
        self.shared = Crucible(PROTECTED, parent=env).update(globalMemory).update(self.baseApi.export())
        print(self.shared.variables)
        self.apis: dict[str, API] = import_api(self, exclude=["BaseAPI"])
        self.log(Info(f"{len(self.apis)} APIs loaded: {Ansi.RESET}{', '.join(self.apis.keys())}", "🔌"))
        self.player: SocketUser = None
        self.env = None
        self.running = True
        self.debug = False
        self.log(Info("Game initialized.", "🕹️ "))

    def run(self):
        def gameLoop():
            def scriptLoop(scene: str, script: Scene, user: Crucible, local: Crucible):
                """
                The script loop is how scripts interact with the engine, thus we continue until
                it finishes, a escaping control exception is called, or an error occurs.
                """
                nonlocal line, lastline
                while True:
                    try:
                        line = script.run(line, local)
                    except Imported as e:
                        if e.library not in self.apis:
                            raise TinderBurn(f"Library '{e.library}' not found.")
                        lib = self.apis.get(e.library)
                        if not lib.hasPermission(script):
                            raise TinderBurn(f"Library '{e.library}' cannot be imported in this context.")
                        if e.request:
                            local.update(lib.export(e.request))
                        else:
                            local[e.name or e.library] = lib.export()
                        line = e.line + 1
                        continue

                    except Jumped as e:
                        lastline = e.last + 1
                        line = e.line + 1
                        continue

                    except Returned:
                        line = lastline
                        continue

                    except Halted as e:
                        user['STACK'] = []
                        break

                    except Yielded as e:
                        line = e.line + 1
                        if e.carry:
                            user["STACK"][-1][2].update(e.carry)
                        break
                    break

            queue = self.queue
            lastline = 0
            while self.running:
                try:
                    message = queue.get(timeout=1) # blocking
                    player: SocketUser = message.user
                    self.player = player # keep reference to the player
                    user: Crucible = player.environment

                    if message.type == "login":
                        user.parent = self.shared
                    
                    stack: list[Tuple[int, str, Crucible]] = user["STACK"]

                    while True:
                        if stack[-1][2] is None:
                            # If the scope is not set, we need to set it up
                            scene = stack[-1][1]
                            script = self.get(scene)
                            if not script:
                                raise TinderBurn(f"Scene '{scene}' not found.")
                            local = Crucible(NO_SHADOWING, parent=user) # initialize new local scope
                            user["STACK"] = [(0, scene, local)]
                            stack = user["STACK"]
                            script.writeJumpTable(local)
                        
                        depth = len(stack) - 1
                        lastline, script, local = stack[-1]
                        line = lastline
                        scene: Scene = self.get(script) # type: ignore
                        local.parent = user
                        self.env = local
                        try:
                            user["INPUT"] = message.content.lower()
                            scriptLoop(script, scene, user, local)
                            # this is to clean up changes in local variables that may have been made
                            # by the script, we look up the user scope, and rebind the local in case
                            # the user has changed, and update the stack for the same reason
                            user = player.environment
                            local.parent = user
                            
                            if depth < len(stack):
                                _, scr, lo = stack[depth]
                                stack[depth] = (line, scr, lo) # update stack with new line

                            output = self.substitute(user["OUTPUT"].replace("\\n", "\n"))
                            input = self.substitute(user["INPUT"].replace("\\n", "\n"))
                            
                            # check if scene changed, if so continue
                            if stack and stack[-1][1] != script:
                                user["OUTPUT"] = output
                                user["INPUT"] = input
                                continue
                            
                            user["OUTPUT"] = ""
        
                            if not user["STACK"]:
                                player.close(output)
                            else:
                                player.send(output, input)
                        except Shutdown:
                            self.log(Info("Server shutting down...", "🛑"))
                            self.running = False
                            break
                        except TinderBurn as e:
                            error = f"Error in scene '{script}': {e}"
                            self.log(Warning(error))
                            player.send(error + "\n")
                            player.close() # close the connection on error
                            raise e
                        except EOFError:
                            break
                        break
    
                except QueueEmpty:
                    continue

        threading.Thread(target=gameLoop).start()
        try:
            while self.running:
                time.sleep(1)
        except Shutdown:
            print('\n')
            self.log(Info("Server shutting down...", "🛑"))
            self.running = False
        except KeyboardInterrupt:
            print('\n')
            self.log(Info("Server shutting down due to KeyboardInterrupt.", "⌨️ "))
            self.running = False
        except Exception as e:
            print('\n')
            self.log(Critical("Unhandled exception, shutting down server."))
            self.log(Critical(f"{e.__class__.__name__}: {e}"))
        finally:
            self.realm.save(SAVE_FILE)
            self.logger.write(clear=True)

    def getHandler(self, client, of: str) -> ConnectionHandler:
        match of:
            case "socket":
                return SocketUser(client, self.queue, self.log)
        return super().getHandler(client, of)

    def compile(self, filepath: str) -> Scene:
        """Compile a script and add it to the game."""
        keyname, filename = os.path.split(filepath)
        filename = filename.split(".")
        keyname = os.path.normpath(keyname).replace("\\", "/").removeprefix("game/scripts")
        keyname = keyname.removeprefix("/")
        keyname += "/" if keyname else ""
        version = filename[-2]
        script = get_file(filepath)
        try:
            tinder = tinderstarter.compile(script, version)
        except FirestarterError as e:
            raise Ember(f"Error compiling '{filepath}':\n{e}")
        #print(tinder)
        self.add(keyname + filename[0], tinder)
        return tinder

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
    game = Game(None, Crucible(READ_ONLY).update(protectedMemory))
    if os.path.exists(SAVE_FILE):
        game.log(Info(f"Loading realm from {Ansi.BLUE}{SAVE_FILE}{Ansi.RESET}...", "💽", Ansi.WHITE))
        realm = Realm.load(SAVE_FILE, classes=classes)
    else:
        game.log(Info("Creating new realm...", "🛠️", Ansi.WHITE))
        realm = Realm("Socks & Sorcery", "A realm for Socks & Sorcery users.")
        realm.addUser(User("admin", "default"))
    game.realm = realm
    game.log(Info("Starting TorchBox server...", "🔥"))
    game.log(Info(f"Realm: {Ansi.GREEN}{realm.name}{Ansi.RESET}", f"🏰", Ansi.WHITE))
    game.debug = debug
    if not debug:
        permissions = []
        for api in game.apis.values():
            if api.permissions:
                permissions.extend(api.permissions)
        scripts = getAllScripts()
        game.log(Info(f"Found {len(scripts)} scripts.", "📜"))
        count = 0
        game.logger.show = False
        for script in scripts:
            try:
                # grab start of path up until first /
                scene = game.compile(script)
                path = Path(script).parts
                if len(path) > 3 and path[2] in permissions:
                    scene.permissions = [path[2]]
                count += 1
            except (Ember, TinderBurn) as e:
                text = str(Warning(f"Error compiling '{script}': {Ansi.RESET}{e}"))
                print(text)
                game.log(Warning(e))
        game.logger.show = True
        game.log(Info(f"Compiled {count} scripts.", "  "))
        game.log(Info("Server is ready to accept connections.", "  ", Ansi.WHITE))
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
