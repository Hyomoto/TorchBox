"""
Tinder is a minimalist scripting language builder for deterministic, extensible
logic in interactive scenes or nodes for Python applications.

Overview:
---------
Defines a small, declarative language and grammar builder optimized for ease of parsing,
customization, and rapid iteration. Its core features:
  - PEG-based syntax supporting a compact, extensible instruction set ("kindlings") for assignment,
    flow control, arithmetic, branching, I/O, and macros.
  - The Firestarter class enables flexible language definition and compilation of scripts
    into executable Tinder instruction trees.
  - Dynamic registration of commands and support for default arguments.
  - Seamless integration with arbitrary application state via the Crucible class,
    supporting protected, global, and local scopes for variable management.
  - Syntactic sugar for common operations, such as operator aliases, conditional statements,
    and array/list manipulation.

A Tinder is itself unopinionated about how game or application state is structured.  The
scripts operate directly on a Crucible, meaning the user (or host engine) defines what
variables exist, how memory maps are arranged, and what conventions—if any—are imposed on
input, output, or control flow. Patterns and macros can be freely redefined to fit a
domain because the shape of the environment is the implementer's choice.

Typical Usage:
--------------
- Register core and/or custom commands with desired syntax and argument rules.
- Compile source scripts to Tinder instruction trees using the Firestarter class.
- At runtime, pass a Crucible (or stack) as the execution environment.
- Scripts directly operate on the Crucible, serving as the interface for all variable access,
  function calls, and I/O between script and host.
- Scripts yield the next line, label, or scene to execute, enabling explicit flow control.
- Host application manages script resumption and state, supporting coroutines or simple
  left-to-right execution as needed.

Tinder Scripting Language: Syntax
=================================
- Each script consists of lines; each line is a statement, label, or comment.
- Statements are read left-to-right, supporting assignment, I/O, flow control, function calls,
  and expressions.
- Labels (e.g., `# label`) mark jump targets for flow control.
- Conditional execution is supported inline: e.g., `jump fail if not USER`.
- Arithmetic, logical operators, and membership (`in`) are supported as expressions.
- Arrays/lists use `[item, ...]` syntax.
- String interpolation and macro expansion (e.g., `[[VARNAME]]`) are available at runtime.
- Sub-operations and nested function calls are supported within expressions.
- Comments begin with `//`. Blank lines are ignored.

Arguments
=========
String: "quoted"
Number: parsed as float (e.g., 3, 2.5)
Lookup: variable name (unquoted)
Redirect: @key (lookup the value of key, then use as new key)
Nil: Explicitly signals "no value" for optional/slurp args
Sub-operation: `keyword ... for inline/nested operations

Type Patterns
-------------
Symbol   Meaning
 %s      String argument (literal or variable)
 %n      Number argument (literal or variable)
 %.      Any type (String, Number, Array, Lookup, Redirect, Nil, etc.)
 %?x     Optional argument of type x
 %..     Slurp: all remaining arguments, any type
 .ARG    Insert specific literal or variable (e.g., .INPUT)

Core Keywords & Patterns
========================
Keyword    Pattern         Function
 write     %. %?s          Write value to output (or optionally to variable)
 input     %s %?s          Prompt user, optionally store input in variable
 set       %s %.           Assign value to variable
 in        %. %..          Membership test (left in right...)
 and       %..             Logical AND of N arguments
 or        %..             Logical OR of N arguments
 not       %.              Logical NOT
 jump      %s %?expr       Jump to line/label if (optional) condition
 #         %s              Label marker (alias for jump target)
 stop      (none)          End script/yield
 call      %s %..          Call function with arguments

Notes:
- The parser consumes arguments left-to-right, matching against the keyword's pattern.
- Operator aliases are supported (e.g., `+`, `-`, `*`, `/`, `==`, `!=`, `<`, `>`, `in`, etc.).
- Expressions and conditions can be nested within arguments where grammar allows.
- Macro definitions and .ARG patterns enable reusable/aliased commands.
- Nil is valid for slurp or optional args, ensuring safe pattern matching.
- Sub-operations allow composition and nesting.

Author: Devon "Hyomoto" Mullane, 2025

License: MIT License
"""
from importlib.resources import files as import_files, files
from typing import Tuple, Type, Dict, List, Optional, Any
from .crucible import Crucible
from abc import ABC, abstractmethod
from firestarter import Firestarter, SymbolReplace, Symbol as AbstractSymbol, Value as AbstractValue
from firestarter.grammar import make_grammar_from_file, Grammar
from firestarter.grammar import Flags as GrammarFlags
import inspect
import sys

def getGrammars() -> Dict[str, Grammar]:
    traverse = files("tinder")
    output = {}
    for entry in traverse.iterdir():
        if not entry.is_file() or not entry.name.endswith(".peg"):
            continue
        file = entry.name[:-4]  # Remove the .peg extension
        output[file] = make_grammar_from_file(entry, GrammarFlags.IGNORE_SPACE_AND_TAB | GrammarFlags.FLATTEN)
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

# symbols

class Symbol(AbstractSymbol,ABC):
    """Base class for all symbols in the Tinder language."""
    def __init__(self):
        pass
    def __repr__(self):
        return f"{self.__class__.__name__}()"

class Bang(Symbol):
    pass

class Minus(Symbol):
    pass

class Plus(Symbol):
    pass

class Times(Symbol):
    pass

class Slash(Symbol):
    pass

class LeftAngleBracket(Symbol):
    pass

class RightAngleBracket(Symbol):
    pass

class LeftAngleBracketEqual(Symbol):
    pass

class RightAngleBracketEqual(Symbol):
    pass

class BangEqual(Symbol):
    pass

class EqualEqual(Symbol):
    pass
    
# abstract base class

class Kindling(AbstractSymbol, ABC):
    """Base class for all kindling operations."""
    @abstractmethod
    def transmute(self, env: Crucible) -> Any | None:
        """Transmute the kindling into a value or operation in the Crucible."""
        pass

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

# primitives

class Constant(Value):
    """A constant value."""
    def __init__(self, value: str):
        if value == "True":
            self.value = True
        elif value == "False":
            self.value = False
        else:
            raise TinderBurn(f"Invalid constant value: {value}")
    @property
    def type(self):
        return type(self.value)

class String(Constant):
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

class Number(Constant):
    """A number value."""
    def __init__(self, value: str):
        self.value = self.type(value)
    @property
    def type(self):
        return float

# values

class Identifier(Value):
    """A lookup retrieves a variable from the environment."""
    def __init__(self, value: String | str ):
        if isinstance(value, String):
            self.value: str = value.value
        else:
            self.value = value
    @property
    def type(self):
        return str
    def transmute(self, env: Crucible):
        return env.get(self.value)

class Redirect(Identifier):
    """A lookup that redirects to another variable in the environment."""
    def __init__(self, value: Value | str ):
        if isinstance(value, Value):
            value = value.value
        super().__init__(value)
    def transmute(self, env: Crucible):
        lookup = super().transmute(env)
        return env.get(lookup)

class Array(Value):
    """A group of values that can be retrieved as a list."""
    def __init__(self, *items: Kindling):
        self.list = list(items)
    @property
    def type(self) -> Type[List]:
        return list
    def transmute(self, env: Crucible):
        return [item.transmute(env) for item in self.list]
    def __getitem__(self, index: int):
        index = int(index)
        if index < 0 or index >= len(self.list):
            return None
        return self.list[index]
    def __setitem__(self, index: int, value: Value):
        if index < len(self.list):
            self.list[index] = value
        else:
            raise IndexError("Index out of range for Array.")
    def __contains__(self, item: Any):
        return item in self.list
    def __len__(self):
        return len(self.list)
    def __repr__(self):
        return f"Array({self.list})"

# kindling operations

# unary functions

class Function(Kindling):
    """Calls a function in the environment with arguments."""
    def __init__(self, identifier: Identifier, *args: Kindling):
        self.identifier = identifier
        self.arguments = list(args) if args else []
    def transmute(self, env: Crucible):
        identifier = self.identifier.transmute(env)
        args = [arg.transmute(env) for arg in self.arguments]
        if not callable(identifier):
            raise TinderBurn(f"Identifier '{self.identifier}:{identifier}' is not callable.")
        return identifier(*args)
    def __repr__(self):
        return f"Function(identifier={self.identifier}, args={self.arguments})"

class Unary(AbstractSymbol):
    """A unary operation that applies a function to a single argument."""
    def __init__(self, symbol: Symbol, right: Kindling):
        match symbol:
            case Minus():
                if not isinstance(right, Value) or not isinstance(right.type, (bool, int, float)):
                    raise TinderBurn("Unary minus can only be applied to numbers.")
                raise SymbolReplace(Number(right.value * -1))
            case Bang():
                if isinstance(right, Constant):
                    raise SymbolReplace(Constant(not right.value))
                raise SymbolReplace(Not(right))
            case _:
                raise TinderBurn(f"Unknown unary operator: {symbol}")

class Not(Kindling):
    def __init__(self, right: Kindling):
        if isinstance(right, Constant):
            raise SymbolReplace(Constant("False" if right.value else "True"))
        self.right = right
    def transmute(self, env: Crucible):
        if not self.right.transmute(env):
            return True
        return False
    def __repr__(self):
        return f"Not({self.right})"

# binary functions

class Binary(AbstractSymbol):
    def __init__(self, left: Kindling, symbol: Symbol, right: Kindling):
        match symbol:
            case Plus():
                raise SymbolReplace(Add(left, right))
            case Minus():
                raise SymbolReplace(Subtract(left, right))
            case Times():
                raise SymbolReplace(Multiply(left, right))
            case Slash():
                raise SymbolReplace(Divide(left, right))
            case Less():
                raise SymbolReplace(Less(left, right))
            case Greater():
                raise SymbolReplace(Greater(left, right))
            case LessEqual():
                raise SymbolReplace(LessEqual(left, right))
            case GreaterEqual():
                raise SymbolReplace(GreaterEqual(left, right))
            case EqualEqual():
                raise SymbolReplace(Equal(left, right))
            case BangEqual():
                raise SymbolReplace(NotEqual(left, right))
            case _:
                raise TinderBurn(f"Unknown binary operator: {symbol}")

class AbstractBinary(Kindling):
    def __init__(self, left: Kindling, right: Kindling):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"{self.__class__.__name__}({self.left} %s {self.right})"

class Add(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) + self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "+")
    
class Subtract(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) - self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "-")
    
class Multiply(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) * self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "*")
    
class Divide(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) / self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "/")

class Less(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) < self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "<")
    
class Greater(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) > self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", ">")

class LessEqual(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) <= self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "<=")
    
class GreaterEqual(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) >= self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", ">=")
    
class Equal(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) == self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "==")

class NotEqual(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) != self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "!=")

class And(AbstractBinary):
    def transmute(self, env: Crucible):
        return self.left.transmute(env) and self.right.transmute(env)
    def __repr__(self):
        return super().__repr__().replace("%s", "and")
    
class Or(AbstractBinary):
    def transmute(self, env: Crucible):
        left = self.left.transmute(env)
        if left:
            return left
        right = self.right.transmute(env)
        if right:
            return right
        return None
    def __repr__(self):
        return super().__repr__().replace("%s", "or")

class In(AbstractBinary):
    def __init__(self, left: Kindling, right: List):
        super().__init__(left, right)
    def transmute(self, env: Crucible):
        left = self.left.transmute(env)
        right = self.right.transmute(env)
        if left in right:
            return left
        return None
    def __repr__(self):
        return super().__repr__().replace("%s", "in")

# conditions

class Condition(Kindling):
    def __init__(self, condition: Kindling):
        self.condition = condition
    def transmute(self, env: Crucible):
        if self.condition.transmute(env):
            return True
        return False
    def __repr__(self):
        return f"If(condition={self.condition})"

# control flow

class Call(AbstractSymbol):
    def __init__(self, function: Function):
        raise SymbolReplace(function)

class Jump(Kindling):
    def __init__(self, identifier: Identifier):
        self.identifier = identifier
    def transmute(self, env: Crucible):
        line = self.identifier.transmute(env)
        if line is None:
            raise TinderBurn(f"Jump target '{self.identifier.value}' not found in environment.")
        if not isinstance(line, (int, float)):
            raise TinderBurn(f"Jump target '{self.identifier.value}' is not a number.")
        raise JumpTo(int(line))
    def __repr__(self):
        return f"Jump(identifier={self.identifier})"

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
    def __init__(self, identifier: Identifier | String):
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
        raise Yield()
    def __repr__(self):
        return "Stop()"

# io

class Input(Kindling):
    """Sets a variable in the environment based and yields execution."""
    def __init__(self, prompt: Kindling, identifier: Optional[Identifier] = None):
        self.prompt = prompt
        self.identifier = identifier.value
    def transmute(self, env: Crucible):
        env.set(self.identifier, self.prompt.transmute(env))
        raise Yield()
    def __repr__(self):
        return f"Input(prompt={self.prompt}, identifier={self.identifier})"

class Set(Kindling):
    """Sets a variable in the environment."""
    def __init__(self, identifier: Identifier, value: Optional[Kindling] = None):
        self.identifier = identifier.value
        self.value = value
    def transmute(self, env: Crucible):
        value = self.value.transmute(env) if self.value else None
        env.set(self.identifier, value)
    def __repr__(self):
        return f"Set(identifier={self.identifier}, value={self.value})"

class Write(Kindling):
    """Writes a string to a variable in the environment."""
    def __init__(self, text: Kindling, identifier: Optional[Identifier] = None):
        self.text = text
        self.identifier = identifier.value
    def transmute(self, env: Crucible):
        current = env.get(self.identifier) if self.identifier in env else ""
        env.set(self.identifier, current + self.text.transmute(env) + "\n")
    def __repr__(self):
        return f"Write(text={self.text}, identifier={self.identifier})"

# statements

class Statement(Kindling):
    """A statement that executes a kindling operation."""
    def __init__(self, operation: Kindling, condition: Optional[Condition] = None):
        if not condition:
            raise SymbolReplace(operation) # no condition, just execute the operation
        self.operation = operation
        self.condition = condition
    def transmute(self, env: Crucible):
        if not self.condition.transmute(env):
            return
        self.operation.transmute(env)
    def __repr__(self):
        return f"Statement(operation={self.operation}, condition={self.condition})"

# Tinder

class Tinder:
    """
    A collection of Kindling instructions that can be executed.  Returns
    the next line of execution or raises an exception if an error occurs.
    """
    jumpTable: Dict[str, int]
    def __init__(self, instructions: List[Tuple[int, Kindling]] ):
        self.instructions = instructions
        self.jumpTable = {inst[1].identifier: i for i, inst in enumerate(self.instructions) if isinstance(inst[1], Goto)}
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
            actual, op = self.instructions[line]
            try:
                op.transmute(env)
                line += 1
            except JumpTo as j:
                line = j.line
            except Yield:
                line += 1
                break
            except Exception as e:
                raise TinderBurn(f"Run failed on line {actual}: {e}") from e
        return line

def getAllSymbols():
    """
    Returns a list of all registered symbols in the Tinderstarter.
    This is useful for introspection or testing purposes.
    """
    return [obj for _, obj in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and issubclass(x, AbstractSymbol) and not inspect.isabstract(x))]

class Tinderstarter(Firestarter):
    def __init__(self):
        super().__init__(None, True)

        classes = getAllSymbols()
        # Auto-register all classes that are subclasses of Symbol
        for obj in classes:
            self.register(obj)
        self.registerDefaults("Write", String(""), Identifier("OUTPUT"))
        self.registerDefaults("Input", String(""), Identifier("INPUT"))

    def compile(self, source: str, version: str) -> Tinder:
        if not source.endswith('\n'):
            source += '\n'
        if version not in GRAMMARS:
            raise TinderBurn(f"Unsupported Tinder version: {version}. Available versions: {list(GRAMMARS.keys())}")
        self.grammar = GRAMMARS[version]
        return super().compile(source, Tinder)
