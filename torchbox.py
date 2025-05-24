from typing import Dict, List, Optional, Any
from constants import Crucible, Ember, Macro
from logger import Logger, Message, Debug, Info, Warning, Error
from tinder import TinderBox
import re

MACRO_PATTERN = re.compile(r'\[\[(.*?)\]\]')

class Sheaf:
    pass

class TorchBox():
    name: str
    macros: Crucible
    scenes: Dict[str, TinderBox]
    logger: Logger
    line: str
    scene: str
    def __init__(self, name: str, macros = None, errorLevel = Debug, first: str = "start"):
        self.name = name
        self.macros = macros or Crucible()
        self.logger = Logger(errorLevel)
        self.scenes = {}
        self.messages = []

    def __getitem__(self, name: str) -> TinderBox:
        """Get a scene by name."""
        if name in self.scenes:
            return self.scenes[name]
        raise ValueError(f"TinderBox '{name}' not found.")

    def __setitem__(self, name, scene: TinderBox):
        self.add(name, scene)

    def update(self, cmd: str, env: Crucible):
        """Send input to the scene graph and return the output.
        Returns:
            tuple(output, clear)
            * output- the output string from the scene graph
            * clear - whether the scene requested a clear
        """
        self.logger.clear()
        try:
            output = "PLACEHOLDER"
            logs = []
        except Ember as e:
            raise Ember(f"{env.get('SCENE')} -> {e}")
        # push scene graph logs to the logger
        for log in logs:
            log(log)
        # return the scene graph output
        env.set("OUTPUT", self.substitute(env.get("OUTPUT")))

    def log(self, message: Message):
        message.text = f"{self.scene} -> {message.text}"
        self.logger.log(message)
        if isinstance(message, Error):
            raise Ember(message.text)

    def substitute(self, text: str, env: Crucible, stack = None):
        if stack is None:
            stack = []
        for match in reversed(list(MACRO_PATTERN.finditer(text))):
            macro = match.group(1)
            if macro in stack:
                continue
            sub: Macro | str | None = self.macros.get(macro)
            if sub:
                replace = sub
                if isinstance(sub, Macro) and sub.replace in env:
                    replace = str(env.get(sub.replace))
                replace = self.substitute(replace, env, stack + [macro])
                text = text[:match.start()] + replace + text[match.end():]
        return text

    def add(self, name: str, scene: TinderBox):
        self.scenes[name] = scene
        return self

    def get(self, name: str):
        if name in self.scenes:
            return self.scenes[name]
        raise ValueError(f"TinderBox '{name}' not found.")
