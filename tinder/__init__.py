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
from typing import Type, List, Any
from firestarter.crucible import Crucible
from abc import ABC, abstractmethod
from firestarter import Firestarter, Grammar, Lexeme, Value, Primitive
import re

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

# primitives

class String(Primitive):
    """A string value."""
    @property
    def primitive(self) -> Type[str]:
        return str
    def __repr__(self):
        return f"String({self.var})"

class Number(Primitive):
    """A number value."""
    @property
    def primitive(self) -> Type[str]:
        return float
    def __repr__(self):
        return f"Number({self.var})"

# values

class Lookup(Value):
    """A lookup retrieves a variable from the environment."""
    def __init__(self, var: str):
        self.var = var
    def get(self, env: Crucible):
        return env.get(self.var)
    def __repr__(self):
        return f"Lookup({self.var})"
    
class Redirect(Lookup):
    """A lookup that redirects to another variable in the environment."""
    def __init__(self, var: str):
        super().__init__(var)
    def get(self, env: Crucible):
        lookup = super().get(env)
        return env.get(lookup)
    def __repr__(self):
        return f"Redirect({self.var})"

class Group(Value):
    """A group of values that can be retrieved as a list."""
    def __init__(self, *items: Any):
        self.list = items
    def __getitem__(self, index: int):
        return self.list[index] if index < len(self.list) else None
    def __setitem__(self, index: int, value: Value):
        if index < len(self.list):
            self.list[index] = value
        else:
            raise IndexError("Index out of range for Group.")
    def get(self, env: Crucible):
        return [item.get(env) for item in self.list]
    def __repr__(self):
        return f"Group({self.list})"

# kindling operations

class Kindling(Value, ABC):
    """Base class for all kindling operations."""
    def __init__(self):
        pass
    @abstractmethod
    def get(self, env: Crucible) -> Any | None:
        pass

class From(Kindling):
    """A kindling that retrieves a value from a list."""
    def __init__(self, var: Value, index: Value):
        self.var = str(var.var)
        self.index = index
    def get(self, env: Crucible):
        return env.get(self.var)[self.index.get(env)]
    def __repr__(self):
        return f"From({self.var})"

# set

class Set(Kindling):
    """Sets a variable in the environment."""
    def __init__(self, var: Value, value: Value):
        self.var = str(var.var)
        self.value = value
    def get(self, env: Crucible):
        env.set(self.var, self.value.get(env))
    def __repr__(self):
        return f"Set({self.var}, {self.value})"

class Write(Kindling):
    """Writes a string to a variable in the environment."""
    def __init__(self, var: Value, text: Value, newline: Value = None):
        self.var = str(var.var)
        self.text = text
        self.newline = newline or Number(1)  # Optional newline condition
    def get(self, env: Crucible):
        env.set(self.var, env.get(self.var) + self.text.get(env) + "\n" if self.newline.get(env) else "")
    def __repr__(self):
        return f"Write({self.var}, {self.text})"

class Input(Kindling):
    """Sets a variable in the environment based and yields execution."""
    def __init__(self, var: Value, prompt: Value):
        self.var = str(var.var)
        self.prompt = prompt
    def get(self, env: Crucible):
        env.set(self.var,self.prompt.get(env))
        raise Yield()
    def __repr__(self):
        return f"Input({self.var}, {self.prompt})"

# comparison

class Comparison(Kindling):
    pass

class In(Comparison):
    """Returns the value if it is in the list, or None."""
    def __init__(self, value: Value, *ops: Value):
        self.value = value
        self.ops = ops
    def get(self, env: Crucible):
        compare = self.value.get(env)
        for op in self.ops:
            result = op.get(env)
            if result == compare:
                return result
        return None
    def __repr__(self):
        return f"In({self.value}, {self.ops})"

class And(Comparison):
    """Checks if all values are true."""
    def __init__(self, *ops: Value):
        self.ops = ops
    def get(self, env: Crucible):
        for op in self.ops:
            if not op.get(env):
                return False
        return True
    def __repr__(self):
        return f"And({self.ops})"

class Or(Comparison):
    """Returns the first value that is Truthy, or None."""
    def __init__(self, *ops: Value):
        self.ops = ops
    def get(self, env: Crucible):
        for op in self.ops:
            result = op.get(env)
            if op.get(env):
                return result
        return None
    def __repr__(self):
        return f"Or({self.ops})"

class Not(Comparison):
    """Negates a value or operation."""
    def __init__(self, op: Value):
        self.op = op
    def get(self, env: Crucible):
        return not self.op.get(env)
    def __repr__(self):
        return f"Not({self.op})"
    
class Less(Comparison):
    """Checks if the left value is less than the right value."""
    def __init__(self, left: Value, right: Value):
        self.left = left
        self.right = right
    def get(self, env: Crucible):
        return self.left.get(env) < self.right.get(env)
    def __repr__(self):
        return f"Less({self.left}, {self.right})"
    
class Greater(Comparison):
    """Checks if the left value is greater than the right value."""
    def __init__(self, left: Value, right: Value):
        self.left = left
        self.right = right
    def get(self, env: Crucible):
        return self.left.get(env) > self.right.get(env)
    def __repr__(self):
        return f"Greater({self.left}, {self.right})"

# data manipulation

class Max(Kindling):
    """Returns the maximum value from a list of values."""
    def __init__(self, *ops: Value):
        self.ops = ops
    def get(self, env: Crucible):
        return max(op.get(env) for op in self.ops)
    def __repr__(self):
        return f"Max({self.ops})"
    
class Min(Kindling):
    """Returns the minimum value from a list of values."""
    def __init__(self, *ops: Value):
        self.ops = ops
    def get(self, env: Crucible):
        return min(op.get(env) for op in self.ops)
    def __repr__(self):
        return f"Min({self.ops})"

class Add(Kindling):
    """Adds two values together, optionally with a maximum limit."""
    def __init__(self, left: Value, right: Value, max: Value | None = None):
        self.left = left
        self.right = right
        self.max = max
    def get(self, env: Crucible):
        if self.max is not None:
            return min(self.max.get(env), self.left.get(env) + self.right.get(env))
        return self.left.get(env) + self.right.get(env)
    def __repr__(self):
        if self.max is not None:
            return f"Add({self.left}, {self.right}, {self.max})"
        return f"Add({self.left}, {self.right})"
    
class Subtract(Kindling):
    """Subtracts the right value from the left value, optionally with a minimum limit."""
    def __init__(self, left: Value, right: Value, min: Value | None = None):
        self.left = left
        self.right = right
        self.min = min
    def get(self, env: Crucible):
        if self.min is not None:
            return max(self.min.get(env), self.left.get(env) - self.right.get(env))
        return self.left.get(env) - self.right.get(env)
    def __repr__(self):
        if self.min is not None:
            return f"Subtract({self.left}, {self.right}, {self.min})"
        return f"Subtract({self.left}, {self.right})"

# call

class Call(Kindling):
    """Calls a function in the environment with arguments."""
    def __init__(self, name: Value, *args: Value):
        self.name = str(name.var)
        self.args = args
    def get(self, env: Crucible):
        return env.call(self.name, *[arg.get(env) for arg in self.args])
    def __repr__(self):
        return f"Call({self.name}, {self.args})"

# control flow

class NoOp(Kindling):
    """A no-operation instruction that does nothing."""
    def get(self, env: Crucible):
        pass
    def __repr__(self):
        return "NoOp()"

class Goto(NoOp):
    """A no-operation instruction used to flag line numbers by name."""
    def __init__(self, scene: Value):
        self.var = scene.var
    def get(self, env: Crucible):
        pass
    def __repr__(self):
        return f"Goto({self.var})"

class Stop(Kindling):
    """Stops the execution of the Tinder."""
    def get(self, env: Crucible):
        raise Yield() # causes a yield
    def __repr__(self):
        return "Stop()"

class Jump(Kindling):
    """Jumps to a line number based on a condition."""
    def __init__(self, goto: Lookup | Number, condition: Comparison | Value | None = None):
        self.goto = Lookup(goto.var) if isinstance(goto, String) else goto
        self.condition = condition
    def get(self, env: Crucible):
        if self.condition is None:
            raise JumpTo(self.goto.get(env))
        elif self.condition.get(env):
            raise JumpTo(self.goto.get(env))
    def __repr__(self):
        return f"Jump({self.goto}, {self.condition})"

# Tinder

class Tinder:
    """
    A collection of Kindling instructions that can be executed.  Returns
    the next line of execution or raises an exception if an error occurs.
    """
    instructions: List[Kindling]
    def __init__(self, *instructions: Kindling ):
        self.instructions = instructions
    def __setitem__(self, index: int, instruction: Kindling):
        self.instructions[index] = instruction
    def __getitem__(self, index: int) -> Kindling:
        return self.instructions[index]
    def __len__(self) -> int:
        return len(self.instructions)
    def __repr__(self) -> str:
        return f"Tinder[{len(self)} lines](\n\t{'\n\t'.join(repr(inst) for inst in self.instructions)}\n)"
    def getJumpTable(self) -> dict[str, int]:
        """
        Returns a dictionary mapping Goto labels to their line numbers.
        This is useful for resolving jumps by name.
        """
        return {inst.var: i for i, inst in enumerate(self.instructions) if isinstance(inst, Goto)}
    def run(self, line: int, env: Crucible):
        while line < len(self.instructions):
            try:
                self.instructions[line].get(env)
                line += 1
            except JumpTo as j:
                line = j.line
            except Yield:
                line += 1
                break
            except Exception as e:
                raise TinderBurn(f"Error at line {line+1}: {e}") from e
        return line


class Comment(Lexeme):
    """Base class for comments."""
    @property
    def value(self) -> str:
        """Return the comment text."""
        return self.text

class Number(Lexeme):
    @property
    def value(self) -> int:
        """Return the numeric value of the lexeme."""
        return int(self.text)

class String(Lexeme):
    @property
    def value(self) -> str:
        """Return the string value of the lexeme."""
        return self.text[1:-1]  # Remove quotes

class Identifier(Lexeme):
    @property
    def value(self) -> str:
        """Return the identifier value."""
        return self.text

class Function(Lexeme):
    @property
    def value(self) -> str:
        """Return the function name without the backtick."""
        return self.text[1:]  # Remove the leading backtick
    
class Redirect(Lexeme):
    @property
    def value(self) -> str:
        """Return the redirection identifier without the '@'."""
        return self.text[1:]  # Remove the leading '@'

class Nil(Lexeme):
    @property
    def value(self) -> None:
        """Return None for the nil lexeme."""
        return None

NUMBER_RE = re.compile(r'-?(?:\d+(\.\d*)?|\.\d+)')  # Matches floats, including negative numbers
REDIRECT_RE = re.compile(r'@([a-zA-Z_][a-zA-Z0-9_]*)')  # Matches redirection identifiers starting with '@'
FUNC_RE = re.compile(r'`[a-zA-Z_][a-zA-Z0-9_]*')  # Matches function names starting with a backtick
NIL_RE = re.compile(r'Nil')  # Matches the keyword 'nil'
#LINE_COMMENT_RE = re.compile(r'//[^\r\n]*')
#BLOCK_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)
STRING_RE = re.compile(r'(".*"|\'[^\']*\')')  # Matches double or single quoted strings
IDENTI_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*')  # Matches identifiers

grammar = Grammar(IGNORE_WHITESPACE)
grammar.register(String, match=[STRING_RE])
grammar.register(Number, match=[NUMBER_RE])
grammar.register(Identifier, "Keyword", match=["call", "write", "set", "input", "jump", "#", "stop"])
grammar.register(Identifier, match=[IDENTI_RE])
grammar.register(Function, match=["call", "add", "subtract", "max", "min", "less", "greater", "equal", "and", "or", "not", "if", "in"])
grammar.register(Redirect, match=[REDIRECT_RE])
#grammar.register(Comment, match=[LINE_COMMENT_RE, BLOCK_COMMENT_RE])
grammar.register(Number, match=["True", "False"], sub = [1, 0]) # Treat True as 1 and False as 0
grammar.register(Nil, match=["Nil"], sub=[None])  # Treat Nil as None


# this is all super ungraceful, ugly development stuff
# get the Tinder grammar
tinder = Firestarter(grammar)
# register discardable expressions
tinder.register(Tinder)

tinder.register(Call)
tinder.register(Write)
tinder.register(Input)
tinder.register(Set)

tinder.register(Jump)
tinder.register(Goto)
tinder.register(Stop)

tinder.register(Add)
tinder.register(Subtract)
tinder.register(Min)
tinder.register(Max)
tinder.register(From)

tinder.register(Less)
tinder.register(Greater)
tinder.register(In)
tinder.register(And)
tinder.register(Or)
tinder.register(Not)

tinder.register(Lookup)
tinder.register(Redirect)
tinder.register(String)
tinder.register(Number)

tinder.macro(Call, "function")
tinder.macro(Number, "True", Number(1))
tinder.macro(Number, "False", Number(0))
tinder.macro(Write, None, ". .", Number(1))  # alias write with newline
tinder.discard("ws", "ws?")

with open("./scripts/login.tinder", "r") as f:
    script = f.read()

script = tinder.compile(script)