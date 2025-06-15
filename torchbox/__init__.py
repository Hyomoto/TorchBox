from typing import Optional, Callable, Dict, List, Type, Any
from tinder.crucible import Crucible, CrucibleError
from tinder import Tinder
from .realm import Realm
from .logger import Logger, Log, Critical, Warning, Info, Debug
from abc import ABC, abstractmethod
from constants import RESET, BLACK, WHITE, RED, GREEN, BROWN, BLUE, PURPLE, CYAN, YELLOW, LIGHT_GRAY, LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE, LIGHT_PURPLE, LIGHT_CYAN, DARK_GRAY, BOLD, FAINT, ITALIC, UNDERLINE, BLINK, NEGATIVE, CROSSED
import socket
import threading
import queue
import re

class Ember(Exception):
    """
    Raised when TorchBox encounters an unrecoverable error.
    Remember: where there's smoke, there's fire.
    """
    pass

class Shutdown(Exception):
    """
    Raised to signal TorchBox to shut down gracefully.
    """
    pass

COLORS = [
    RESET,      # 0
    WHITE,      # 1
    RED,        # 2
    GREEN,      # 3
    BROWN,      # 4
    BLUE,       # 5 
    PURPLE,     # 6
    CYAN,       # 7
    YELLOW,     # 8
    LIGHT_GRAY, # 9
    LIGHT_RED,  # 10
    LIGHT_GREEN,# 11
    LIGHT_BLUE, # 12
    LIGHT_PURPLE, # 13
    LIGHT_CYAN, # 14
    DARK_GRAY,  # 15
    BOLD,       # 16
    FAINT,      # 17
    ITALIC,     # 18
    UNDERLINE,  # 19
    BLINK,      # 20
    NEGATIVE,   # 21
    CROSSED     # 22
]
MACRO_PATTERN = re.compile(
    r'\[\[(.*?)\]\]'  # substitute macros like `[[macro]]`
    r'|`(-?\d+)'      # color codes
    r'|`\*'           # pop color
)

class ConnectionHandler(ABC):
    def __init__(self, client, queue: queue.Queue, log: Callable = None):
        self.client = client
        self.queue = queue
        self.log = log
        self.connected = True

    def listen(self):
        """Start listening for input from the user via this connection."""
        while True:
            try:
                self.receive()
            except Exception:
                break

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def receive(self):
        """Override in subclass: receive text input from user via this connection."""
        pass
    @abstractmethod
    def send(self, output: str, input: Optional[str] = None):
        """Override in subclass: send text response to user via this connection."""
        pass
    def close(self, output: Optional[str] = None):
        """Override in subclass: close this connection."""
        pass
    def __repr__(self):
        return f"<{self.__class__.__name__} %s>"

class SocketHandler(ConnectionHandler):
    client: socket.socket
    def __init__(self, client: socket.socket, queue: queue.Queue, log: Callable = None):
        super().__init__(client, queue, log)

    def login(self):
        self.queue.put(Message(self, "__LOGIN__", "login"))

    def receive(self):
        def filter(data: bytes) -> bytes:
            i = 0
            out = bytearray()
            while i < len(data):
                if data[i] == 255:  # IAC
                    if i + 1 < len(data):
                        cmd = data[i+1]
                        # Telnet command bytes: 251-254 (WILL, WONT, DO, DONT)
                        if cmd in (251, 252, 253, 254):
                            # Skip IAC + command + option
                            i += 3
                        else:
                            # Skip IAC + command
                            i += 2
                    else:
                        i += 1
                else:
                    out.append(data[i])
                    i += 1
            return bytes(out)
        try:
            data = self.client.recv(1024)
            if not data:
                raise ConnectionResetError
            data = filter(data)
            msg = data.decode(errors='ignore').strip()
            if not msg:
                return
            self.queue.put(Message(self, msg))
        except Exception:
            self.close()

    def send(self, output: str, input: Optional[str] = None):
        if not self.connected:
            return
        if input:
            text = output + "\n" + input + " "
        else:
            text = output
        text = text.replace("\n", "\r\n") # normalize newlines for telnet
        try:
            self.client.sendall(text.encode('utf-8'))
        except Exception:
            self.close()

    def close(self, output: Optional[str] = None):
        if not self.connected:
            return
        if output:
            self.client.sendall(output.encode('utf-8'))
        self.client.close()
        if self.log:
            self.log(Info("Connection closed."), self)
        self.connected = False

    def __repr__(self):
        try:
            return super().__repr__().replace("%s", str(self.client.getpeername()))
        except Exception:
            return super().__repr__().replace("%s", "closed or unknown")

class Message:
    def __init__(self, user: ConnectionHandler, content: str, type: Optional[str] = None):
        self.user = user
        self.content = content
        self.type = type

class TorchBox(ABC):
    scenes: Dict[str, Tinder]
    logger: Logger
    def __init__(self, realm: Realm, env: Crucible, logger: Logger = None):
        self.queue: queue.Queue[Message] = queue.Queue()
        self.logger = logger
        self.realm = realm
        self.env = env
        self.users: List[ConnectionHandler] = []

    @abstractmethod
    def run(self):
        """This is the game loop, override it in the subclass."""
        pass

    def getConnections(self):
        self.flushClosedConnections()
        return self.users

    def flushClosedConnections(self):
        self.users = [user for user in self.users if user.connected]
        return self

    def listen(self, host="localhost", port=8080):
        """Start listening for connections on the given IP address and port."""
        def socketListener(address='localhost', port=8080):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                self.log(Info(f"Listening on {address}:{port}"))
                server.bind((address, port))
                server.listen()
                while True:
                    sock, _ = server.accept()
                    client = self.getHandler(sock, 'socket')
                    threading.Thread(target=client.listen, daemon=True).start()
                    self.log(Info(f"New connection established {client}"), client)
                    self.users.append(client)
                    client.login()
        threading.Thread(target=socketListener, args=(host, port), daemon=True).start()
        return self

    def getHandler(self, client, of: str) -> ConnectionHandler:
        match of:
            case 'socket':
                return SocketHandler(client, self.queue, self.log)
            case _:
                raise ValueError(f"Unknown handler type: {of}")

    def substitute(self, text: str) -> str:
        env = self.env
        for match in reversed(list(MACRO_PATTERN.finditer(text))):
            macro = match.group(1)
            if match.group(0).startswith("`"):
                # Handle color codes
                color_code = int(match.group(0)[1:])
                macro = COLORS[color_code]
            else:
                macro = macro.split(":")
                try:
                    value = env[macro[0]]
                except CrucibleError:
                    continue
                if isinstance(value, float):
                    value = format(value, macro[1] if len(macro) > 1 else ".0f")
                else:
                    value = format(value, macro[1] if len(macro) > 1 else "")
                output = self.substitute(value)
            text = text[:match.start()] + output + text[match.end():]
        return text

    def log(self, message: Log, handle: Optional[ConnectionHandler] = None):
        if self.logger:
            if handle:
                message.text = f"{handle} -> {message.text}"
            self.logger.log(message)