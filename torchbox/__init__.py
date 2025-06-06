from typing import Dict, List, Optional, Any
from tinder.crucible import Crucible
from tinder import Tinderstarter, Tinder, TinderBurn
from .realm import Realm, User
from .logger import Logger, Message, Error
from abc import ABC, abstractmethod
from constants import RESET, BLACK, WHITE, RED, GREEN, BROWN, BLUE, PURPLE, CYAN, YELLOW, LIGHT_GRAY, LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE, LIGHT_PURPLE, LIGHT_CYAN, DARK_GRAY, BOLD, FAINT, ITALIC, UNDERLINE, BLINK, NEGATIVE, CROSSED
import re

class Ember(Exception):
    """
    Raised when TorchBox encounters an unrecoverable error.
    Remember: where there's smoke, there's fire.
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

class TorchBox(ABC):
    macros: Crucible
    scenes: Dict[str, Tinder]
    logger: Logger
    def __init__(self, ):
        self.logger = None
        self.macros = {}
        self.scenes = {}
        self.messages = []

    @abstractmethod
    def run(self, realm: Realm, env: Crucible, entry: str) -> tuple[str, bool]:
        """Run the TorchBox with the given realm and environment."""

    def substitute(self, text: str, env: Crucible, macros: dict[str, str] = {}) -> str:
        for match in reversed(list(MACRO_PATTERN.finditer(text))):
            macro = match.group(1)
            if match.group(0).startswith("`"):
                # Handle color codes
                color_code = int(match.group(0)[1:])
                macro = COLORS[color_code]
            elif macro in macros:
                macro = self.substitute(macros[macro], macros, env)
            else:
                macro = env[macro]
                if not macro:
                    continue
                macro = self.substitute(macro, macros, env)
            text = text[:match.start()] + macro + text[match.end():]
        return text

    def log(self, message: Message):
        message.text = f"{self.scene} -> {message.text}"
        if self.logger:
            self.logger.log(message)
        if isinstance(message, Error):
            raise Ember(message.text)

    def add(self, name: str, scene: Tinder):
        self.scenes[name] = scene
        return self

    def get(self, name: str):
        if name in self.scenes:
            return self.scenes[name]
        raise ValueError(f"Tinder '{name}' not found.")
