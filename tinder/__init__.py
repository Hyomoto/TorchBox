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

Language Features
=================
Minimal Command Set:
- Only five explicit commands: call, jump, set, input, and stop.
- Any standalone string or interpolated expression on its own line is implicitly output to the user (“write”).

Line Structure:
- Each line is a single command, a label (# label), a comment, or a string to output.
- Conditions can be attached to commands (e.g., jump fail if not USER).

Expressions:
- Full support for arithmetic, comparison (==, !=, <, >, etc.), boolean logic, and function calls.
- Lists are supported: [a, b, c].
- Variable assignment and manipulation are straightforward (set VAR value).

Value-Returning Operators:
- or returns the first non-falsy value, not just a boolean (e.g., A or "fallback" gives "fallback" if A is falsy).
- in returns the matched item if present (e.g., CHOICE in ["a", "b"] yields the matching string).

String Interpolation:
- Strings can interpolate variables using [[VARNAME]] syntax at runtime.

Labels and Flow:
- Labels (# label) act as jump targets.
- jump may be conditional, allowing for simple branching and flow control.
- stop halts script execution.

Comments and Whitespace:
- Lines beginning with // are ignored.
- Blank lines are ignored.

Evaluation:
- Commands and expressions are parsed and executed left-to-right.
- Scripts operate on a mutable environment (the Crucible), allowing flexible variable and state management.

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
from importlib.resources import files
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

class FlowControl(Exception):
    pass

class Halted(FlowControl):
    """Used to halt the execution of the Tinder."""
    def __repr__(self):
        return "Halt()"

class Yielded(FlowControl):
    """
    Used by Tinders to yield control.
    """
    def __init__(self, line: int = 0, carry: Optional[Dict] = None):
        self.line = line
        if carry and not isinstance(carry, dict):
            raise TinderBurn(f"Illegal yield with carry: expected dict, got '{type(carry).__name__}'.")
        self.carry = carry
    def __str__(self):
        return f"Yield(line={self.line}, carry={self.carry})"

class Jumped(FlowControl):
    """
    Used by the Tinders to jump to a new line.
    """
    def __init__(self, line: int = 0, last: int = 0):
        self.line = line
        self.last = last
    def __str__(self):
        return f"JumpTo({self.line})"

class Returned(FlowControl):
    """
    Used to return to the last jump line.
    """
    def __str__(self):
        return "Return()"

class Imported(Yielded):
    """
    Used to import a library.
    """
    def __init__(self, library: str, name: Optional[str] = None):
        super().__init__()
        self.library = library
        self.name = name

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

class From(Symbol):
    pass

class In(Symbol):
    pass

class At(Symbol):
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
    def __init__(self, value):
        if value == "True":
            self.value = True
        elif value == "False":
            self.value = False
        else:
            self.value = value
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

class Indirect(Identifier):
    """A lookup that directs to another lookup in the environment."""
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
    def type(self) -> Type["Array"]:
        return Array
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

class KeyValuePair(Value):
    """A key-value pair for use in Tables."""
    def __init__(self, key: Identifier | String, value: Kindling):
        self.key = key.value
        self.value = value
    @property
    def type(self) -> Type[Tuple]:
        return KeyValuePair
    def transmute(self, env: Crucible):
        value = self.value.transmute(env)
        return (self.key, value)

class Table(Value):
    """A table of key-value pairs."""
    def __init__(self, *items: KeyValuePair):
        self.table = {item.key: item.value for item in items}
    @property
    def type(self) -> Type["Table"]:
        return Table
    def transmute(self, env: Crucible):
        return {key: value.transmute(env) for key, value in self.table.items()}
    def __getitem__(self, key: str):
        if key in self.table:
            return self.table[key]
        raise KeyError(f"Key '{key}' not found in Table.")
    def __setitem__(self, key: str, value: Kindling):
        self.table[key] = value
    def __contains__(self, key: str):
        return key in self.table
    def __len__(self):
        return len(self.table)
    def __repr__(self):
        items = ', '.join(f"{key}={value}" for key, value in self.table.items())
        return f"Table({{{items}}})"

# kindling operations

# unary functions

class Function(Kindling):
    """Calls a function in the environment with arguments."""
    def __init__(self, identifier: Identifier, *args: Kindling):
        self.identifier = identifier
        self.arguments = list(args) if args else []
    def transmute(self, env: Crucible):
        identifier = self.identifier.transmute(env)
        if not callable(identifier):
            raise TinderBurn(f"Identifier '{self.identifier}:{identifier}' is not callable.")
        return identifier(env, *[arg.transmute(env) for arg in self.arguments])
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
        left = self.left.transmute(env)
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

class Access(AbstractSymbol):
    def __init__(self, left: Kindling, symbol: Symbol, right: Array | Table | Identifier):
        match symbol:
            case In():
                raise SymbolReplace(ValueIn(left, right))
            case From():
                raise SymbolReplace(ValueFrom(left, right))
            case At():
                raise SymbolReplace(ValueAt(left, right))
            case _:
                raise TinderBurn(f"Unknown access operator: {symbol}")

class ValueFrom(AbstractBinary):
    """Returns where the value is found in the right operand, or None if not found."""
    def __init__(self, left: Kindling, right: Array | Table | Identifier ):
        super().__init__(left, right)
    def transmute(self, env: Crucible):
        right = self.right.transmute(env)
        left = self.left.transmute(env)
        if isinstance(right, Array):
            if not isinstance(left, (int, float)):
                raise TinderBurn(f"Left operand must be an integer index, got {type(left).__name__}.")
            return right[int(left)] if left in right else None
        if isinstance(right, Table):
            for key, value in right.table.items():
                if value.transmute(env) == left:
                    return key
            return None
        raise TinderBurn(f"Right operand must be an Array or Table, got {type(right).__name__}.")

class ValueIn(AbstractBinary):
    """Returns the left operand if it is found in the right operand, otherwise None."""
    def __init__(self, left: Kindling, right: Array | Table | Identifier ):
        super().__init__(left, right)
    def transmute(self, env: Crucible):
        right = self.right.transmute(env)
        if not isinstance(right, (dict, list)):
            raise TinderBurn(f"Right operand must be an Array or Table, got {type(right).__name__}.")
        left = self.left.transmute(env)
        if left in right:
            return left
        return None
    def __repr__(self):
        return super().__repr__().replace("%s", "in")

class ValueAt(AbstractBinary):
    """Returns the value at the index specified by the left operand in the right operand."""
    def __init__(self, left: Kindling, right: Array | Table | Identifier ):
        super().__init__(left, right)
    def transmute(self, env):
        right = self.right.transmute(env)
        left = self.left.transmute(env)
        if isinstance(right, Array):
            if isinstance(left, (int, float)):
                value = right[int(left)]
                return value.transmute(env) if value else None
            raise TinderBurn(f"Left operand must be an integer index, got {type(left).__name__}.")
        if isinstance(right, Table):
            if isinstance(left, str):
                value = right[left]
                return value.transmute(env) if value else None
            raise TinderBurn(f"Left operand must be a string key, got {type(left).__name__}.")
        raise TinderBurn(f"Right operand must be an Array or Table, got {type(right).__name__}.")

# statements

class Condition(Kindling):
    def __init__(self, condition: Kindling):
        self.condition = condition
    def transmute(self, env: Crucible):
        if self.condition.transmute(env):
            return True
        return False
    def __repr__(self):
        return f"If(condition={self.condition})"

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

### keywords ###

class Call(AbstractSymbol):
    def __init__(self, callout: Function):
        raise SymbolReplace(callout)

# assignment

class Inc(AbstractSymbol):
    def __init__(self, identifier: Identifier):
        raise SymbolReplace(Set(identifier, Add(identifier, Number(1))))

class Dec(AbstractSymbol):
    def __init__(self, identifier: Identifier):
        raise SymbolReplace(Set(identifier, Subtract(identifier, Number(1))))

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

# control flow

class Interrupt(Kindling):
    """Redirects execution to a specific line if an exception is raised."""
    def __init__(self, exception: Identifier, jump: Identifier):
        self.exception = exception.value
        self.jump = jump.value
    def transmute(self, env: Crucible):
        raise InterruptHandler(self.exception, self.jump)
    def __repr__(self):
        return f"Interrupt(exception={self.exception}, jump={self.jump})"

class Jump(Kindling):
    def __init__(self, identifier: Identifier):
        self.identifier = identifier
    def transmute(self, env: Crucible):
        line = self.identifier.transmute(env)
        if line is None:
            raise TinderBurn(f"Jump target '{self.identifier.value}' not found in environment.")
        if not isinstance(line, (int, float)):
            raise TinderBurn(f"Jump target '{self.identifier.value}' is not a number.")
        raise Jumped(int(line))
    def __repr__(self):
        return f"Jump(identifier={self.identifier})"

class Return(Kindling):
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        raise Returned()
    def __repr__(self):
        return "Return()"

class NoOp(Kindling):
    """A no-operation instruction that does nothing."""
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        pass
    def __repr__(self) -> str:
        return "NoOp()"

class Goto(NoOp):
    """A no-operation instruction used to flag line numbers by name."""
    def __init__(self, identifier: Identifier | String, otherwise: Optional[Identifier] = None):
        self.identifier: str = identifier.value
        self.otherwise = otherwise.value if otherwise else None
    def transmute(self, env: Crucible):
        if self.otherwise: # if otherwise, yield to it
            raise Jumped(env.get(self.otherwise))
    def __repr__(self):
        return f"Goto(identifier={self.identifier}, otherwise={self.otherwise})"

class Stop(Kindling):
    """Stops the execution of the Tinder."""
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        raise Halted()
    def __repr__(self):
        return "Stop()"

class Yield(Kindling):
    """Yields the execution of the Tinder."""
    def __init__(self, callout: Optional[Function | Table] = None):
        self.callout = callout
    def transmute(self, env: Crucible):
        if self.callout:
            if isinstance(self.callout, Function):
                output = self.callout.transmute(env)
            else:
                output = self.callout.transmute(env)
        else:
            output = None
        raise Yielded(carry=output)
    def __repr__(self) -> str:
        return f"Yield(callout={self.callout})"

# io

class Input(Kindling):
    """Sets a variable in the environment based and yields execution."""
    def __init__(self, prompt: Kindling, identifier: Optional[Identifier] = None):
        self.prompt = prompt
        if not identifier:
            raise TinderBurn("Input operation requires an identifier.")
        self.identifier = identifier.value
    def transmute(self, env: Crucible):
        env.set(self.identifier, self.prompt.transmute(env))
        raise Yielded()
    def __repr__(self):
        return f"Input(prompt={self.prompt}, identifier={self.identifier})"

class Write(Kindling):
    """Writes a string to a variable in the environment."""
    def __init__(self, text: Kindling, identifier: Optional[Identifier] = None):
        self.text = text
        if not identifier:
            raise TinderBurn("Write operation requires an identifier.")
        self.identifier = identifier.value
    def transmute(self, env: Crucible):
        current = env.get(self.identifier) or ""
        env.set(self.identifier, current + str(self.text.transmute(env)) + "\n")
    def __repr__(self):
        return f"Write(text={self.text}, identifier={self.identifier})"

class Import(Kindling):
    """Imports a library into the environment."""
    def __init__(self, library: Identifier, name: Optional[Identifier] = None):
        self.library = library.value
        self.name = name.value if name else None
    def transmute(self, env: Crucible):
        raise Imported(self.library, self.name)
    def __repr__(self):
        return f"Import(library={self.library}, name={self.name})"

# Interrupt Handler

class InterruptHandler(Exception):
    def __init__(self, exception: str, jump: str):
        self.exception = exception
        self.jump = jump

# Tinder

class Tinder:
    """
    A collection of Kindling instructions that can be executed.  Returns
    the next line of execution or raises an exception if an error occurs.
    """
    jumpTable: Dict[str, int]
    def __init__(self, instructions: List[Tuple[int, Kindling]], **kwargs):
        self.interrupts = {}
        self.instructions = instructions
        self.jumpTable = {inst[1].identifier: i for i, inst in enumerate(self.instructions) if isinstance(inst[1], Goto)}
        super().__init__(**kwargs)
    def __setitem__(self, index: int, instruction):
        self.instructions[index] = instruction
    def __getitem__(self, index: int):
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
            except InterruptHandler as e:
                self.interrupts[e.exception] = e.jump
                continue
            except Yielded as e:
                e.line = line
                raise e
            except Jumped as e:
                e.last = line
                raise e
            except FlowControl as e:
                raise e
            except Exception as e:
                if e.__class__.__name__ in self.interrupts:
                    line = self.jumpTable[self.interrupts[e.__class__.__name__]]
                    raise Jumped(line, line) # convert exception to Jumped
                raise TinderBurn(f"Run failed on line {actual}: {e}") from e
        return line

def getAllSymbols():
    """
    Returns a list of all registered symbols in the Tinderstarter.
    This is useful for introspection or testing purposes.
    """
    return [obj for _, obj in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and issubclass(x, AbstractSymbol) and not inspect.isabstract(x))]

class Tinderstarter(Firestarter):
    def __init__(self, script_type = Tinder):
        super().__init__(grammar=None, strict=True) # type: ignore
        self.script = script_type
        classes = getAllSymbols()
        # Grabs all non-abstract classes so we can just define them and not register them manually
        for obj in classes:
            self.register(obj)
        self.registerDefaults("Write", String(""), Identifier("OUTPUT"))
        self.registerDefaults("Input", String(""), Identifier("INPUT"))

    def compile(self, source: str, version: str) -> Tinder: # type: ignore
        if not source.endswith('\n'):
            source += '\n'
        if version not in GRAMMARS:
            raise TinderBurn(f"Unsupported Tinder version: {version}. Available versions: {list(GRAMMARS.keys())}")
        self.grammar = GRAMMARS[version]
        return super().compile(source, self.script)
