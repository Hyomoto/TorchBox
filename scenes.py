from typing import Dict, List, Optional, Callable
from canvas import Ansi

class Macro:
    pattern: str
    replace: str
    lookup: bool
    def __init__(self, pattern: str, replace: str, lookup: bool = False):
        self.pattern = pattern
        self.replace = replace
        self.lookup = lookup

class MacroLookup(Macro):
    def __init__(self, pattern: str, replace: str):
        super().__init__(pattern, replace, lookup=True)

class MacroList():
    def __init__(self, *args: Macro):
        self.macros = {}
        for macro in args:
            self.macros[macro.pattern] = macro

    def get(self, pattern: str):
        return self.macros.get(pattern)

    def __contains__(self, pattern):
        return pattern in self.macros

class Choice:
    keys: List[str]
    text: str
    goto: Optional[str]
    call: Optional[Callable]
    def __init__(self, keys, goto=None, call=None):
        self.keys = keys
        self.goto = goto
        self.call = call

class InputFlags:
    NONE = 0b0000
    LOWER = 0b0001
    UPPER = 0b0010
    PROPER = 0b0011
    SPLIT = 0b1000

class NodeInput:
    text: str
    var: Optional[str]
    goto: Optional[str]
    call: Optional[Callable]
    flags: int
    def __init__(self, text, var=None, goto=None, call=None, flags = InputFlags.LOWER | InputFlags.SPLIT ):
        self.text = text
        self.var = var
        self.goto = goto
        self.call = call
        self.flags = flags
    def getInput(self, text) -> List[str]:
        if self.flags & InputFlags.PROPER == InputFlags.PROPER:
            text = text.title()
        elif self.flags & InputFlags.LOWER:
            text = text.lower()
        elif self.flags & InputFlags.UPPER:
            text = text.upper()
        if self.flags & InputFlags.SPLIT:
            text = text.split()
        return [text] if isinstance(text, str) else text
        

class NodeInputConfirm(NodeInput):
    def __init__(self, text, goto, var=None, call=None, flags = InputFlags.NONE ):
        super().__init__(text, var, goto, call, flags)

class NodeInputChoices(NodeInput):
    choices: List[Choice]
    def __init__(self, text, choices: list[Choice], var=None, goto=None, call=None, flags = InputFlags.LOWER ):
        super().__init__(text, var, goto, call, flags)
        self.choices = choices

class NodeText:
    text: str
    def __init__(self, text):
        self.text = text
    def __str__(self):
        return self.text

class NodeTextLookup(NodeText):
    var: str
    before: Optional[str]
    after: Optional[str]
    def __init__(self, var, lookup, before = None, after = None):
        self.var = var
        self.before = before
        self.after = after
        self.lookup = lookup
    def get(self, var):
        if var in self.lookup:
            return f"{self.before or ''}{self.lookup.get(var)}{self.after or ''}"
        raise ValueError(f"NodeTextLookup does not have a '{var}' entry.")

class Node:
    text: NodeText
    input: NodeInput
    def __init__(self, text: str | NodeText, input):
        self.name = "unknown"
        if isinstance(text, str):
            self.text = NodeText(text)
        self.text = text # type: ignore
        self.input = input
    def __repr__(self):
        return f"Node({self.name})"

class Scene:
    first: Optional[Node]
    macros: Optional[MacroList]
    def __init__(self,name: str, macros = None):
        self.nodes = {}
        self.name = name
        self.first = None
        self.macros = macros

    def getMacro(self, pattern: str):
        if not self.macros:
            return None
        return self.macros.get(pattern)

    def add(self, name, node : Node):
        """Add a node to the scene."""
        self.nodes[name] = node
        node.name = name
        if self.first is None:
            self.first = node
        return self

    def get(self, name: Optional[str] = None) -> Node:
        if name is None:
            return self.first # type: ignore
        if name in self.nodes:
            return self.nodes[name]
        raise ValueError(f"Node '{name}' not found in scene.")

    def __repr__(self):
        # name, number of nodes, first node
        return f"Scene({self.name}({len(self)}) -> {self.first})"

    def __len__(self):
        return len(self.nodes)

class SceneList:
    scenes: Dict[str, Scene]
    def __init__(self):
        self.scenes = {}

    def add(self, scene: Scene):
        self.scenes[scene.name] = scene
        return self

    def get(self, name: str):
        if name in self.scenes:
            return self.scenes[name]
        raise ValueError(f"Scene '{name}' not found.")

intro = SceneList().add(
    Scene("creation",
            MacroList(
                MacroLookup("name", "name"),
            )
         )
        .add("name",Node(
            f"{Ansi.WHITE}            ** Welcome to the realm, new warrior! **\n\n"
            f"{Ansi.LIGHT_GREEN}What would you like as an alias?\n",
            NodeInput(
                f"{Ansi.GREEN}Name: {Ansi.RESET}",
                var="name",
                goto="confirm_name",
                flags=InputFlags.NONE
            )
        ))
        .add("confirm_name",Node(
            "",
            NodeInputChoices(
                f"{Ansi.GREEN}[[name]]? [Y] : {Ansi.RESET}",
                [
                    Choice(["y", "yes"], goto="gender"),
                    Choice(["n", "no"], goto="name")
                ]
            )
        ))
        .add("gender",Node(
            "",
            NodeInputChoices(
                f"{Ansi.GREEN}And your gender? ({Ansi.LIGHT_GREEN}M{Ansi.GREEN}/{Ansi.LIGHT_GREEN}F{Ansi.GREEN}) [{Ansi.LIGHT_GREEN}M{Ansi.GREEN}]:{Ansi.RESET} ",
                [
                    Choice(["m","male","boy"], call = lambda x : "male"),
                    Choice(["f","female","girl"], call = lambda x : "female"),
                ],
                var="gender",
                goto="background",
            )
        ))
        .add("background",Node(
            f"{Ansi.WHITE}As you remember your childhood, you think of...\n\n"
            f"{Ansi.LIGHT_GREEN}({Ansi.PURPLE}K{Ansi.LIGHT_GREEN})illing a lot of woodland creatures.\n"
            f"{Ansi.LIGHT_GREEN}({Ansi.PURPLE}D{Ansi.LIGHT_GREEN})abbling in the mystical forces.\n"
            f"{Ansi.LIGHT_GREEN}({Ansi.PURPLE}L{Ansi.LIGHT_GREEN})ying, cheating, and stealing from the blind.\n\n",
            NodeInputChoices(
                f"{Ansi.GREEN}Pick one. ({Ansi.LIGHT_GREEN}K{Ansi.GREEN},{Ansi.LIGHT_GREEN}D{Ansi.GREEN},{Ansi.LIGHT_GREEN}L{Ansi.GREEN}) : {Ansi.RESET}",
                [
                    Choice(["k","fighter"]),
                    Choice(["d","wizard"]),
                    Choice(["l","thief"]),
                ],
                var="background",
                goto="intro"
            )
        ))
        .add("intro",Node(
            NodeTextLookup(
                "background",
                {
                    "k" :
                        f"{Ansi.LIGHT_GREEN}Now that you've grown up, you have decided to study the ways of the"
                        "Death Knights.  All beginners want the power to use their body"
                        "and weapon as one.  To inflict twice the damage with the finesse only"
                        "a warrior of perfect mind can do.",
                    "d" :
                        f"{Ansi.LIGHT_GREEN}You remember the strange smells and stranger noises coming from your"
                        "“laboratory”—which was really just the family pantry. If anyone"
                        "asks, the burnt eyebrows were a result of “advanced research.” Sometimes"
                        "the village still smells faintly of brimstone when you pass through.",
                    "l" :
                        f"{Ansi.LIGHT_GREEN}Childhood taught you plenty—mostly, how gullible grown-ups can be and"
                        "how easy it is to walk off with an unattended pie. Some called it"
                        "“resourceful,” others “a menace.” You just called it “training for"
                        "bigger things.”"
                }),
            NodeInputConfirm(
                f"\n\n<MORE>{Ansi.RESET}",
                "intro2",
            )
        ))
)