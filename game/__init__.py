from typing import Dict, List, Tuple, Callable, Optional
from torchbox import TorchBox, Ember, ConnectionHandler, SocketHandler, Shutdown
from torchbox.realm import Realm, User
from firestarter import FirestarterError
from tinder import Tinderstarter, Tinder, Kindling, TinderBurn
from tinder import Imported, Yielded, Halted
from tinder.crucible import Crucible, PROTECTED, READ_ONLY, NO_SHADOWING
from tinder.library import Library
from torchbox.logger import Logger, Log, Critical, Warning, Info, Debug
from mixins.permissions import PermissionHolder
from constants import RESET
from .memory.protected import map as protectedMemory
from .memory.globals import map as globalMemory
from .memory.user import map as userMemory, classes as user_classes
from .libraries import import_libraries, BaseLibrary
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

def get_scripts(path: str = ""):
    path = "./game/scripts/" + path
    scripts = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".tinder"):
                    scripts.append(os.path.join(root, file))
    elif os.path.isfile(path) and path.endswith(".tinder"):
        scripts.append(path)
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
    def __init__(self, env: Crucible):
        super().__init__(None, env, Logger(length = 255, output="./logs/torchbox.log"))
        self.scenes = {}
        # build the memory environment
        self.shared = Crucible(PROTECTED, parent=env).update(globalMemory)
        self.libraries: Dict[str, Library] | None = None
        self.player: SocketUser = None
        self.env = None
        self.running = True
        self.debug = False

    def run(self):
        def gameLoop():
            def scriptLoop(scene: str, script: Scene, user: Crucible, local: Crucible):
                """
                The script loop is how scripts interact with the engine, thus we continue until
                it finishes, a escaping control exception is called, or an error occurs.
                """
                while True:
                    try:
                        script.run(local)
                    except Imported as e:
                        if e.library not in self.libraries:
                            raise TinderBurn(f"Library '{e.library}' not found.")
                        lib = self.libraries.get(e.library)
                        if not lib.hasPermission(script):
                            raise TinderBurn(f"Library '{e.library}' cannot be imported in this context.")
                        if e.request:
                            local.update(lib.export(e.request))
                        else:
                            local[e.name or e.library] = lib.export()
                        continue
                    
                    except Halted as e:
                        user['STACK'] = []
                        break

                    except Yielded as e:
                        if e.carry:
                            user["STACK"][-1][1].update(e.carry)
                        break
                    break

            queue = self.queue
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
                        if stack[-1][1] is None:
                            # If the scope is not set, we need to set it up
                            scene = stack[-1][0]
                            script = self.get(scene)
                            if not script:
                                raise TinderBurn(f"Scene '{scene}' not found.")
                            local = Crucible(NO_SHADOWING, parent=user) # initialize new local scope
                            user["STACK"] = [(scene, local)]
                            stack = user["STACK"]
                            script.writeJumpTable(local)
                        
                        depth = len(stack) - 1
                        script, local = stack[-1]
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
                                scr, lo = stack[depth]
                                stack[depth] = (scr, lo) # update stack with new line

                            output = self.substitute(user["OUTPUT"].replace("\\n", "\n"))
                            input = self.substitute(user["INPUT"].replace("\\n", "\n"))
                            
                            # check if scene changed, if so continue
                            if stack and stack[-1][0] != script:
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

    def add(self, name: str, scene: Tinder):
        self.scenes[name] = scene
        return self

    def get(self, name: str):
        if name in self.scenes:
            return self.scenes[name]
        raise ValueError(f"Tinder '{name}' not found.")

def instantiate_game(path: str = "", debug = False):
    """
    Instantiate the game, compile all scripts, and return the game instance.

    If debug is True, script compilation is skipped.
    """
    def compile_worker(queue: queue.Queue, results: queue.Queue, env: dict, permissions: list[str]):
        """Worker function to compile scripts in a separate thread."""
        while True:
            try:
                filepath: str = queue.get_nowait()
                filepath = os.path.normpath(filepath).replace("\\", "/")
            except QueueEmpty:
                break
            scenename = None
            try:
                script = get_file(filepath)
                keyname, filename = os.path.split(filepath.removeprefix("game/scripts"))
                filename = filename.split(".")
                keyname = keyname.removeprefix("/")
                keyname += "/" if keyname else ""
                version = filename[-2]
                scenename = keyname + filename[0]
                try:
                    tinder: Scene = tinderstarter.compile(script, version, copy.copy(env))
                except FirestarterError as e:
                    raise Ember(f"Error compiling '{filepath}':\n{e}")
                path = Path(filepath).parts
                if len(path) > 3 and path[2] in permissions:
                    tinder.permissions = [path[2]]
                results.put((scenename, tinder, None))
            except (Ember, TinderBurn) as e:
                results.put((scenename, None, str(e)))
            finally:
                queue.task_done()
    
# Initialize the game environment
    game = Game(Crucible(READ_ONLY).update(protectedMemory))
    game.log(Info("Starting TorchBox server...", "🔥"))
# Import libraries
    libraries = import_libraries(game, exclude=["BaseLibrary"])
    game.log(Info(f"Loaded {len(libraries)} libraries.", "📚"))
    base = BaseLibrary(game).export()
    game.shared.update(base)
    game.libraries = libraries
# Prepare the realm
    if os.path.exists(SAVE_FILE):
        game.log(Info(f"Loading realm from {Ansi.BLUE}{SAVE_FILE}{Ansi.RESET}...", "💽", Ansi.WHITE))
        realm = Realm.load(SAVE_FILE, classes=classes)
    else:
        game.log(Info("Creating new realm...", "🛠️", Ansi.WHITE))
        realm = Realm("Socks & Sorcery", "A realm for Socks & Sorcery users.")
    game.log(Info(f"Realm: {Ansi.GREEN}{realm.name}{Ansi.RESET}", f"🏰", Ansi.WHITE))
    game.realm = realm
    game.debug = debug
# Find possible permissions
    tinderstarter.libs = game.libraries
    permissions = []
    for library in game.libraries.values():
        if library.permissions:
            permissions.extend(library.permissions)
# Prepare thread environment for compiling scripts
    scripts = queue.Queue()
    results = queue.Queue()
    count = 0
    env = {k: v for k, v in base.items()}
    for script in get_scripts(path):
        scripts.put(script)
        count += 1

    game.log(Info(f"Found {count} scripts.", "📜"))
    game.logger.show = False # Hide logger output during compilation
    from testing import Profiler
# Start worker threads to compile scripts
    with Profiler("Compiling scripts"):
        NUM_WORKERS = min(4, os.cpu_count() or 1)  # Use up to 4 workers or number of CPUs
        threads: list[threading.Thread] = []
        for _ in range(NUM_WORKERS):
            thread = threading.Thread(target=compile_worker, args=(scripts, results, env, permissions))
            thread.start()
            threads.append(thread)
    # Wait for all scripts to be processed
        scripts.join()
        for thread in threads:
            thread.join()
    # Only errors are put in the results queue, so we can check if there were any errors
        game.logger.show = True
        while not results.empty():
            keyname, scene, error = results.get()
            if scene:
                game.add(keyname, scene)
            else:
                game.log(Warning(error))
        game.log(Info(f"Compiled {len(game.scenes)} scripts.", "  "))

    return game

def start_server(torchbox: TorchBox):
    torchbox.listen()
    game.log(Info("Server is ready to accept connections.", "  ", Ansi.WHITE))
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
