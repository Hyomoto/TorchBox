from typing import Callable, Type, Dict, Set, Tuple, List, Any
from abc import ABC, abstractmethod
import re

SPACES_RE = re.compile(r'[ \t]+')  # Matches whitespace only
NEWLINE_RE = re.compile(r'\n|\r\n|\r')  # Matches newlines in various formats
WHITESPACE_RE = re.compile(r'\s+')  # Matches all whitespace including newlines

class Match:
    """
    Represents a successful match of a rule against the input token stream.

    Stores the rule, and the start and end indices into the token list for the matched span.
    The token stream itself is not stored; all context is derived from the original input.
    """
    def __init__(self, rule: "Rule", start: int, end: int, children: "List[Match] | None" = None, lasterror: "MatchError | None" = None):
        self.rule = rule
        self.start = start
        self.end = end
        self.children = children or []
        self.error = lasterror

    def __iter__(self):
        return self.walk()

    def __getitem__(self, index: int):
        return self.children[index]

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

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
        self.branch = len(self.children) > 1  # True if this error has children, indicating a failed branch

    def lastError(self) -> "MatchError | None":
        """Return the last error in the chain of children."""
        if not self.children: # bottom, return self
            return self
        if self.branch == False: # no branch, continue down the chain
            return self.children[0].lastError()
        # if this is a branch, drill down: if the returned error is branch, return that, otherwise return self
        last = self
        for child in self.children:
            check = child.lastError()
            last = check if check.branch and check.pos > last.pos else last
        return last

    def lastIndex(self) -> int:
        """Return the last index of the matched tokens."""
        if self.children:
            return max(child.lastIndex() for child in self.children)
        return self.pos

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
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
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
            return f"{self.identifier}<{self.__class__.__name__}>(%s)"
        return f"{self.__class__.__name__}(%s)"


class RuleReference(Rule):
    """
    Represents a reference to a rule identified by name.
    During initial parsing, this stands in for rules not yet resolved.
    The reference can be resolved later to point to the actual rule object.
    """
    def __init__(self, identifier: str):
        self.identifier_ = identifier

    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        raise NotImplementedError(
            f"Unresolved rule reference '{self.identifier}' in grammar. "
            "Check that all rules are defined.")

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

    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        """Consume tokens based on the rule."""
        if ignore and ignore.match(tokens, pos):
            pos = ignore.match(tokens, pos).end()
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

    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        """Match if the pattern can consume tokens starting at pos."""
        if ignore and ignore.match(tokens, pos):
            pos = ignore.match(tokens, pos).end()
        match = self.pattern.match(tokens, pos)
        if match:
            return Match(self, pos, match.end())
        raise MatchError(pos, self)

    def __repr__(self):
        return super().__repr__().replace("%s", str(self.pattern))

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
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        pass

    def __eq__(self, other):
        return super().__eq__(other) and self.rule == other.rule


class RuleOneOrMore(RuleSingle):
    """A rule that matches one or more occurrences of a rule."""
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        """Match if the rule can consume one or more tokens."""
        matches = []
        start = pos
        error = None
        while pos < len(tokens):
            try:
                match = self.rule.consume(tokens, pos, ignore)
                matches.append(match)
                pos = match.end
            except MatchError as e:
                error = e
                if matches:  # If we have matched at least one token, return the match
                    break
                raise MatchError(pos, self, [e])  # If no tokens matched, raise an error
        if not matches:
            raise MatchError(pos, self)
        return Match(self, start, pos, matches, lasterror = error)
    
    def visit(self, matches, tokens: str):
        """Visit all matches and return a list of their tokens."""
        
    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleZeroOrMore(RuleSingle):
    """A rule that matches zero or more occurrences of a rule."""
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        """Match if the rule can consume zero or more tokens."""
        matches = []
        start = pos
        while pos < len(tokens):
            try:
                match = self.rule.consume(tokens, pos, ignore)
                matches.append(match)
                pos = match.end
            except MatchError as e:
                return Match(self, start, pos, lasterror = e)
        return Match(self, start, pos, matches)

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleOptional(RuleSingle):
    """A rule that matches zero or one occurrence of a rule."""
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        """Match if the rule can consume zero or one token."""
        try:
            match = self.rule.consume(tokens, pos, ignore)
            return Match(self, match.start, match.end, [match])
        except MatchError as e:
            return Match(self, pos, pos, lasterror = e)

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleAndPredicate(RuleSingle):
    """A rule that succeeds if the inner rule matches, but consumes no tokens."""
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        try:
            self.rule.consume(tokens, pos, ignore)  # Try matching inner rule
            # If successful, return a zero-width match at pos
            return Match(self, pos, pos)
        except MatchError as e:
            raise MatchError(pos, self, [e])

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleNotPredicate(RuleSingle):
    """A rule that succeeds if the inner rule does not match, but consumes no tokens."""
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        try:
            self.rule.consume(tokens, pos, ignore)  # Try matching inner rule
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
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        pass

    def __eq__(self, other):
        return super().__eq__(other) and self.rules == other.rules


class RuleAll(RuleMultiple):
    """A rule that matches all tokens in the input."""
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        """Match if all rules can consume tokens starting at pos."""
        matches = []
        start = pos
        for rule in self.rules:
            try:
                match = rule.consume(tokens, pos, ignore)
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
    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern = None) -> Match:
        """Match if any of the rules can consume tokens starting at pos."""
        unmatched = []
        for rule in self.rules:
            try:
                match = rule.consume(tokens, pos, ignore)
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
    pass

class GrammarParseError(Exception):
    """
    Raised when a grammar fails to parse.
    """
    def __init__(self, index: int, line: int, column: int, token_slice: str, exception: MatchError = None):
        self.index = index
        self.line = line
        self.column = column
        self.tokens = token_slice
        self.exception = exception

    def __str__(self):
        # Build the base header
        last = self.exception.lastError()
        if isinstance(last.expected, RuleSingle):
            expect = last.expected.identifier
        else:
            expect = ', '.join(rule.identifier for rule in last.expected.rules)
        header = f"Expected {expect}"
        # Show exact location and context
        pointer_line = "-" * (self.column - 1) + "^"
        # The input fragment where it stopped, with context
        snippet = self.tokens
        return (
            f"{header} at line {self.line}, column {self.column}:\n"
            f"{snippet}\n"
            f"{pointer_line}"
        )

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

class RuleIgnore:
    NONE = 0x00
    SPACES = 0x01
    NEWLINE = 0x02
    WHITESPACE = SPACES | NEWLINE

IGNORABLE = [None, SPACES_RE, NEWLINE_RE, WHITESPACE_RE]

class Grammar:
    """A grammar definition for the Firestarter parser."""
    def __init__(self, ignore: RuleIgnore = RuleIgnore.NONE):
        self.rule: Rule | None = None
        self.rules: Dict[str, Rule] = {}
        self.dirty = False
        self.ignore = ignore  # bitmask for ignored lexemes (e.g. whitespace, newlines)

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
                raise GrammarError(f"Circular dependency detected in grammar rules. Triggerd by: {toVisit[-1][0]}")
            identifier, base = toVisit.pop(0)
            stack, visited = [base], []
            try:
                while stack:
                    this = stack.pop()
                    if this in visited:
                            continue
                    visited.append(this)
                    if isinstance(this, RuleReference):
                        raise GrammarError(f"Identifier '{this.identifier}' has an unresolved reference as its root rule.")
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
        def getLineInfo(tokens: str, error: MatchError):
            # traverse match error to find the last index that failed to match
            pos = error.lastIndex()
            lines = tokens.split('\n')
            row = tokens.count('\n', 0, pos) + 1
            line = lines[row - 1] if row <= len(lines) else ""
            line_start = tokens.rfind('\n', 0, pos) + 1
            column = pos - line_start + 1
            
            return column, row, line
        """Parse the input tokens using the defined grammar rules."""
        if not self.rule:
            raise RuntimeError(f"No rule defined for {self.__class__.__name__}.")
        if self.dirty:
            self.resolve()
        pos = 0
        matches = []
        ignore = IGNORABLE[self.ignore]
        while pos < len(tokens):
            try:
                match = self.rule.consume(tokens, pos, ignore)
                matches.append(match)
            except MatchError as e:
                col, row, line = getLineInfo(tokens, e)
                raise GrammarParseError(pos, row, col, line, exception = e)
            pos = match.end
        return matches

PEG = Grammar(RuleIgnore.SPACES).register(
        Comment=RuleAll(RuleString("#"), RulePattern(re.compile(r'[^\n]*'))),
        Newline=RuleChoice(RulePattern(NEWLINE_RE)),
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
    def pretty_print(self, tokens: str, strict: bool = True, highlight: str = "\033[94m"):
        """Pretty print the match tree, showing the rule and matched text."""
        reset = "\033[0m"
        def render(match: Match, tokens, depth=0):
            if match.rule.identifier_ :
                out = f"{' ' * depth}{highlight}{match.rule.identifier}{reset}<{match.rule}>:'{match.slice(tokens)}'\n"
            elif not strict:
                out = f"{' ' * depth}{match.rule.__class__.__name__}:'{match.slice(tokens)}'\n"
            else:
                out = ''
            for child in match.children:
                out += render(child, tokens, depth + 2)
            return out
        print(render(self,tokens).rstrip())
    
    if not text.strip():
        raise GrammarError("Empty grammar definition provided.")
    try:
        matches = PEG.parse(text)
    except GrammarParseError as e:
        print(e)
        return
    for match in matches:
        rule, start, end, children = match.rule, match.start, match.end, match.children
        identifier = rule.identifier
        pretty_print(match, text, strict=False)
    return Grammar()
