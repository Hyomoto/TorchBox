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
from .crucible import Crucible, CrucibleError, CrucibleValueNotFound
from .library import Library
from abc import ABC, abstractmethod
from firestarter import Firestarter, SymbolReplace, Symbol as AbstractSymbol, Value as AbstractValue
from firestarter.grammar import make_grammar_from_file, Grammar
from firestarter.grammar import Flags as GrammarFlags
from functools import singledispatchmethod
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
    def __init__(self, carry: Optional[Dict] = None):
        if carry and not isinstance(carry, dict):
            raise TinderBurn(f"Illegal yield with carry: expected dict, got '{type(carry).__name__}'.")
        self.carry = carry
    def __str__(self):
        return f"Yielded(carry={self.carry})"

class Imported(FlowControl):
    """
    Used to import a library.
    """
    def __init__(self, library: str, name: Optional[str] = None, request: Optional[List[str]] = None):
        super().__init__()
        self.library = library
        self.name = name
        self.request = request
    def __repr__(self):
        return f"Imported(library={self.library}, name={self.name}, request={self.request})"

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

class FromSymbol(Symbol):
    pass

class Before(Symbol):
    pass

class After(Symbol):
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

class NoOp(Kindling):
    """A no-operation instruction that does nothing."""
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        pass
    def __repr__(self) -> str:
        return "NoOp()"

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
    def __init__(self, value: Any):
        if value == "True":
            self.value = True
        elif value == "False":
            self.value = False
        else:
            self.value = value
    @property
    def type(self):
        return type(self.value)
    def __repr__(self):
        return f"Constant({self.value!r})"

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
    def transmute(self, env: Crucible):
        if self.value % 1 == 0:
            return int(self.value)
        return float(self.value)
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
    def __init__(self, key: Identifier | String, value: Optional[Kindling] = None):
        self.key = key.value
        self.value = value or key
    @property
    def type(self):
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
        if "_" in self.table:
            return self.table["_"]
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
        self.arguments = Array(*args) if args else None
    def transmute(self, env: Crucible):
        identifier = self.identifier.transmute(env)
        if not callable(identifier):
            raise TinderBurn(f"Identifier '{self.identifier}:{identifier}' is not callable.")
        return identifier(env, *self.arguments.transmute(env) if self.arguments else [])
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

PRECEDENCE = {
    Plus: 2,
    Minus: 2,
    Times: 1,
    Slash: 1,
    LeftAngleBracket: 3,
    RightAngleBracket: 3,
    LeftAngleBracketEqual: 3,
    RightAngleBracketEqual: 3,
    EqualEqual: 4,
    BangEqual: 4,
}

class Binary(AbstractSymbol):
    def __init__(self, *ops: Any):
        # Separate operands and operators
        operands = ops[::2]  # a, b, c, d
        operators = ops[1::2]  # +, *, +

        operand_stack = []
        operator_stack = []

        def apply_operator():
            right = operand_stack.pop()
            left = operand_stack.pop()
            op = operator_stack.pop()
            if isinstance(op, Plus):
                operand_stack.append(Add(left, right))
            elif isinstance(op, Minus):
                operand_stack.append(Subtract(left, right))
            elif isinstance(op, Times):
                operand_stack.append(Multiply(left, right))
            elif isinstance(op, Slash):
                operand_stack.append(Divide(left, right))
            elif isinstance(op, LeftAngleBracket):
                operand_stack.append(Less(left, right))
            elif isinstance(op, RightAngleBracket):
                operand_stack.append(Greater(left, right))
            elif isinstance(op, LeftAngleBracketEqual):
                operand_stack.append(LessEqual(left, right))
            elif isinstance(op, RightAngleBracketEqual):
                operand_stack.append(GreaterEqual(left, right))
            elif isinstance(op, EqualEqual):
                operand_stack.append(Equal(left, right))
            elif isinstance(op, BangEqual):
                operand_stack.append(NotEqual(left, right))
            else:
                raise TinderBurn(f"Unknown binary operator: {op}")

        for i, operand in enumerate(operands):
            operand_stack.append(operand)
            if i < len(operators):
                current_op = operators[i]
                while operator_stack and PRECEDENCE[type(operator_stack[-1])] <= PRECEDENCE[type(current_op)]:
                    apply_operator()
                operator_stack.append(current_op)

        while operator_stack:
            apply_operator()
        if len(operand_stack) != 1:
            raise TinderBurn("Invalid expression tree construction")
        raise SymbolReplace(operand_stack[0])

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

class Indirect(Kindling):
    """Takes the expression evaluation and converts it to a lookup in the environment."""
    def __init__(self, value: Kindling ):
        self.value = value
    def transmute(self, env: Crucible):
        lookup = self.value.transmute(env)
        return env.get(lookup)
    def __repr__(self):
        return f"Indirect({self.value})"

class Access(AbstractSymbol):
    def __init__(self, left: Kindling, symbol: Symbol, right: Kindling):
        match symbol:
            case In():
                raise SymbolReplace(ValueIn(left, right))
            case FromSymbol():
                raise SymbolReplace(ValueFrom(left, right))
            case At():
                raise SymbolReplace(ValueAt(left, right))
            case _:
                raise TinderBurn(f"Unknown access operator: {symbol}")

class ValueFrom(AbstractBinary):
    """Returns where the value is found in the right operand, or None if not found."""
    def __init__(self, left: Kindling, right: Kindling ):
        super().__init__(left, right)
    def transmute(self, env: Crucible):
        right = self.right.transmute(env)
        left = self.left.transmute(env)
        if isinstance(right, list):
            if not isinstance(left, (int, float)):
                raise TinderBurn(f"Left operand must be an integer index, got {type(left).__name__}.")
            if left < 0 or left >= len(right):
                return None
            return right[left]
        if isinstance(right, dict):
            if left not in right:
                if "_" in right:
                    return right["_"]
                return None
            return right[left]
        raise TinderBurn(f"Right operand must be an Array or Table, got {type(right).__name__}.")
    def __repr__(self):
        return super().__repr__().replace("%s", "from")

class ValueIn(AbstractBinary):
    """Returns the left operand if it is found in the right operand, otherwise None."""
    def __init__(self, left: Kindling, right: Kindling ):
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
    def __init__(self, left: Kindling, right: Kindling ):
        super().__init__(left, right)
    def transmute(self, env):
        right = self.right.transmute(env)
        left = self.left.transmute(env)
        if isinstance(right, list):
            if isinstance(left, (int, float)):
                value = right[int(left)]
                return value.transmute(env) if value else None
            raise TinderBurn(f"Left operand must be an integer index, got {type(left).__name__}.")
        if isinstance(right, dict):
            if isinstance(left, str):
                value = right[left]
                return value.transmute(env) if value else None
            raise TinderBurn(f"Left operand must be a string key, got {type(left).__name__}.")
        raise TinderBurn(f"Right operand must be an Array or Table, got {type(right).__name__}.")
    def __repr__(self):
        return super().__repr__().replace("%s", "at")

# statements

class Condition(Kindling):
    def __init__(self, condition: Kindling):
        self.condition = condition
    def transmute(self, env: Crucible):
        result = True if self.condition.transmute(env) else False
        env.set("__CONDITION__", result)
        return result
    def __repr__(self):
        return f"Condition(condition={self.condition})"

class Statement(Kindling):
    """A statement that executes a kindling operation."""
    def __init__(self, operation: "Keyword | Function", condition: Optional[Condition] = None):
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
    
class If(Statement):
    """Sugars a jump to the next endif label when the condition is false."""
    def __init__(self, condition: Condition):
        super().__init__(None, Not(condition))
    def __repr__(self):
        return f"If(operation={self.operation}, condition={self.condition})"
    
class Else(Statement):
    """Sugars a jump to the next endif label and a jump to the next endif label when the condition is false."""
    def __init__(self, condition: Condition = None):
        super().__init__(None, Not(condition) if condition else Constant(False))
        raise SymbolReplace([
            Jump(None),
            self,
        ])
    def __repr__(self):
        return f"Else(operation={self.operation}, condition={self.condition})"

class EndIf(NoOp):
    """
    Marks the end of an if statement block. These need to be resolved by the resolver. These should
    never be run, but they are a form of NoOp in the event that the script is compiled, but not resolved.
    """
    def __repr__(self):
        return "Endif()"

### keywords ###

class Keyword(Kindling):
    """A keyword that represents a special operation that can't resolve at compile time."""
    pass

class Call(AbstractSymbol):
    def __init__(self, callout: Function):
        raise SymbolReplace(callout)

# assignment

class Put(Keyword):
    """Inserts a value into a list or table"""
    def __init__(self, expression: Kindling, op: Symbol, identifier: Identifier):
        self.expression = expression
        self.identifier = identifier
        self.op = op
    def transmute(self, env: Crucible):
        value = self.expression.transmute(env)
        identifier = self.identifier.transmute(env)
        if not isinstance(identifier, list):
            raise TinderBurn(f"Identifier '{self.identifier.value}' is not an array.")
        if isinstance(identifier, list):
            if isinstance(self.op, Before):
                identifier.insert(0, value)
            elif isinstance(self.op, After):
                identifier.append(value)
            else:
                raise TinderBurn(f"Unknown put operation: {self.op.__class__.__name__}")
    def __repr__(self):
        return f"Put(expression={self.expression}, op={self.op.__class__.__name__}, identifier={self.identifier})"

class Inc(AbstractSymbol):
    def __init__(self, identifier: Identifier, expression: Optional[Kindling] = None):
        raise SymbolReplace(Set(identifier, Add(identifier, expression or Number("1"))))

class Dec(AbstractSymbol):
    def __init__(self, identifier: Identifier, expression: Optional[Kindling] = None):
        raise SymbolReplace(Set(identifier, Subtract(identifier, expression or Number("1"))))

class Set(Keyword):
    """Sets a variable in the environment."""
    def __init__(self, *terms: Kindling):
        if len(terms) % 2 != 0:
            raise TinderBurn("Set requires an even number of terms (identifier, value pairs).")
        keys = [key.value for key in terms[:len(terms) // 2]]
        values = terms[len(terms) // 2:]
        self.pairs: List[Tuple[Identifier, Kindling]] = list(zip(keys, values))
    def transmute(self, env: Crucible):
        for identifier, value in self.pairs:
            value = value.transmute(env) if value else None
            env.set(identifier, value)
    def __repr__(self):
        return f"Set(pairs={self.pairs})"

class Swap(Keyword):
    """Swaps the values of two variables in the environment."""
    def __init__(self, left: Identifier, right: Identifier):
        self.left = left.value
        self.right = right.value
    def transmute(self, env: Crucible):
        left = env.get(self.left)
        right = env.get(self.right)
        env.set(self.left, right)
        env.set(self.right, left)
    def __repr__(self):
        return f"Swap(left={self.left}, right={self.right})"

class Const(Set):
    """Flags a variable as a const in the environment for the resolver."""
    def __init__(self, identifier: Identifier, value: Kindling ):
        super().__init__(identifier, value)
    def transmute(self, env):
        super().transmute(env)
        for key, _ in self.pairs:
            env.constants.append(key)
    def __repr__(self):
        return f"Const(pairs={self.pairs})"

# loop sugar

class Foreach(Statement):
    """
    Provides sugar for looping over a list or table.
    # goto a (, b) in c; d
    """
    def __init__(self, *identifier: Identifier ):
        is_dict = len(identifier) == 4
        values = [identifier[0], identifier[1]] if is_dict else [identifier[0]]
        iterable = identifier[2] if is_dict else identifier[1]
        super().__init__(None, Condition(Equal(Identifier("__INDEX__"), Identifier("__LENGTH__"))))
        output = [
            Set(Identifier("__ITER__"), iterable),
            Set(Identifier("__INDEX__"), Number("0")),
            Set(Identifier("__LENGTH__"), Function(Identifier("len"), iterable)),
            self,
        ]
        if len(values) == 1:
            output.append(Set(values[0], ValueFrom(Identifier("__INDEX__"), Identifier("__ITER__"))))
        else:
            output.append(Set(values[0], ValueAt(Identifier("__INDEX__"), Identifier("__ITER__"))))
            output.append(Set(values[1], ValueFrom(values[0], Identifier("__ITER__"))))
        output.append(Set(Identifier("__INDEX__"), Add(Identifier("__INDEX__"), Number("1"))))
        raise SymbolReplace(output)
    def __repr__(self):
        return f"Foreach(operation={self.operation}, condition={self.condition})"

class Foriter(Statement):
    """
    Provides sugar for looping over a list or table.
    # goto a = 0; a < len(b); inc a
    """
    def __init__(self, identifier: Identifier, value: Kindling, condition: Kindling, operation: Kindling):
        super().__init__(None, Not(condition))
        output = [
            Set(identifier, value),
            JumpAhead(1), # bypass the first operation
            operation,
            self,
        ]
        raise SymbolReplace(output)
    def __repr__(self):
        return f"Foriter(operation={self.operation}, condition={self.condition})"

class EndFor(NoOp):
    """
    Marks the end of a for loop block. These need to be resolved by the resolver. These should
    never be run, but they are a form of NoOp in the event that the script is compiled, but not resolved.
    """
    def __init__(self):
        raise SymbolReplace([
            Jump(None),
            self,
        ])
    def __repr__(self):
        return "EndFor()"

# control flow

class Interrupt(Keyword):
    """Redirects execution to a specific line if an exception is raised."""
    def __init__(self, exception: String, jump: Identifier):
        self.exception = exception.value
        self.jump = jump
    def transmute(self, env: Crucible):
        raise InterruptHandler(self.exception, self.jump.transmute(env))
    def __repr__(self):
        return f"Interrupt(exception={self.exception}, jump={self.jump})"

class Jump(Keyword):
    def __init__(self, identifier: Kindling ):
        self.identifier = identifier
    def transmute(self, env: Crucible):
        try:
            line = self.identifier.transmute(env)
            env.set("__JUMPED__", env.get("__LINE__"))
            env.set("__LINE__", line + 1)
        except CrucibleError as e:
            raise TinderBurn(f"{e}")
        if not isinstance(line, (int, float)):
            raise TinderBurn(f"Jump target '{self.identifier}' is not a number ({line}).")
    def __repr__(self):
        return f"Jump(identifier={self.identifier})"
    
class JumpAhead(Keyword):
    """Jumps ahead a specified number of lines."""
    def __init__(self, lines: int ):
        self.lines = lines
    def transmute(self, env: Crucible):
        env.set("__LINE__", env.get("__LINE__") + self.lines)
    def __repr__(self):
        return f"JumpAhead(lines={self.lines})"

class Return(Keyword):
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        try:
            env.set("__JUMPED__", env.get("__LINE__"))
        except CrucibleError:
            raise TinderBurn(f"No return target found in environment.")
    def __repr__(self):
        return "Return()"

class Goto(Keyword):
    """A no-operation instruction used to flag line numbers by name."""
    def __init__(self, identifier: Identifier | String, otherwise: Optional[Identifier | Foreach | Foriter] = None):
        self.identifier: str = identifier.value
        self.otherwise = Jump(otherwise) if otherwise else None
    def transmute(self, env: Crucible):
        if self.otherwise: # if otherwise, yield to it
            self.otherwise.transmute(env)
    def __repr__(self):
        return f"Goto(identifier={self.identifier}, otherwise={self.otherwise})"

class Stop(Keyword):
    """Stops the execution of the Tinder."""
    def __init__(self):
        pass
    def transmute(self, env: Crucible):
        raise Halted()
    def __repr__(self):
        return "Stop()"

class Yield(Keyword):
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

class Input(Keyword):
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

class Write(Keyword):
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

class Import(Keyword):
    """Imports a library into the environment."""
    def __init__(self, library: Identifier, name: Optional[Identifier] = None):
        self.library = library.value
        self.name = name.value if name else None
    def transmute(self, env: Crucible):
        raise Imported(self.library, self.name)
    def __repr__(self):
        return f"Import(library={self.library}, name={self.name})"

class From(Keyword):
    """Imports one or more specific symbols from a library into the environment."""
    def __init__(self, library: Identifier, *symbols: Identifier):
        self.library = library.value
        self.symbols = [symbol.value for symbol in symbols]
    def transmute(self, env: Crucible):
        raise Imported(self.library, request=self.symbols)
    def __repr__(self):
        return f"From(library={self.library}, symbols={self.symbols})"

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
        list = '\n\t'.join(str(i).ljust(4) + repr(inst) for i, inst in enumerate(self.instructions))
        return f"Tinder[{len(self)} lines](\n\t{list}\n)"

    def writeJumpTable(self, env: Crucible):
        env.update(self.jumpTable)
        return env

    def run(self, env: Crucible):
        if "__LINE__" not in env:
            env.set("__LINE__", 0)
        while True:
            line = env.get("__LINE__")
            if line < 0 or line >= len(self.instructions):
                break
            actual, op = self.instructions[line]
            try:
                env.set("__LINE__", line + 1)
                op.transmute(env)
            except InterruptHandler as e:
                self.interrupts[e.exception] = e.jump
            except FlowControl as e:
                env.set("__LINE__", line + 1)
                raise e
            except Exception as e:
                if e.__class__.__name__ in self.interrupts:
                    line = self.interrupts[e.__class__.__name__]
                    Jump(Constant(line)).transmute(env)
                    continue
                else:
                    raise TinderBurn(f"Run failed on line {actual}: {e}") from e
        raise Halted() # end of execution

def getAllSymbols():
    """
    Returns a list of all registered symbols in the Tinderstarter.
    This is useful for introspection or testing purposes.
    """
    return [obj for _, obj in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and issubclass(x, AbstractSymbol) and not inspect.isabstract(x))]

class Tinderstarter(Firestarter):
    def __init__(self, script_type = Tinder, libs: Dict[str, Library] = {}):
        super().__init__(grammar=None, strict=True) # type: ignore
        self.resolver = TinderResolver()
        self.script = script_type
        self.libs = libs
        classes = getAllSymbols()
        # Grabs all non-abstract classes so we can just define them and not register them manually
        for obj in classes:
            self.register(obj)
        self.registerDefaults("Write", String(""), Identifier("OUTPUT"))
        self.registerDefaults("Input", String(""), Identifier("INPUT"))

    def compile(self, source: str, version: str, env: dict = {}) -> Tinder: # type: ignore
        resolver = self.resolver
        if not source.endswith('\n'):
            source += '\n'
        if version not in GRAMMARS:
            raise TinderBurn(f"Unsupported Tinder version: {version}. Available versions: {list(GRAMMARS.keys())}")
        self.grammar = GRAMMARS[version]
        script: Tinder = super().compile(source, self.script)
        print(script)
        resolver.libs = self.libs
        crucible = Crucible().update(env)
        crucible.update(script.jumpTable, constants=True)
        resolver.env = crucible
        script = resolver.resolve(script)
        return script


# Resolver

class TinderResolver:
    """A resolver for Tinder kindlings that resolves all kindlings to constants where possible."""
    def __init__(self):
        self.env = Crucible()
        self.libs: Dict[str, Library] = {}
        self.blocks: List[List] = []
        self.instruction: int = 0
        
    @singledispatchmethod
    def resolve(self, node: Kindling):
        """Try to resolve a Kindling."""
        if (self.resolveChildren(node)):
            try:
                return Constant(node.transmute(self.env))
            except Exception:
                pass
        return node
    
    @resolve.register
    def _(self, node: If):
        self.blocks.append([node])
        node.condition = self.resolve(node.condition)
        return node
    
    @resolve.register
    def _(self, node: Foreach | Foriter):
        self.blocks.append([node, self.instruction])
        node.condition = self.resolve(node.condition)
        return node

    @resolve.register
    def _(self, node: Else):
        if not self.blocks or type(self.blocks[-1][0]) is not If:
            raise TinderBurn("Else without If block.")
        print(self.blocks[-1][-2])
        self.blocks[-1][-2].operation = Jump(Constant(self.instruction - 1))
        self.blocks[-1].append(node)
        node.condition = self.resolve(node.condition)
        return node

    @resolve.register
    def _(self, node: EndIf):
        if not self.blocks or type(self.blocks[-1][0]) is not If:
            raise TinderBurn("EndIf without If block.")
        block = self.blocks.pop()
        block[-1].operation = Jump(Constant(self.instruction - 1))
        for statement in block:
            if isinstance(statement, Jump):
                statement.identifier = Constant(self.instruction - 1)
        return node
    
    @resolve.register
    def _(self, node: EndFor):
        if not self.blocks or (type(self.blocks[-1][0]) is not Foriter and type(self.blocks[-1][0]) is not Foreach):
            raise TinderBurn("EndFor without For block.")
        block = self.blocks.pop()
        jump = block.pop()
        jump.identifier = Constant(block.pop() - 2 )
        block[-1].operation = Jump(Constant(self.instruction - 1))
        return node
    
    @resolve.register
    def _(self, node: Jump):
        if node.identifier is None:
            if not self.blocks:
                raise TinderBurn("Else Jump without If block.")
            self.blocks[-1].append(node)
        return node

    @resolve.register
    def _(self, node: Tinder):
        self.block = 0
        for i, (line, instruction) in enumerate(node.instructions):
            self.instruction = i
            if isinstance(instruction, Kindling):
                print(f"Resolving instruction {i} at line {line}: {instruction}")
                node.instructions[i] = (line, self.resolve(instruction))
        return node

    @resolve.register
    def _(self, node: Import | From):
        try:
            node.transmute(self.env)
        except Imported as e:
            if e.library not in self.libs:
                return node
            lib = self.libs.get(e.library)
            if e.request:
                self.env.update(lib.export(e.request))
            else:
                self.env[e.name or e.library] = lib.export()
        return node

    @resolve.register
    def _(self, node: Condition):
        return node

    @resolve.register
    def _(self, node: Statement):
        self.resolveChildren(node)
        return node

    @resolve.register
    def _(self, node: Function):
        try:
            func = node.identifier.transmute(self.env)
        except CrucibleError:
            return node
        if getattr(func, "_resolvable", False):
            try:
                return Constant(func(self.env, *node.arguments.transmute(self.env) if node.arguments else []))
            except Exception:
                pass
        return node

    @resolve.register
    def _(self, node: Set | Const):
        for i, (key, value) in enumerate(node.pairs):
            try:
                node.pairs[i] = (key, self.resolve(value))
                self.env.set(key, node.pairs[i][1].transmute(self.env))
                if isinstance(node, Const):
                    self.env.constants.append(key)
            except Exception:
                pass
        return node

    @resolve.register
    def _(self, node: Identifier):
        if node.value in self.env.constants:
            try:
                value = node.transmute(self.env)
                return Constant(value)
            except Exception:
                pass
        return node

    @resolve.register
    def _(self, node: Constant):
        return node
    
    @resolve.register
    def _(self, node: Condition):
        """Resolve a condition to a constant if possible."""
        return self.resolve(node.condition)

    @singledispatchmethod
    def resolveChildren(self, node: Kindling):
        """Recursively resolve all child kindlings."""
        count, tried = 0, 0
        for attr in vars(node):
            tried += 1
            value = getattr(node, attr)
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, Kindling):
                        value[i] = self.resolve(item)
            elif isinstance(value, Kindling):
                setattr(node, attr, self.resolve(value))
            count += 1 if isinstance(getattr(node, attr), Constant) else 0
        return count == tried # all children resolved to constants

    @resolveChildren.register
    def _(self, node: Array):
        count = 0
        for i in range(len(node.list)):
            node.list[i] = self.resolve(node.list[i])
            count += 1 if isinstance(node.list[i], Constant) else 0
        return count == len(node.list) # whole list is resolved to constants

    @resolveChildren.register
    def _(self, node: Table):
        count = 0
        for key, value in node.table.items():
            node.table[key] = self.resolve(value)
            count += 1 if isinstance(node.table[key], Constant) else 0
        return count == len(node.table) # whole table is resolved to constants
