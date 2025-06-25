from firestarter import Firestarter, SymbolReplace, Symbol as AbstractSymbol, Value as AbstractValue
from firestarter.grammar import make_grammar_from_file, Grammar, Flags as GrammarFlags, GrammarError
from firestarter.resolver import Resolver as AbstractResolver
from functools import singledispatchmethod

class Symbol(AbstractSymbol):
    pass

class Bang(Symbol):
    pass

class Plus(Symbol):
    pass

class Minus(Symbol):
    pass

class Mul(Symbol):
    pass

class Div(Symbol):
    pass

class Gt(Symbol):
    pass

class Lt(Symbol):
    pass

class Ge(Symbol):
    pass

class Le(Symbol):
    pass

class Eq(Symbol):
    pass

class Ne(Symbol):
    pass

class Op(Symbol):
    pass

class And(Symbol):
    pass

class Or(Symbol):
    pass

class Primitive(AbstractValue):
    pass

class Operation(AbstractSymbol):
    pass

class AbstractObject(AbstractSymbol):
    pass

class Null(Primitive):
    def __init__(self):
        super().__init__(None)
    def __repr__(self):
        return "Null"
    
class Boolean(Primitive):
    def __init__(self, value: str):
        super().__init__(True if value == "True" else False)
    def __repr__(self):
        return "True" if self.value else "False"
    
class Number(Primitive):
    def __init__(self, value: str):
        try:
            value = float(value)
        except ValueError:
            raise ValueError(f"Invalid number: {value}")
        if value % 1 == 0:
            value = int(value)
        super().__init__(value)
    def __repr__(self):
        return str(self.value)
    
class String(Primitive):
    def __init__(self, value: str):
        if not value.startswith('"') or not value.endswith('"'):
            raise ValueError(f"Invalid string: {value}")
        value = value[1:-1]  # Remove quotes
        super().__init__(value)
    def __repr__(self):
        return f'"{self.value}"'
    
class Identifier(Primitive):
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f"<Identifier: {self.name}>"

class Variable(Identifier):
    pass

class Import(Identifier):
    def __init__(self, name: str):
        super().__init__(name)
    def __repr__(self):
        return f"<Import: {self.name}>"

class Property(Variable):
    def __init__(self, name: str, *values: AbstractValue):
        super().__init__(name)
        self.values = list(values)
    def __repr__(self):
        return f"<Property: {self.name}, Values: {self.values}>"
    
class Action(Variable):
    def __init__(self, name: str, *statements: AbstractSymbol):
        super().__init__(name)
        self.statements = list(statements)
    def __repr__(self):
        return f"<Action: {self.name}, Statements: {self.statements}>"

class Object(AbstractObject):
    def __init__(self, identifier: Identifier, *properties: Property | Action):
        self.identifier = identifier.name
        self.imported = None
        if properties and isinstance(properties[0], Import):
            self.imported = properties[0]
            properties = properties[1:]
        self.properties = {}
        self.actions = {}
        for property in properties:
            if isinstance(property, Property):
                self.properties[property.name] = property
            elif isinstance(property, Action):
                self.actions[property.name] = property
            else:
                raise TypeError(f"Invalid property or action: {property}")
    def __repr__(self):
        return f"<Object: {self.name}, Properties: {self.properties.keys()}, Actions: {self.actions.keys()}>"

class Call(Operation):
    def __init__(self, name: str, *args: AbstractValue):
        self.name = name
        self.args = list(args)
    def __repr__(self):
        return f"<Call: {self.name}, Args: {self.args}>"

class UnaryOp(Operation):
    def __init__(self, operator: Symbol, operand: AbstractValue):
        self.operator = operator
        self.operand = operand
    def __repr__(self):
        return f"<UnaryOp: {self.operator}, Operand: {self.operand}>"

class BinaryOp(Operation):
    def __init__(self, left: AbstractValue, operator: Symbol, right: AbstractValue):
        self.left = left
        self.operator = operator
        self.right = right
    def __repr__(self):
        return f"<BinaryOp: {self.left} {self.operator} {self.right}>"
    
class Block(Operation):
    def __init__(self, *statements: AbstractSymbol):
        self.statements = list(statements)
    def __repr__(self):
        return f"<Block: {len(self.statements)} statements>"

class Condition(Operation):
    def __init__(self, condition: AbstractSymbol, block: Block):
        self.condition = condition
        self.block = block
    def __repr__(self):
        return f"<Condition: {self.condition}, Block: {self.block}>"

class Argument(Identifier):
    def __init__(self, name: str, op: Op = None, default: AbstractValue = None):
        super().__init__(name)
        self.op = op
        self.default = default if default is not None else Null()
    def __repr__(self):
        return f"{self.name}{str(self.op or '')}{' = ' + repr(self.default) if self.default is not None else ''}>"
    
class Arguments(AbstractObject):
    def __init__(self, *args: Argument):
        self.arguments = list(args)
    def __repr__(self):
        return f"<Arguments: {', '.join(repr(arg) for arg in self.arguments)}>"
    
class Function(Operation):
    def __init__(self, identifier: Identifier, *args: AbstractSymbol):
        self.identifier = identifier.name
        self.arguments = []
        if args and isinstance(args[0], Arguments):
            self.arguments = args[0].arguments
            args = args[1:]
        if args:
            self.block: Block = args[-1]
    def __repr__(self):
        return f"<Function: {self.identifier}({', '.join(repr(arg) for arg in self.arguments)}), {self.block}>"
    
class Synonym(AbstractObject):
    def __init__(self, name: str, *aliases: str):
        self.name = name
        self.aliases = list(aliases)
    def __repr__(self):
        return f"<Synonym: {self.name}, Aliases: {self.aliases}>"
    
class SyntaxObject(AbstractObject):
    def __init__(self, *flags: Identifier):
        self.flags = list(flags)
    def __repr__(self):
        return f"<OBJECT ({', '.join(flag.name for flag in self.flags)})>"
    
class Syntax(AbstractObject):
    def __init__(self, name: Identifier, *tokens: Identifier | SyntaxObject):
        self.name = name
        self.tokens = list(tokens)
    def __repr__(self):
        return f"<Syntax: {self.name}, Tokens: {' '.join(repr(token) for token in self.tokens)}>"
    
class Flag(AbstractObject):
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return f"<Flag: {self.name}>"
    
class Namespace(AbstractObject):
    def __init__(self, name: str, *symbols: AbstractSymbol):
        self.name = name
        self.symbols = list(symbols)
    def __repr__(self):
        return f"<Namespace: {self.name}, Symbols: {len(self.symbols)}>"


# Resolver

class Resolver(AbstractResolver):
    """A resolver for symbols in the Tinder language."""
    def __init__(self):
        pass

    @singledispatchmethod
    def resolve(self, node: AbstractSymbol) -> AbstractSymbol:
        return node

TINDER = make_grammar_from_file("tinder.peg", GrammarFlags.IGNORE_WHITESPACE | GrammarFlags.FLATTEN)


with open("base.tinder", "r", encoding="utf-8") as f:
    raw = f.read()

try:
    ast = TINDER.parse(raw)
except GrammarError as e:
    print(e)
    exit(1)

ast.pretty_print()