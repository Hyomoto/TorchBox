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

        If the match fails, raises a MatchError to signal the walker and allow
        error context to be captured. Subclasses must ensure that if a child rule
        raises MatchError, it is caught, wrapped with this rule's context, and
        re-raised. This preserves a full chain of failure states for debugging
        and parser diagnostics.
        """
        pass

    def __eq__(self, other):
        return isinstance(other, Rule) and self.__class__ == other.__class__

    def __repr__(self):
        if self.identifier_:
            return f"{self.__class__.__name__}<{self.identifier}>(%s)"
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


class GrammarError(Exception):
    """
    Raised when a grammar fails to parse.  Contains the index the failure
    occurred at, the line and column number, and the MatchError that caused
    the failure.
    """
    def __init__(self, index: int, line: int, column: int, match: MatchError):
        self.match = match
        self.index = index
        self.line = line
        self.column = column

class GrammarParseError(Exception):
    """
    Raised when a grammar fails to parse.
    """
    pass

class GrammarDeferResolve(Exception):
    """
    Raised when a grammar rule cannot be resolved immediately.
    This is used to defer resolution of rules until all rules are defined.
    """
    def __init__(self, identifier: str):
        super().__init__(f"Rule '{identifier}' could not be resolved.")
        self.identifier = identifier

class GrammarMissingResolve(Exception):
    """
    Raised when a grammar rule is missing during resolution.
    This indicates that the rule was not found in the grammar's defined rules.
    """
    def __init__(self, identifier: str):
        super().__init__(f"Rule '{identifier}' is missing from the grammar.")
        self.identifier = identifier


class Grammar:
    """A grammar definition for the Firestarter parser."""
    def __init__(self):
        self.rule: Rule | None = None
        self.rules: Dict[str, Rule] = {}
        self.dirty = False

    def register(self, **kwargs: Rule):
        """Register a rule with the grammar."""
        for identifier, rule in kwargs.items():
            if isinstance(rule, str):
                raise GrammarError(f"Root of '{identifier}' must be an instance of Rule, not an unresolved string!")
            self.rules[identifier] = rule
            rule.identifier_ = identifier
            self.rule = rule # last registered rule becomes the root
        self.dirty = True
        return self

    def resolve(self):
        """Resolve all rule references in the grammar."""
        def handle_rule(rule, callback):
            nonlocal stack, misses
            if isinstance(rule, RuleReference):
                if isinstance(self.rules[rule.identifier], RuleReference):
                    misses += 1
                    raise GrammarDeferResolve(rule.identifier)
                if rule.identifier not in self.rules:
                    raise GrammarMissingResolve(rule.identifier)
                callback(self.rules[rule.identifier])
            else:
                stack.append(rule)
        
        toVisit = [(identifier, base) for identifier, base in self.rules.items()]
        misses = 0
        while toVisit:
            if misses == len(self.rules):
                raise GrammarParseError(f"Circular dependency detected in grammar rules. Triggerd by: {toVisit[-1][0]}")
            identifier, base = toVisit.pop(0)
            stack, visited = [base], []
            try:
                while stack:
                    this = stack.pop()
                    if this in visited:
                            continue
                    visited.append(this)
                    if isinstance(this, RuleReference):
                        raise GrammarParseError(f"Identifier '{this.identifier}' has an unresolved reference as its root rule.")
                    elif isinstance(this, RuleSingle):
                        def assign(x): setattr(this, "rule", x)
                        handle_rule(this.rule, assign)
                    elif isinstance(this, RuleMultiple):
                        for i, rule in enumerate(this.rules):
                            def assign(x, i=i): this.rules.__setitem__(i, x) # type: ignore
                            handle_rule(rule, assign)
            except GrammarDeferResolve as e:
                toVisit.append((identifier, base))
        return self
    
    def parse(self, tokens: str):
        """Parse the input tokens using the defined grammar rules."""
        if not self.rule:
            raise RuntimeError(f"No rule defined for {self.__class__.__name__}.")
        if self.dirty:
            print("Resolving grammar rules...")
            self.resolve()
        pos = 0
        matches = []
        while pos < len(tokens):
            try:
                match = self.rule.consume(tokens, pos)
                matches.append(match)
                pos = match.end
            except MatchError as e:
                line = tokens.count('\n', 0, pos) + 1
                column = pos - tokens.rfind(
                    '\n', 0, pos) if '\n' in tokens[:pos] else pos + 1
                raise GrammarError(pos, line, column, e)
            if match.end == match.start:
                raise MatchError(pos, match.rule, None, matches)
        return matches

PEG = Grammar().register(
        Comment=RuleAll(RuleString("#"), RulePattern(re.compile(r'[^\n]*'))),
        Newline=RuleChoice(RuleString("\n"), RuleString("\r\n"), RuleString("\r")),
        Identifier=RulePattern(re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')),
        RegEx=RulePattern(re.compile(r"~'(?:[^'\\]|\\.)*'")),
        String=RulePattern(re.compile(r'"(?:[^"\\]|\\.)*"')),
        Quantifier=RuleChoice(RuleString("+"), RuleString("*"), RuleString("?")),
        Quantified=RuleAll(RuleChoice("String", "RegEx", "Identifier", "Group"), "Quantifier"),
        Group=RuleAll(RuleString("("), "Expression", RuleString(")")),
        Primary=RuleChoice("Quantified", "String", "RegEx", "Identifier", "Group"),
        Sequence=RuleAll("Primary", RuleZeroOrMore("Primary")),
        Choice=RuleAll("Sequence", RuleZeroOrMore(RuleAll(RuleString("/"), "Sequence"))),
        Expression=RuleAll("Choice"),
        RuleLine=RuleAll("Identifier", RuleString("<-"), "Expression", RuleOptional("Newline")),
        Line=RuleChoice("Comment", "RuleLine"),
        Peg=RuleOneOrMore(RuleAll("Line", RuleOptional("Newline")))
    ).resolve()

def make_grammar_from_file(file_path: str) -> Grammar:
    """
    Load a grammar from a file.

    This function reads the grammar definition from the specified file and returns a Grammar object.
    It raises GrammarError if the grammar is invalid or cannot be resolved.
    """
    with open(file_path, 'r') as f:
        text = f.read()
    return make_grammar(text)

def make_grammar(text: str) -> Grammar:
    """
    Load a grammar from a string definition.

    This function parses the grammar text and returns a Grammar object.
    It raises GrammarError if the grammar is invalid or cannot be resolved.
    """
    if not text.strip():
        raise GrammarError("Empty grammar definition provided.")
    matches = PEG.parse(text)
    
    return grammar