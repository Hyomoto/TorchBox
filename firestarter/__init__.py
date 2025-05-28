"""

"""
from typing import Callable, Type, Dict, Set, Tuple, List, Any
from abc import ABC, abstractmethod
from .crucible import Crucible
import inspect
import re

SAFE_WHITESPACE_RE = re.compile(r'[ \t]+')  # Matches whitespace only


class Lexeme:
    pattern: re.Pattern = re.compile(r'\S+')
    def __init__(self, text: str, line: int, column: int, override: str = None):  # type: ignore
        self.text = text
        self.line = line
        self.column = column
        self.override = override

    @property
    def value(self) -> Any:
        """Return the value of the lexeme."""
        return self.text

    def __repr__(self):
        return f"{self.override or self.__class__.__name__}(text={self.text!r}, line={self.line}, column={self.column})"


class Whitespace(Lexeme):
    pattern = re.compile(r'\s+')  # Matches whitespace only
    @property
    def value(self) -> str:
        """Return the whitespace character."""
        return self.text


class Match:
    """
    Represents a successful match of a rule against the input token stream.

    Stores the rule, and the start and end indices into the token list for the matched span.
    The token stream itself is not stored; all context is derived from the original input.
    """
    def __init__(self, rule: "Rule", start: int, end: int, children: "List[Match] | None" = None):
        self.rule = rule
        self.start = start
        self.end = end
        self.children = children or []

    def __iter__(self):
        return self.walk()

    def __getitem__(self, index: int):
        return self.children[index]

    def tokens(self, tokens: List[Lexeme]) -> List[Lexeme]:
        """Return the matched tokens from the input token stream."""
        return tokens[self.start:self.end]

    def add_child(self, child: "Match"):
        """Add a child match to this match."""
        self.children.append(child)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def tag(self, tokens: str, pairs=None) -> List[Tuple["Rule", str]]:
        """
        Collects (Rule, str) pairs for all leaves in the match tree.
        """
        pairs = pairs or []
        if not self.children:
            pairs.append(
                (self.rule.__class__.__name__, tokens[self.start:self.end]))
        else:
            for child in self.children:
                child.tag(tokens, pairs)
        return pairs

    def slice(self, tokens: str) -> str:
        """Return the matched text from the input token stream."""
        return tokens[self.start:self.end] if self.start < self.end else ""

    def __eq__(self, other):
        """Check if two matches are equal based on their start and end indices."""
        return isinstance(
            other, Match
        ) and self.start == other.start and self.end == other.end and self.rule == other.rule

    def __len__(self):
        """Return the number of tokens matched by this rule."""
        return self.end - self.start

    def __repr__(self):
        return f"Match(rule={self.rule!r}, start={self.start+1}, end={self.end+1})"


class MatchError(Exception):
    """
    Raised when a parsing rule fails to match at a given input position.

    MatchError is used for both parser backtracking and debugging. It records the
    position and rule where the failure happened, and keeps a list of child MatchErrors
    from any failed sub-rules (such as choices or alternatives). This lets you see
    the full trace of unsuccessful parsing attempts and understand why the parse failed.
    """
    def __init__(self, pos: int, expected: "Rule", children: "List[MatchError] | None" = None, matched: "List[Match] | None" = None):
        self.pos = pos
        self.expected = expected
        self.children = children or []
        self.matched = matched

    def __repr__(self):
        return f"MatchError(pos={self.pos+1}, expected={self.expected}, matched={self.matched})"

    def __str__(self):
        def render(err, depth=0):
            out = f"{' ' * depth}{err!r}\n"
            for child in err.children:
                out += render(child, depth + 2)
            return out
        return render(self).rstrip()


class Rule(ABC):
    """
    Abstract base class for grammar rules used in parsing.

    A Rule defines how to match a specific pattern of lexemes (tokens) in the input.
    Each subclass implements the `consume` method, which tries to match its pattern 
    against a sequence of tokens, starting at a given position. Rules can represent 
    single tokens, sequences, choices, repetitions, or other grammar constructs.
    """
    def __init__(self):
        self.identifier_: str | None = None  # identifier for the rule for reverse lookup
    
    @property
    def identifier(self) -> str:
        """Return the identifier for this rule."""
        if self.identifier_ is None:
            raise NotImplementedError(
                f"Rule {self.__class__.__name__} does not have an identifier set.")
        return self.identifier_

    @abstractmethod
    def consume(self, tokens: str, pos: int = 0) -> Match:
        """
        Checks whether this rule matches the input token stream at position `pos`.

        On success, returns a Match containing the span of tokens.

        If the match fails, raises a MatchError to signal the walker and allow error context
        to be captured. Subclasses must ensure that if a child rule raises MatchError, it is
        caught, wrapped with this rule's context, and re-raised. This preserves a full chain
        of failure states for debugging and parser diagnostics.
        """
        pass

    def __eq__(self, other):
        return isinstance(other, Rule) and self.__class__ == other.__class__

    def __repr__(self):
        return f"{self.__class__.__name__}(%s)"


class RuleReference(Rule):
    """
    Represents a reference to a rule identified by name.
    During initial parsing, this stands in for rules not yet resolved.
    The reference can be resolved later to point to the actual rule object.
    """
    def __init__(self, identifier: str):
        self.identifier_ = identifier
        self.resolvedTo = None

    def resolve(self, rule: Rule):
        self.resolvedTo = rule

    def consume(self, tokens: str, pos: int = 0):
        if self.resolvedTo is None:
            raise NotImplementedError(
                f"Unresolved rule reference '{self.identifier}' in grammar. "
                "Check that all rules are defined.")
        return self.resolvedTo.consume(tokens, pos)

    def __repr__(self):
        return super().__repr__().replace("%s", self.identifier)

# primitive rules

class RulePrimitive(Rule, ABC):
    """Abstract base class for primitive rules that match a specific pattern of lexemes."""
    def __init__(self, pattern: Any):
        super().__init__()
        self.pattern = pattern

class RuleString(RulePrimitive):
    """A rule that matches a specific string."""
    def __init__(self, text: str):
        super().__init__(text)

    def consume(self, tokens: str, pos: int = 0) -> Match:
        """Consume tokens based on the rule."""
        while pos < len(tokens) and tokens[pos] in ' \t\r':
            pos += 1
        if pos < len(tokens) and tokens.startswith(self.pattern, pos):
            return Match(self, pos, pos + len(self.pattern))
        raise MatchError(pos, self)

    def __repr__(self):
        return super().__repr__().replace("%s", self.pattern)

    def __eq__(self, other):
        return super().__eq__(other) and self.pattern == other.pattern


class RulePattern(RulePrimitive):
    """A rule that matches a regular expression pattern."""
    def __init__(self, pattern: re.Pattern):
        super().__init__(pattern)
        
    def consume(self, tokens: str, pos: int = 0) -> Match:
        """Match if the pattern can consume tokens starting at pos."""
        while pos < len(tokens) and tokens[pos] in ' \t\r':
            pos += 1
        match = self.pattern.match(tokens, pos)
        if match:
            return Match(self, pos, match.end())
        raise MatchError(pos, self)

    def __repr__(self):
        return super().__repr__().replace("%s", str(self.pattern))

    def __eq__(self, other):
        return super().__eq__(other) and self.pattern == other.pattern


class RuleClass(RulePattern):
    """A rule that matches a specific class of lexemes."""
    def __init__(self, cls: Lexeme):
        super().__init__(cls.pattern)
    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.pattern))

    def __eq__(self, other):
        return super().__eq__(other) and self.pattern == other.pattern

# single rules

class RuleSingle(Rule, ABC):
    """A rule that matches a single occurrence of another rule."""
    def __init__(self, rule: Rule | str):
        super().__init__()
        if isinstance(rule, str):
            self.rule = RuleReference(rule)
        else:
            self.rule = rule

    @abstractmethod
    def consume(self, tokens: str, pos: int = 0) -> Match:
        pass

    def __eq__(self, other):
        return super().__eq__(other) and self.rule == other.rule


class RuleOneOrMore(RuleSingle):
    """A rule that matches one or more occurrences of a rule."""
    def consume(self, tokens: str, pos: int = 0) -> Match:
        """Match if the rule can consume one or more tokens."""
        matches = []
        start = pos
        while pos < len(tokens):
            start = pos
            try:
                match = self.rule.consume(tokens, pos)
                matches.append(match)
                pos = match.end
            except MatchError as e:
                if matches:  # If we have matched at least one token, return the match
                    break
                raise MatchError(pos, self,
                                 [e])  # If no tokens matched, raise an error
        if not matches:
            raise MatchError(pos, self)
        return Match(self, start, pos, matches)

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleZeroOrMore(RuleSingle):
    """A rule that matches zero or more occurrences of a rule."""
    def consume(self, tokens: str, pos: int = 0) -> Match:
        """Match if the rule can consume zero or more tokens."""
        matches = []
        start = pos
        while pos < len(tokens):
            start = pos
            try:
                match = self.rule.consume(tokens, pos)
                matches.append(match)
                pos = match.end
            except MatchError:
                return Match(self, start, start)
        return Match(self, start, pos, matches)

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleOptional(RuleSingle):
    """A rule that matches zero or one occurrence of a rule."""
    def consume(self, tokens: str, pos: int = 0) -> Match:
        """Match if the rule can consume zero or one token."""
        try:
            match = self.rule.consume(tokens, pos)
            return Match(self, match.start, match.end, [match])
        except MatchError:
            return Match(self, pos, pos)

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleAndPredicate(RuleSingle):
    """A rule that succeeds if the inner rule matches, but consumes no tokens."""
    def consume(self, tokens: str, pos: int = 0) -> Match:
        try:
            self.rule.consume(tokens, pos)  # Try matching inner rule
            # If successful, return a zero-width match at pos
            return Match(self, pos, pos)
        except MatchError as e:
            raise MatchError(pos, self, [e])

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleNotPredicate(RuleSingle):
    """A rule that succeeds if the inner rule does not match, but consumes no tokens."""
    def consume(self, tokens: str, pos: int = 0) -> Match:
        try:
            self.rule.consume(tokens, pos)  # Try matching inner rule
        except MatchError:
            # If it fails, return a zero-width match at pos
            return Match(self, pos, pos)
        raise MatchError(pos, self,
                         None)  # If the inner rule matches, raise an error

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))

# group rules

class RuleMultiple(Rule, ABC):
    """A rule that matches multiple occurrences of other rules."""
    def __init__(self, *rules: Rule | str):
        super().__init__()
        self.rules = [
            RuleReference(rule) if isinstance(rule, str) else rule
            for rule in rules
        ]

    @abstractmethod
    def consume(self, tokens: str, pos: int = 0) -> Match:
        pass

    def __eq__(self, other):
        return super().__eq__(other) and self.rules == other.rules


class RuleAll(RuleMultiple):
    """A rule that matches all tokens in the input."""
    def consume(self, tokens: str, pos: int = 0) -> Match:
        """Match if all rules can consume tokens starting at pos."""
        matches = []
        start = pos
        for rule in self.rules:
            start = pos
            try:
                match = rule.consume(tokens, pos)
                matches.append(match)
                pos = match.end
            except MatchError as e:
                raise MatchError(pos, self, [e], matches)
        return Match(self, start, pos, matches)

    def __repr__(self):
        rules_repr = ", ".join(rule.__class__.__name__ for rule in self.rules)
        return super().__repr__().replace("%s", rules_repr)


class RuleChoice(RuleMultiple):
    """A rule that matches one of several alternatives."""
    def consume(self, tokens: str, pos: int = 0) -> Match:
        """Match if any of the rules can consume tokens starting at pos."""
        unmatched = []
        for rule in self.rules:
            try:
                match = rule.consume(tokens, pos)
                return Match(self, match.start, match.end, [match])
            except MatchError as e:
                unmatched.append(e)
        raise MatchError(pos, self, unmatched)

    def __repr__(self):
        rules_repr = ", ".join(rule.__class__.__name__ for rule in self.rules)
        return super().__repr__().replace("%s", rules_repr)

class Grammar:
    """A grammar definition for the Firestarter parser."""
    def __init__(self):
        self.rule: Rule | None = None
        self.rules: Dict[str, Rule] = {}

    def register(self, **kwargs: Rule):
        """Register a rule with the grammar."""
        for identifier, rule in kwargs.items():
            self.rules[identifier] = rule
            rule.identifier_ = identifier
        return self

    def resolve(self, rule):
        """Resolve all rule references in the grammar."""
        self.rule = rule
        stack: List[Rule] = [rule]
        visited: Set[Rule] = []
        while stack:
            this = stack.pop()
            if this in visited:
                    continue
            visited.append(this)
            if isinstance(this, RuleSingle):
                if isinstance(this.rule, RuleReference):
                    print(f"Resolving {this.rule.identifier} in {this.__class__.__name__}")
                    this.rule = self.rules[this.rule.identifier]
                elif isinstance(this.rule, RuleMultiple) or isinstance(
                        this.rule, RuleSingle):
                    stack.append(this.rule)
            elif isinstance(this, RuleMultiple):
                for i, rule in enumerate(this.rules):
                    if isinstance(rule, RuleReference):
                        print(f"Resolving {rule.identifier} in {this.__class__.__name__}")
                        this.rules[i] = self.rules[rule.identifier]
                    elif isinstance(rule, RuleMultiple) or isinstance(
                            rule, RuleSingle):
                        stack.append(rule)

    def parse(self, tokens: str):
        """Parse the input tokens using the defined grammar rules."""
        if not self.rule:
            raise FirestarterError("No rule defined for grammar.")
        pos = 0
        matches = []
        while pos < len(tokens):
            try:
                match = self.rule.consume(tokens, pos)
                matches.append(match)
                pos = match.end
                if match.end == match.start:
                    raise FirestarterError(
                        f"Rule {self.rule} matched zero-length at position {pos}"
                    )
            except Exception as e:
                line = tokens.count('\n', 0, pos) + 1
                column = pos - tokens.rfind(
                    '\n', 0, pos) if '\n' in tokens[:pos] else pos + 1
                print(f"Error at line {line}, column {column}, position {pos}")
                raise FirestarterError(
                    f"Parsing failed at line {line} column {column} position {pos}: {e}"
                )
        return matches


class Peg(Grammar):
    """A PEG grammar for the Firestarter parser."""
    def __init__(self):
        super().__init__()
        rules = self.rules
        self.register(
            Comment=RuleAll(RuleString("#"), RulePattern(re.compile(r'[^\n]*'))),
            Newline=RuleChoice(RuleString("\n"), RuleString("\r\n"), RuleString("\r")),
            Identifier=RulePattern(re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')),
            RegEx=RulePattern(re.compile(r"~'(?:[^'\\]|\\.)*'")),
            String=RulePattern(re.compile(r'"(?:[^"\\]|\\.)*"')),
            Quantifier=RuleChoice(RuleString("+"), RuleString("*"), RuleString("?"))
        )
        self.register(
            Quantified=RuleAll(RuleChoice(rules["String"], rules["RegEx"], rules["Identifier"], "Group"), rules["Quantifier"]),
            Group=RuleAll(RuleString("("), "Expression", RuleString(")"))
        )
        self.register(Primary=RuleChoice(rules["Quantified"], rules["String"],rules["RegEx"], rules["Identifier"], rules["Group"]))
        self.register(Sequence=RuleAll(rules["Primary"], RuleZeroOrMore(rules["Primary"])))
        self.register(Choice=RuleAll(rules["Sequence"], RuleZeroOrMore(RuleAll(RuleString("/"), rules["Sequence"]))))
        self.register(Expression=rules["Choice"])
        self.register(RuleLine=RuleAll(rules["Identifier"], RuleString("<-"), rules["Expression"], RuleOptional(rules["Newline"])))
        self.register(Line=RuleChoice(rules["Comment"], rules["RuleLine"]))
        self.register(Peg=RuleOneOrMore(RuleAll(rules["Line"], RuleOptional(rules["Newline"]))))
        self.resolve(rules["Peg"])

# Firestarter compiler

class Value(ABC):
    @abstractmethod
    def get(self, env: Crucible) -> Any:
        pass

    @classmethod
    def priority(cls) -> int:
        """Return the priority of the Value."""
        return 0

    @classmethod
    def args(cls) -> List[str]:
        """Return the argument pattern for the Value."""
        args = []
        for name, param in inspect.signature(cls.__init__).parameters.items():
            if name == "self":
                continue
            if param.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD):
                if param.default is inspect.Parameter.empty:
                    args.append(".")  # required
                else:
                    args.append("?")  # optional
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                args.append("*")  # *args
        return args

# primitive

class Primitive(Value):
    """A primitive untyped value."""
    def __init__(self, var: Any):
        self.var = self.primitive(var)

    @property
    def primitive(self) -> Type:
        """The type of the primitive value."""
        return str

    def get(self, env: Crucible) -> Any:
        """Primitive values are directly returned without further processing."""
        return self.var


class FirestarterPEGImportError(Exception):
    """Thrown when a PEG language definition is invalid."""
    def __init__(self, message: str, tokens: str, line: int, column: int):
        near = tokens[max(0, column - 10):min(len(tokens), column + 10)]
        error = f"{message} at {line}:{column} near: {near!r}"
        super().__init__(error)
        self.line = line
        self.column = column


class FirestarterError(Exception):
    """A general error in the Firestarter parser or compiler."""

class Firestarter:
    """A PEG-powered AST and compiler.  Contains the scanner, tokenizer, and parser."""
    def __init__(self, rules: List[Rule] = None):
        default_rules = [
            RuleString, RuleClass, RulePattern, RuleOneOrMore, RuleZeroOrMore,
            RuleOptional, RuleAll, RuleChoice, RuleAndPredicate,
            RuleNotPredicate
        ]
        self.rules_ = rules or default_rules

    def grammar(self, peg: str):
        """Convert the provided PEG grammar into a Rule."""
        pass
