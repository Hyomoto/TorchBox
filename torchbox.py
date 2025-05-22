from typing import Callable, Dict, List, Optional, Tuple, Union
from canvas import Canvas, Ansi
from terminal import Terminal
from scenes import Scene, Node, NodeTextLookup, NodeInput, NodeInputChoices, NodeInputConfirm, Macro, MacroLookup, MacroList
import scenes
from test import Logger, Message, Debug, Info, Warning, Error
import os
import re

colorTable = [
    Ansi.RESET,
    Ansi.BLACK,
    Ansi.RED,
    Ansi.GREEN,
    Ansi.BROWN,
    Ansi.BLUE,
    Ansi.PURPLE,
    Ansi.CYAN,
    Ansi.YELLOW,
    Ansi.WHITE,
    Ansi.LIGHT_GRAY,
    Ansi.LIGHT_RED,
    Ansi.LIGHT_GREEN,
    Ansi.LIGHT_BLUE,
    Ansi.LIGHT_PURPLE,
    Ansi.LIGHT_CYAN,
    Ansi.DARK_GRAY,
    Ansi.BOLD,
    Ansi.FAINT,
    Ansi.ITALIC,
    Ansi.UNDERLINE,
    Ansi.BLINK,
    Ansi.NEGATIVE,
    Ansi.CROSSED,
]

MACRO_PATTERN = re.compile(r'\[\[(.*?)\]\]')

class Environment:
    def __init__(self):
        self.variables = {}
        self.functions = {}

    def set(self, var: str, value: Union[str, int, float]):
        points = var.split('.')
        scope = self.variables
        while len(points) > 1:
            point = points.pop(0)
            if point not in scope:
                scope[point] = {}
            scope = scope[point]
        scope[points[0]] = value

    def get(self, var: str) -> Union[str, int, float]:
        points = var.split('.')
        scope = self.variables
        while len(points) > 1:
            point = points.pop(0)
            if point not in scope:
                raise ValueError(f"Variable '{var}' not found.")
            scope = scope[point]
        return scope.get(points[0], None)

    def call(self, func: str, *args):
        if func in self.functions:
            return self.functions[func](*args)
        raise ValueError(f"Function '{func}' not found.")


class TorchBox:
    scene: Scene
    node: Node
    def __init__(self, width: int = 60, height: int = 24):
        self.canvas = Canvas(width, height)
        self.terminal = Terminal(width, height)
        self.scene = None # type: ignore
        self.node = None # type: ignore
        self.environment = Environment()
        self.macros = MacroList()
        self.logger = Logger(Debug)

    def log(self, message: Message):
        message.text = f"{self.scene if self.scene else 'Scene(None)'}:{self.node if self.node else 'None'} -> {message.text}"
        self.logger.log(message)

    def write(self, text: str, wrap = True):
        if self.getMode() == self.terminal and not wrap:
            self.terminal.writer(text)
        else:
            self.getMode().write(text)

    def substitute(self, text: str, stack = None):
        if stack is None:
            stack = []
        for match in reversed(list(MACRO_PATTERN.finditer(text))):
            macro = match.group(1)
            if macro in stack:
                self.log(Warning(f"Recursinve'{macro}' {stack}. Aborting."))
                continue
            sub = self.getMacro(macro)
            if sub:
                if isinstance(sub, MacroLookup):
                    try:
                        replace = self.environment.get(sub.replace)
                    except ValueError as _:
                        self.log(Warning(f"Lookup '{sub.replace}' from '{macro}' not found in environment."))
                        continue
                    replace = str(replace)
                else:
                    replace = sub.replace
                replace = self.substitute(replace, stack + [macro])
                text = text[:match.start()] + replace + text[match.end():]
            else:
                self.log(Warning(f"Macro '{macro}' not found."))
        return text

    def getMode(self):
        return self.terminal if isinstance(self.scene, Scene) else self.canvas

    def getMacro(self, pattern: str):
        result = None
        if self.scene:
            result = self.scene.getMacro(pattern)
        if not result:
            result = self.macros.get(pattern)
        return result

    def setScene(self, scene: Scene):
        self.log(Debug(f"Setting scene {scene}"))
        self.getMode().clear()
        self.scene = scene
        if not scene.first:
            return
        self.setNode(scene.first)

    def setNode(self, node: Node):
        self.log(Debug(f"Setting node {node}"))
        self.node = node
        if isinstance(node.text, NodeTextLookup):
            text = node.text.get(self.environment.get(node.text.var))
        else:
            text = node.text
        self.write(self.substitute(str(text)))

    def tokens(self, cmd: str):
        input = self.node.input

        if self.getMode() == self.terminal:
            self.write(self.substitute(f"{input.text}{cmd}"))

        tokens = input.getInput(cmd)
        first = tokens[0]
        
        match input.__class__:
            case scenes.NodeInput:
                if not cmd:
                    return
                if input.var:
                    self.environment.set(input.var, first)
                self.setNode(self.scene.get(input.goto))
            case scenes.NodeInputChoices:
                if not cmd:
                    return
                for choice in input.choices: # type: ignore
                    if first in choice.keys:
                        self.log(Debug(f"Choice '{first}' found in {choice.keys}"))
                        if choice.call:
                            result = choice.call(choice.keys[0])
                        else:
                            result = choice.keys[0]
                        if input.var:
                            self.environment.set(input.var, result)
                        # add call eventually
                        goto = choice.goto if choice.goto else input.goto
                        self.setNode(self.scene.get(goto))
            case scenes.NodeInputConfirm:
                self.setNode(self.scene.get(input.goto))

    def input(self):
        return input(self.substitute(self.node.input.text))

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def render(self):
        print(self.getMode().render())
