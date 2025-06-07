"""
Tinder is a minimalist scripting language builder providing deterministic, extensible
logic for interactive scenes or nodes in Python applications.

Overview:
---------
Defines a small, declarative language builder designed for ease of parsing, customization,
and rapid iteration. Its core features:
  - A built-in compact, extensible instruction set ("kindlings") for assignment, flow
    control, arithmetic, branching, and I/O.
  - A flexible Firestarter class for easily defining the language syntax and
    compiling scripts into executable Tinder instruction trees.
  - Dynamic registration and macro redefinition of commands and argument patterns.
  - Seamless integration with arbitrary data environments via the Crucible class,
    supporting protected, global, and local scopes for variable management.

A Tinder is itself unopinionated about how game or application state is structured.  The
scripts operate directly on a Crucible, meaning the user (or host engine) defines what
variables exist, how memory maps are arranged, and what conventions—if any—are imposed on
input, output, or control flow. Patterns and macros can be freely redefined to fit a
domain because the shape of the environment is the implementer's choice.

Typical Usage:
--------------
- Register a core or custom command set with desired syntax and argument rules.
- Compile source scripts to Tinder instruction trees using the Firestarter class.
- At runtime, pass a Crucible (or stack of Crucibles) as the execution environment.
- Scripts operate directly on the Crucible, serving as the interface for all input and output
  between the script and host application.
- Scripts return the next line to execute, enabling explicit control over script flow.
  If yields are used, the host is responsible for managing the line counter and script resumption.

Tinder Scripting Language: Syntax and Standard Library
==========================================================
Type Patterns
Symbol	Meaning
 %s	    String argument (or Lookup/Redirect)
 %n	    Number argument (or Lookup/Redirect)
 %.	    Any type (String, Number, Lookup, Redirect, Nil, etc)
 %?x	Optional argument of type x
 %..	Slurp: all remaining arguments, any type
 .ARG	Insert specific literal or variable (e.g., .INPUT)

Arguments
=========
String: "quoted"
Number: parsed as float (e.g., 3, 2.5)
Lookup: variable name (unquoted)
Redirect: @key (lookup the value of key, then use as new key)
Nil: Explicitly signals "no value" for optional/slurp args
Sub-operation: `keyword ... for inline/nested operations

Core Keywords & Patterns
==========================
Keyword	Pattern	Function
 write	%s %s	Write string to variable
 input	%s %s	Prompt user, store input in variable
 set	%s %.	Assign value to variable
 add	%. %. %?.	Add two (optionally capped)
 subtract	%. %. %?.	Subtract two (optionally floored)
 max	%..	Maximum of N arguments
 min	%..	Minimum of N arguments
 less	%. %.	Less-than comparison
 greater	%. %.	Greater-than comparison
 in	%s %..	Membership test (left in right...)
 and	%..	Logical AND of N arguments
 or	%..	Logical OR of N arguments
 not	%.'	Logical NOT
 jump	%s %?.	Jump to line/label if (optional) condition
 #	%s	Goto (alias for jump/label mapping)
 stop	`` (none)	End script/yield
 call	%s %..	Call function with arguments

Notes
 The compiler reads tokens left-to-right, consuming arguments as matched by the keyword pattern.
 Type patterns enforce only the string/number distinction where possible; Lookups and Redirects always parse but may fail at runtime if types mismatch.
 Macro definitions and .ARG patterns enable reusable or aliased commands (e.g., always writing to OUTPUT).
 Nil is valid for slurp or optional args, ensuring safe pattern matching and termination of argument lists.
 Sub-operations allow basic composition; nesting is supported where grammar allows.

Author: Devon "Hyomoto" Mullane, 2025

License: MIT License
"""
from importlib.resources import files as import_files, files
from typing import Tuple, Type, Dict, List, Optional, Any
from .crucible import Crucible
from abc import ABC, abstractmethod
from firestarter import Firestarter, FirestarterError, Symbol, Value as AbstractValue
from firestarter.grammar import make_grammar_from_file, RuleIgnore, Grammar
import inspect
import sys

def getGrammars() -> Dict[str, Grammar]:
    traverse = files("tinder")
    output = {}
    for entry in traverse.iterdir():
        if not entry.is_file() or not entry.name.endswith(".peg"):
            continue
        file = entry.name[:-4]  # Remove the .peg extension
        output[file] = make_grammar_from_file(entry, RuleIgnore.SPACES)
    return output

GRAMMARS = getGrammars()
# exceptions

class TinderBurn(Exception):
    """Thrown when a Tinder fails to compile."""
    pass

# flow control

class Yield(Exception):
    """
    Used by Tinders to yield control.
    """
    def __str__(self):
        return "Yield()"

class JumpTo(Yield):
    """
    Used by the Tinders to jump to a new line.
    """
    def __init__(self, line: int):
        super().__init__()
        self.line = line
    def __str__(self):
        return f"JumpTo({self.line})"

# Kindling base class

class Kindling(Symbol, ABC):
    """Base class for all kindling operations."""
    @abstractmethod
    def transmute(self, env: Crucible) -> Any | None:
        """Transmute the kindling into a value or operation in the Crucible."""
        pass

# primitives

class Value(AbstractValue, Kindling):
    @property
    @abstractmethod
    def type(self) -> Type[Any]:
        """Return the primitive type of the value."""
        pass
    def transmute(self, env: Crucible):
        return self.value
    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

class String(Value):
    """A string value."""
    def __init__(self, value: str):
        self.value = self.type(value)
        if value.startswith('"') and value.endswith('"'):
            self.value = self.value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            self.value = self.value[1:-1]
    @property
    def type(self):
        return str

class Number(Value):
    """A number value."""
    @property
    def type(self):
        return float

class Boolean(Value):
    """A boolean value."""
    @property
    def type(self):
        return bool

# values

class Identifier(Value):
    pass

class Lookup(Identifier):
    """A lookup retrieves a variable from the environment."""
    def __init__(self, value: String | str):
        if isinstance(value, String):
            self.value: str = value.value
        else:
            self.value = value
    @property
    def type(self):
        return str
    def transmute(self, env: Crucible):
        return env.get(self.value)

class Redirect(Lookup):
    """A lookup that redirects to another variable in the environment."""
    def __init__(self, value: Value | str):
        if isinstance(value, Value):
            value = value.value
        super().__init__(value)
    def transmute(self, env: Crucible):
        lookup = super().transmute(env)
        return env.get(lookup)

class Group(Value):
    """A group of values that can be retrieved as a list."""
    def __init__(self, *items: Kindling):
        self.list = list(items)
    def __getitem__(self, index: int):
        return self.list[index] if index < len(self.list) else None
    def __setitem__(self, index: int, value: Value):
        if index < len(self.list):
            self.list[index] = value
        else:
            raise IndexError("Index out of range for Group.")
    @property
    def type(self) -> Type[List]:
        return list
    def transmute(self, env: Crucible):
        return [item.transmute(env) for item in self.list]
    def __len__(self):
        return len(self.list)
    def __repr__(self):
        return f"Group({self.list})"
    def __contains__(self, item: Any):
        return item in self.list

class Groupables:
    """An operation that operates on a group of values."""
    def __init__(self, *group: Group):
        if len(group) == 1 and isinstance(group[0], Group):
            self.group = group[0]
        else:
            self.group = Group(*group)

# kindling operations

# set

class Set(Kindling):
    """Sets a variable in the environment."""
    def __init__(self, identifier: Identifier, value: Kindling ):
        self.identifier = identifier.value
        self.value = value
    def transmute(self, env: Crucible):
        env.set(self.identifier, self.value.transmute(env))
    def __repr__(self):
        return f"Set(identifier={self.identifier}, value={self.value})"

class Write(Kindling):
    """Writes a string to a variable in the environment."""
    def __init__(self, identifier: Identifier, text: Identifier | String, newline: Lookup | Boolean = None):
        self.identifier = identifier.value
        self.text = text
        self.newline = newline if newline else Boolean(False)
    def transmute(self, env: Crucible):
        if self.identifier not in env:
            env.set(self.identifier, "")
        env.set(self.identifier, env.get(self.identifier) + self.text.transmute(env) +  ("\n" if self.newline.transmute(env) else ""))
    def __repr__(self):
        return f"Write(identifier={self.identifier}, text={self.text}, newline={self.newline})"

class Input(Kindling):
    """Sets a variable in the environment based and yields execution."""
    def __init__(self, identifier: Identifier, prompt: Identifier | String):
        self.identifier = identifier.value
        self.prompt = prompt
    def transmute(self, env: Crucible):
        env.set(self.identifier, self.prompt.transmute(env))
        raise Yield()
    def __repr__(self):
        return f"Input(identifier={self.identifier}, prompt={self.prompt})"

# get

class From(Groupables, Kindling):
    """A kindling that retrieves a value from a list."""
    def __init__(self, index: Identifier | Number, *group: Group | Value):
        super().__init__(*group)
        self.index = index
    def transmute(self, env: Crucible):
        index = self.index.transmute(env)
        if index < 0 or index >= len(self.group.list):
            return None
        return self.group.list[index].transmute(env)
    def __repr__(self):
        return f"From(index={self.index}, group={self.group})"

# comparison
class Comparison(Kindling):
    pass

class In(Groupables,Comparison):
    """Returns the value if it is in the list, or None."""
    def __init__(self, value: Kindling, *group: Group | Value):
        super().__init__(*group)
        self.value = value
    def transmute(self, env: Crucible):
        left = self.value.transmute(env)
        right = self.group.transmute(env)
        if left in right:
            return left
        return None
    def __repr__(self):
        return f"In(value={self.value}, group={self.group})"

class And(Groupables,Comparison):
    """Checks if all values are true."""
    def __init__(self, group: Group | Value):
        if len(group) < 2:
            raise TinderBurn("And requires at least two values.")
        super().__init__(group)
    def transmute(self, env: Crucible):
        items = self.group.transmute(env)
        for item in items:
            if not item:
                return False
        return True
    def __repr__(self):
        return f"And({self.group.list})"

class Or(Groupables,Comparison):
    """Returns the first value that is Truthy, or None."""
    def __init__(self, *group: Group | Value):
        if len(group) < 2:
            raise TinderBurn("And requires at least two values.")
        super().__init__(*group)
    def transmute(self, env: Crucible):
        for item in self.group.list:
            value = item.transmute(env)
            if value:
                return value
        return None
    def __repr__(self):
        return f"Or({self.group.list})"

class Not(Comparison):
    """Negates a value or operation."""
    def __init__(self, value: Kindling):
        self.value = value
    def transmute(self, env: Crucible):
        if self.value.transmute(env):
            return False
        return True
    def __repr__(self):
        return f"Not({self.value})"

class Less(Comparison):
    """Checks if the left value is less than the right value."""
    def __init__(self, left: Kindling, right: Kindling):
        self.left = left
        self.right = right
    def transmute(self, env: Crucible):
        return self.left.transmute(env) < self.right.transmute(env)
    def __repr__(self):
        return f"Less({self.left} < {self.right})"

class Greater(Comparison):
    """Checks if the left value is greater than the right value."""
    def __init__(self, left: Kindling, right: Kindling):
        self.left = left
        self.right = right
    def transmute(self, env: Crucible):
        return self.left.transmute(env) > self.right.transmute(env)
    def __repr__(self):
        return f"Greater({self.left} > {self.right})"

# data manipulation

class Max(Groupables, Kindling):
    """Returns the maximum value from a list of values."""
    def __init__(self, *group: Group | Value):
        super().__init__(*group)
    def transmute(self, env: Crucible):
        return max(op.transmute(env) for op in self.group.list)
    def __repr__(self):
        return f"Max({self.group.list})"

class Min(Groupables, Kindling):
    """Returns the minimum value from a list of values."""
    def __init__(self, *group: Group | Value):
        super().__init__(*group)
    def transmute(self, env: Crucible):
        return min(op.transmute(env) for op in self.group.list)
    def __repr__(self):
        return f"Min({self.group.list})"

class Add(Groupables, Kindling):
    """Adds values together, optionally with a maximum limit."""
    def __init__(self, group: Group, max: Value | None = None):
        if len(group) < 2:
            raise TinderBurn("Add requires at least two values.")
        super().__init__(group)
        self.max = max
    def transmute(self, env: Crucible):
        result = sum(op.transmute(env) for op in self.group.list)
        return min(result, self.max.transmute(env)) if self.max is not None else result
    def __repr__(self):
        return f"Add({self.group.list}, max={self.max})" if self.max is not None else f"Add({self.group.list})"

class Subtract(Groupables, Kindling):
    """Subtracts the right value from the left value, optionally with a minimum limit."""
    def __init__(self, group: Group, min: Value | None = None):
        if len(group) < 2:
            raise TinderBurn("Subtract requires at least two values.")
        super().__init__(group)
        self.min = min
    def transmute(self, env: Crucible):
        result = self.group.list[0].transmute(env)
        for item in self.group.list[1:]:
            result -= item.transmute(env)
        return max(result, self.min.transmute(env)) if self.min is not None else result
    def __repr__(self):
        return f"Subtract({self.group.list}, min={self.min})" if self.min is not None else f"Subtract({self.group.list})"

# call

class Call(Groupables, Kindling):
    """Calls a function in the environment with arguments."""
    def __init__(self, identifier: Identifier | String, *group: Optional[Group | Kindling]):
        super().__init__(*group)
        self.identifier = identifier
    def transmute(self, env: Crucible):
        identifier = self.identifier.transmute(env)
        if not callable(identifier):
            raise TinderBurn(f"Identifier '{self.identifier}:{identifier}' is not callable.")
        return identifier(*self.group.transmute(env))
    def __repr__(self):
        return f"Call(identifier={self.identifier}, group={self.group})"

# control flow

class NoOp(Kindling):
    """A no-operation instruction that does nothing."""
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        pass
    def __repr__(self):
        return "NoOp()"

class Goto(NoOp):
    """A no-operation instruction used to flag line numbers by name."""
    def __init__(self, identifier: Lookup | String):
        self.identifier: str = identifier.value
    def transmute(self, env: Crucible):
        pass
    def __repr__(self):
        return f"Goto({self.identifier})"

class Stop(Kindling):
    """Stops the execution of the Tinder."""
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        raise Yield() # causes a yield
    def __repr__(self):
        return "Stop()"

class Jump(Kindling):
    """Jumps to a line number based on a condition."""
    def __init__(self, goto: String | Lookup | Number, condition: Comparison | Identifier | None = None):
        self.goto = Lookup(goto.value) if isinstance(goto, String) else goto
        self.condition = condition
    def transmute(self, env: Crucible):
        condition = self.condition.transmute(env) if self.condition else True
        line = self.goto.transmute(env)
        if not isinstance(line, (float,int)):
            raise TinderBurn(f"Jump target '{self.goto}' must be a line number, got {line}.")
        if not condition:
            return
        raise JumpTo(line)
    def __repr__(self):
        return f"Jump(goto={self.goto}, condition={self.condition})"

# Tinder

class Tinder:
    """
    A collection of Kindling instructions that can be executed.  Returns
    the next line of execution or raises an exception if an error occurs.
    """
    instructions: List[Kindling]
    jumpTable: Dict[str, int]
    def __init__(self, instructions: List[Kindling] ):
        self.instructions = instructions
        self.jumpTable = {inst.identifier: i for i, inst in enumerate(self.instructions) if isinstance(inst, Goto)}
    def __setitem__(self, index: int, instruction: Kindling):
        self.instructions[index] = instruction
    def __getitem__(self, index: int) -> Kindling:
        return self.instructions[index]
    def __len__(self) -> int:
        return len(self.instructions)
    def __repr__(self) -> str:
        list = '\n\t'.join(repr(inst) for inst in self.instructions)
        return f"Tinder[{len(self)} lines](\n\t{list}\n)"
    def writeJumpTable(self, env: Crucible):
        env.update(self.jumpTable)
    def run(self, line: int, env: Crucible):
        while line < len(self.instructions):
            try:
                self.instructions[line].transmute(env)
                line += 1
            except JumpTo as j:
                line = j.line
            except Yield:
                line += 1
                break
            except Exception as e:
                raise TinderBurn(f"Run failed on line {line + 1}: {e}") from e
        return line

def getAllSymbols():
    """
    Returns a list of all registered symbols in the Tinderstarter.
    This is useful for introspection or testing purposes.
    """
    return [obj for _, obj in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and issubclass(x, Symbol) and not inspect.isabstract(x))]

class Tinderstarter(Firestarter):
    def __init__(self):
        super().__init__(None, True)

        classes = getAllSymbols()
        # Auto-register all classes that are subclasses of Symbol
        for obj in classes:
            self.register(obj)
        self.macro(Write, None, Lookup("OUTPUT"), str, Number(1))  # Alias write with newline
        self.macro(Input, None, Lookup("INPUT"), str) # Alias input with prompt
        self.macro(NoOp, "Newline")

    def compile(self, source: str, version: str) -> Tinder:
        if not source.endswith('\n'):
            source += '\n'
        if version not in GRAMMARS:
            raise TinderBurn(f"Unsupported Tinder version: {version}. Available versions: {list(GRAMMARS.keys())}")
        self.grammar = GRAMMARS[version]
        return super().compile(source, Tinder)
