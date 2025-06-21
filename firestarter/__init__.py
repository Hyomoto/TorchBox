"""
Firestarter: a PEG-to-IL compiler frontend for language-agnostic symbolic execution.

This module provides the Firestarter compiler, which transforms tokenized source
strings—parsed using a user-defined PEG grammar—into a sequence of symbolic operations
(Symbols) suitable for interpretation, evaluation, or further compilation. The
Firestarter system is language-agnostic and decouples syntax from semantics, allowing
grammars and runtime behavior to evolve independently.

### Argument Patterns

Argument patterns for operations are inferred from Symbol class constructors using
Python type annotations. The conventions are:

    - T:         required argument of type T (e.g., str, Identifier, Symbol subclass)
    - Optional[T]: optional argument, inserted as None if not present
    - List[T]:   variadic arguments, consumes all remaining of type T
    - Symbol instance: literal injected value

**Type checking is enforced by default (strict mode).** Setting `strict=False` disables
type validation for more permissive or high-performance use cases.

### Symbols vs. Values

- **Symbol**: Abstract base for all opcodes and operations; structural nodes in the
    compiled instruction tree.
- **Value**: Special subclass of Symbol that wraps a literal (e.g., string, number).
    Values allow semantic matching by exposing their internal type, enabling constructs
    like `String("foo")` to satisfy both `String` and `str` expectations.

Typical workflow:
    1. Define a PEG grammar.
    2. Register Symbol subclasses as opcodes (and optionally Value subclasses for literals).
    3. Compile token strings into Symbol-based instruction sequences.
    4. Pass the result to an interpreter or VM for execution.

This model favors flexibility, determinism, and long-term maintainability.
"""
from typing import List, Union, Tuple, Type, Any, Optional, Dict, get_origin, get_args, get_type_hints
from types import UnionType
from abc import ABC, abstractmethod
from .grammar import Grammar, GrammarError, Match, RulePrimitive, AST
import inspect

from constants import RED, RESET

# Firestarter compiler

class Symbol(ABC):
    """
    Abstract base class for all symbolic operations in the Firestarter compiler.

    A Symbol represents a node in the compiled instruction tree (opcode, operation, or structural element).
    Subclasses define their constructor signature with type annotations, which are used to infer argument
    patterns as described in the module docstring.

    Interpretation and execution are handled externally.
    """
    @abstractmethod
    def __init__(self, *args):
        pass

    @classmethod
    def args(cls) -> List[str]:
        """Returns a list of argument names from the class's __init__ method."""
        result = []
        sig = inspect.signature(cls.__init__)
        annotations = get_type_hints(cls.__init__)

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            annotation = annotations.get(name, Symbol)

            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                expected = List[annotation]
            elif param.default is None and get_origin(annotation) is not Union:
                expected = Optional[annotation]
            else:
                expected = annotation
            result.append(expected)
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.__class__ == other.__class__

    def __repr__(self):
        return f"{self.__class__.__name__}(%s)"

class Value(Symbol):
    """
    Base class for symbols representing literal values.

    A Value wraps a typed constant (such as a string or number) and exposes its native
    type via the `type` property, allowing type-based pattern matching as described
    in the module docstring. This enables grammars to express language literals while
    keeping the compiler agnostic to specific value types.
    """
    def __init__(self, value: Any):
        """Initialize with a value based on type."""
        super().__init__()
        self.value = self.type(value)

    @property
    @abstractmethod
    def type(self) -> Any:
        pass

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Value):
            return False
        return self.__class__ == other.__class__ and self.value == other.value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

class SymbolReplace(Exception):
    """Thrown when a Symbol needs to be replaced during compilation."""
    def __init__(self, new: Symbol | List[Symbol]):
        self.new = new

class FirestarterError(Exception):
    """
    Raised when compilation fails due to a malformed AST, invalid pattern, or
    unregistered operation.

    This exception is used to signal structural or semantic errors encountered
    during parsing or compilation, typically when reducing the PEG-parsed input
    into Symbol operations.
    """
    pass

class Firestarter:
    """
    A compiler frontend that transforms PEG-parsed source code into executable Symbol
    operations.

    Firestarter manages opcode registration, grammar parsing, and reduction of the AST
    into a sequence of Symbol instances. Argument patterns for each operation are
    inferred from Python type annotations on Symbol constructors (see module docstring
    for conventions).

    Type checking is enabled by default (`strict=True`). Setting `strict=False`
    disables type validation for argument matching.

    Typical usage:
        - Register opcodes and (optionally) aliases.
        - Compile source code into a Symbol tree.
        - Pass results to an interpreter or executor.

    Parameters:
        grammar (Grammar): The grammar used to parse input source code.
        strict (bool): Whether to enforce type checking on arguments (default: True).
    """
    def __init__(self, grammar: Grammar, strict: bool = True):
        self.opcodes = {}
        self.constants = {}
        self.grammar = grammar
        self.strict = strict

    def __repr__(self):
        return f"Firestarter(opcodes={list(self.opcodes.keys())}, strict={self.strict})"

    def register(self, op: Type[Symbol], name: Optional[str] = None):
        """
        Internal helper for registering a keyword with a pattern and its
        corresponding operation.
        """
        if not isinstance(op, type) or not issubclass(op, Symbol):
            raise TypeError(f"Expected a Symbol class, got {op.__name__}")
        if not name:
            name = op.__name__
        self.opcodes[name] = (op, None)
        return self

    def registerDefaults(self, name: str, *args: Symbol | Type[Any]):
        """
        Internal helper for registering a keyword with a pattern and its
        corresponding constant value.
        """
        if name not in self.opcodes:
            raise ValueError(f"Operation {name} not registered.")
        op, _ = self.opcodes[name]
        self.opcodes[name] = (op, list(args))
        return self

    def compile(self, tokens: str, asType: type = list):
        """
        Compile a source string into a concrete representation of operations.

        This method parses the input `tokens` using the Firestarter's PEG-based grammar,
        producing an abstract syntax tree (AST). It then traverses the tree in post-order,
        resolving each node into a Symbol-based operation using the compiler's registered
        opcodes.

        The resulting operations are collected and passed to the `asType` constructor,
        which determines how to finalize the result. For example, `asType` might wrap
        the list of Symbols in a container type like `Document(...)`, or return them as-is.

        Parameters:
            tokens (str): The input source code to compile.
            asType (type): A callable that accepts the final list of operations and
                        returns a reified object representing the compiled result.
        """
        ast = self.parseTokens(tokens)
        return self.compileAst(ast, asType)

    def parseTokens(self, tokens: str):
        """
        Parse a string of tokens into an abstract syntax tree (AST) using the registered grammar.
        """
        try:
            ast = self.grammar.parse(tokens)
        except GrammarError as e:
            raise FirestarterError(f"Failed to parse tokens: {e}")
        if not ast:
            raise FirestarterError("No valid AST generated from tokens.")
        return ast

    def compileAst(self, ast: AST, asType: type = list):
        """
        Compiles a source AST into a concrete representation of operations.

        It traverses the tree in post-order, resolving each node into a Symbol-based
        operation using the compiler's registered opcodes.

        The resulting operations are collected and passed to the `asType` constructor,
        which determines how to finalize the result. This design exists because the
        grammar may not produce a single top-level operation, and the compiler itself
        cannot infer the output type. For example, `asType` might wrap the list of
        Symbols in a container type like `Document(...)`, or return them as-is.

        Parameters:
            ast (AST): The abstract syntax tree to compile, produced by the grammar.
            asType (type): A callable that accepts the final list of operations and
                        returns a reified object representing the compiled result.
        """
        def getPattern(op, pattern: List[Type[Symbol]], args: List[Symbol], defaults: List[Symbol | None]):
            def typeCheck(arg, expected):
                if not self.strict:
                    return True
                # Any
                if expected is Any:
                    return True
                # UnionType
                if type(expected) is UnionType:
                    for sub in get_args(expected):
                        if typeCheck(arg, sub):
                            return True
                    return False
                # Value.type special case
                if isinstance(arg, Value):
                    if issubclass(arg.type, expected):
                        return True
                # Basic Match
                return isinstance(arg, expected)

            result = []

            for i, p in enumerate(pattern):
                origin = get_origin(p)
                inner = get_args(p)

                # Optional[T]
                if origin is Union and type(None) in inner:
                    if len(args) < len(pattern):
                        if i < len(defaults or []):
                            if typeCheck(defaults[i], inner):
                                result.append(defaults[i])
                            else:
                                raise FirestarterError(f"Argument {defaults[i]} does not match expected type {inner} for {op.__name__}.") 
                        else:
                            result.append(None)
                        continue

                # List[T]
                if origin in (list, List):
                    expected = inner[0] if inner else object
                    #if i >= len(args):
                    #    raise FirestarterError(f"Missing required arguments for variadic {op.__name__}.")
                    remaining = args[i:]
                    if not all(typeCheck(arg, expected) for arg in remaining):
                        raise FirestarterError(f"Expected list of {expected.__name__} for {op.__name__}.")
                    result.extend(remaining)
                    break # List must be last in pattern

                # Simple required type (Symbol subclass or base type)
                if i >= len(args):
                    raise FirestarterError(f"Missing required argument {i} for {op.__name__}.")
                if typeCheck(args[i], p):
                    result.append(args[i])
                else:
                    raise FirestarterError(f"Argument {args[i]} does not match expected type {p} for {op.__name__}.")
            try:
                result = op(*result)
            except SymbolReplace as e:
                return e.new
            return result

        stack: List[Tuple[Match,int,List]] = []
        results = []
        lineNumbers = ast.lineNumbers

        for node in ast.matches:
            stack.append((node,0,[node.rule.identity]))

            while stack:
                node, i, args = stack[-1] # look at last node

                if i == len(node.children): # finished traveral? push to previous scope
                    name = args.pop(0)  # get operation name
                    if name not in self.opcodes:
                        raise FirestarterError(f"Error on line {lineNumbers.pop(0)}: operation {name} not registered.")
                    op, defaults = self.opcodes[name]

                    pattern = op.args()
                    try:
                        output = getPattern(op, pattern, args, defaults) # type checking an optional injection
                    except FirestarterError as e:
                        raise FirestarterError(f"Error on line {lineNumbers.pop(0)}: {e}")
                    stack.pop()  # pop current node from stack
                    if stack:
                        if isinstance(output, list):
                            stack[-1][2].extend(output)
                        else:
                            stack[-1][2].append(output)
                    else:
                        number = lineNumbers.pop(0)
                        if isinstance(output, list):
                            for item in output:
                                results.append((number, item))
                        else:
                            results.append((number, output))
                else:
                    child = node.children[i]
                    stack[-1] = (node, i + 1, args)  # increment index for next iteration
                    identity = child.rule.identity
                    if identity not in self.opcodes:
                        raise FirestarterError(f"Error on line {lineNumbers.pop(0)}: operation {identity} not registered.")
                    if isinstance(child.rule, RulePrimitive): # Primitive node, directly append to results
                        stack.append((child,0,[identity,child.slice(ast.tokens)]))
                    else: # Non-primitive node, push to stack for further processing
                        stack.append((child,0,[identity]))
        return asType(results)