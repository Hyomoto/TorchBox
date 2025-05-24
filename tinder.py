"""
tinder.py
=========
TinderBox is a minimalist scripting engine providing deterministic, extensible
logic for interactive scenes or nodes in Python applications.

Author: Devon "Hyomoto" Mullane, 2025

Overview:
---------
TinderBox defines a small, declarative language designed for ease of parsing,
customization, and rapid iteration. Its core features:
  - A compact, extensible instruction set ("kindling") for assignment, flow control,
    arithmetic, branching, and I/O.
  - Dynamic registration and macro redefinition of commands and argument patterns.
  - Seamless integration with arbitrary data environments via the Crucible class,
    supporting protected, global, and local scopes for variable management.

TinderBox itself is unopinionated about how game or application state is structured.
The user (or host engine) defines what variables exist, how memory maps are arranged,
and what conventions—if any—are imposed on input, output, or control flow. Patterns
and macros can be freely redefined to fit any domain, and the shape of the environment
remains the implementer's choice.

Typical Usage:
--------------
- Register a core or custom command set with desired syntax and argument rules.
- Compile source scripts to TinderBox instruction trees.
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
"""
from typing import List, Any
from constants import Crucible
from abc import ABC, abstractmethod
import re

# exceptions

class Yield(Exception):
    """
    Used by tinderboxes to yield control back to the torchbox.
    """
    def __str__(self):
        return "Yield()"

class JumpTo(Yield):
    """
    Used by the TinderBox to jump to a new line.
    """
    def __init__(self, line: int):
        super().__init__()
        self.line = line
    def __str__(self):
        return f"JumpTo({self.line})"

class TinderBurn(Exception):
    """Thrown when a Tinder script fails to compile."""
    pass

# values

class Value(ABC):
    @abstractmethod
    def get(self, env: Crucible) -> Any:
        pass

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

class String(Value):
    """A string value."""
    def __init__(self, var: str):
        self.var = str(var)
    def get(self, env: Crucible):
        return self.var
    def __repr__(self):
        return f"String({self.var})"

class Number(Value):
    """A number value."""
    def __init__(self, var: float):
        self.var = float(var)
    def get(self, env: Crucible):
        return self.var
    def __repr__(self):
        return f"Number({self.var})"

class Group(Value):
    """A group of values that can be retrieved as a list."""
    def __init__(self, items: list):
        self.list = items
    def get(self, env: Crucible):
        return [item.get(env) for item in self.list]
    def __repr__(self):
        return f"Group({self.list})"

class Kindling(Value, ABC):
    """Base class for all kindling operations."""
    def __init__(self):
        pass
    @abstractmethod
    def get(self, env: Crucible) -> Any | None:
        pass

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
    def __init__(self, var: Value, text: Value):
        self.var = str(var.var)
        self.text = text
    def get(self, env: Crucible):
        env.set(self.var, env.get(self.var) + self.text.get(env) + "\n")
    def __repr__(self):
        return f"Write({self.var}, {self.text})"

class Input(Kindling):
    """Sets a variable in the environment based and yields execution."""
    def __init__(self, var: Value, prompt: Value):
        self.var = str(var.var)
        self.prompt = prompt
    def get(self, env: Crucible):
        env.set(self.var,self.prompt.get(env))
        raise Yield() # causes a yield
    def __repr__(self):
        return f"Input({self.var}, {self.prompt})"

# comparison

class Comparison(Kindling):
    pass

class In(Comparison):
    """Checks if a value is in a list of values."""
    def __init__(self, value: Value, *ops: Value):
        self.value = value
        self.ops = ops
    def get(self, env: Crucible):
        compare = self.value.get(env)
        for op in self.ops:
            if op.get(env) == compare:
                return True
        return False
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
    """Checks if any value is true."""
    def __init__(self, *ops: Value):
        self.ops = ops
    def get(self, env: Crucible):
        for op in self.ops:
            if op.get(env):
                return True
        return False
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

class Goto(Kindling):
    """A Goto instruction that sets a variable to a line number."""
    def __init__(self, scene: Value):
        self.var = scene.var
    def get(self, env: Crucible):
        pass
    def __repr__(self):
        return f"Goto({self.var})"

class Stop(Kindling):
    """Stops the execution of the TinderBox."""
    def get(self, env: Crucible):
        raise Yield() # causes a yield
    def __repr__(self):
        return "Stop()"

class Jump(Kindling):
    """Jumps to a line number based on a condition."""
    def __init__(self, goto: Lookup | Number, condition: Comparison | Value | None = None):
        self.goto = goto
        self.condition = condition
    def get(self, env: Crucible):
        goto = Lookup(self.goto.var) if isinstance(self.goto, String) else self.goto
        if self.condition is None:
            raise JumpTo(goto.get(env))
        elif self.condition.get(env):
            raise JumpTo(goto.get(env))
    def __repr__(self):
        return f"Jump({self.goto}, {self.condition})"

# TinderBox

class TinderBox:
    """
    A collection of Kindling instructions that can be executed.  Returns
    the next line of execution or raises an exception if an error occurs.
    """
    instructions: List[Kindling]
    def __init__(self, instructions: List[Kindling] = []):
        self.instructions = instructions
    def __setitem__(self, index: int, instruction: Kindling):
        self.instructions[index] = instruction
    def __getitem__(self, index: int) -> Kindling:
        return self.instructions[index]
    def __len__(self) -> int:
        return len(self.instructions)
    def __repr__(self) -> str:
        return f"TinderBox[{len(self)} lines](\n\t{'\n\t'.join(repr(inst) for inst in self.instructions)}\n)"
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

TOKEN_RE = re.compile(
    r'(\"(?:[^\"\\]|\\.)*\")'   # Double-quoted string
    r'|(`[^`]+`)'               # Backtick sub-command (non-nested)
    r'|([^\s]+)'                # Plain token
)
TOKEN_LS = re.compile(r'\s*("(?:[^"\\]|\\.)*"|[^,\s\[\]]+)\s*(,|$)')


class Tinder:
    """
    Tinder
    ======
    The Tinder class defines the domain-specific language used by TinderBox.
    It provides a concise API for registering keywords, argument patterns,
    and macro overrides, allowing users to extend or redefine language syntax
    and semantics as needed.

    Primary responsibilities:
    - Register and redefine language keywords and argument patterns.
    - Support macros for custom command behaviors or aliasing.
    - Compile textual scripts into TinderBox instruction trees for execution.
    - Optionally prepare local environments (e.g., for GOTO lookups) to support script navigation.
    """
    def __init__(self):
        self.kindling = {}
        
    def register(self, keyword, pattern, kindling: Kindling):
        """Register a keyword with a pattern and its corresponding kindling operation."""
        self.kindling[keyword] = (pattern.split(), kindling)
        return self
    
    def macro(self, keyword, macro, pattern = None):
        """
        Create an alias for a registered keyword, optionally overriding its pattern. This allows
        a command to be accessed under a different name, or with a custom argument pattern.
        """
        if keyword not in self.kindling:
            raise TinderBurn(f"Keyword '{keyword}' not registered.")
        self.kindling[macro] = (pattern.split() if pattern else self.kindling[keyword][0], self.kindling[keyword][1])
        return self

    def makeLocalEnvironment(self, tinderbox: TinderBox, env: Crucible):
        local = Crucible(parent=env)
        for i, op in enumerate(tinderbox.instructions):
            if isinstance(op, Goto):
                local.set(op.var, i)
        return local

    def compile(self, script) -> TinderBox:
        def error(self, line, message):
            """Record an error message with the line number."""
            nonlocal errors
            errors.append(f"Line {line}: {message}")

        def make_redirect(value: str):
            if value.startswith('@'):
                return Redirect(value[1:])
            return make_number(value)
        
        def make_number(value: str):
            try:
                return Number(float(value))
            except ValueError:
                return make_string(value)

        def make_string(value: str):
            if value.startswith('"'):
                if not value.endswith('"'):
                    raise TinderBurn(f"Unmatched quote in '{value}'")
                return String(value[1:-1])
            return Lookup(value)

        def process_token(index: int, tokens: list[str]):
            keyword = tokens[index]
            if keyword.startswith("`"):
                keyword = keyword[1:]
            values: List[Value] = []

            if keyword not in self.kindling:
                raise TinderBurn(f"Unknown keyword '{tokens[index]}'")

            pattern, kindling = self.kindling[keyword]
            for key in pattern:
                index += 1
                if key.startswith("%"):
                    if key == "%..":
                        for t in range(index, len(tokens)):
                            if tokens[t] == "Nil":
                                break
                            values.append(make_redirect(tokens[t]))
                        break

                    optional = key[1] == "?"
                    type = key[2] if optional else key[1]

                    if index >= len(tokens): # run out of tokens
                        if optional:
                            values.append(None)
                            continue
                        else:
                            raise TinderBurn(f"{keyword} expects '{key}' but got end of line.")

                    if tokens[index] == "Nil":
                        values.append(None)
                        continue

                    if tokens[index].startswith("`"): # operation
                        try:
                            value, index = process_token(index, tokens)
                        except TinderBurn as e:
                            raise TinderBurn(f"{keyword} expects '{key}' but got: {e}")
                        values.append(value)
                    else:
                        match type:
                            case "s":
                                values.append(make_redirect(tokens[index]))
                                if isinstance(values[-1], Number):
                                    raise TinderBurn(f"{keyword} expected a string but got a number: {tokens[index]}")

                            case "n":
                                values.append(make_redirect(tokens[index]))
                                if isinstance(values[-1], String):
                                    raise TinderBurn(f"{keyword} expected a number but got a string: {tokens[index]}")

                            case ".":
                                values.append(make_redirect(tokens[index]))
                            case _:
                                raise TinderBurn(f"Unknown type '{type}' in '{key}'")
                elif key.startswith("."):
                    value = key[1:]
                    if value.startswith('"'):
                        values.append(make_string(value))
                    else:
                        values.append(make_number(value))
                    index -= 1
                else:
                    if tokens[index] != key:
                        raise TinderBurn(line, f"{keyword} expected '{key}' but got '{tokens[index]}'")
            try:
                return kindling(*values), index
            except TypeError as e:
                raise TinderBurn(f"{keyword} expected {repr(pattern)} arguments but got {repr(values)}") from e
            
        errors = []
        output = TinderBox()
        for i, line in enumerate(script.splitlines()):
            tokens = [t for group in TOKEN_RE.findall(line) for t in group if t]
            try:
                operation, index = process_token(0, tokens)
            except TinderBurn as e:
                error(i+1, str(e))
                continue
            output.instructions.append(operation)
        if errors:
            raise TinderBurn("Failed to compile script:\n" + "\n".join(errors))
        return output

tinder = Tinder()
tinder.register("write", "%s %s", Write)
tinder.register("input", "%s %s", Input)
tinder.register("set", "%s %.", Set)

tinder.register("add", "%. %. %?.", Add)
tinder.register("subtract", "%. %. %?.", Subtract)
tinder.register("max", "%..", Max)
tinder.register("min", "%..", Min)
tinder.register("less", "%. %.", Less)
tinder.register("greater", "%. %.", Greater)
tinder.register("in", "%s %..", In)

tinder.register("and", "%..", And)
tinder.register("or", "%..", Or)
tinder.register("not", "%.", Not)

tinder.register("jump", "%s %?.", Jump)
tinder.register("#", "%s", Goto)
tinder.register("stop", "", Stop)

tinder.register("call", "%s %..", Call)
