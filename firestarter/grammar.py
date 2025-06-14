from typing import Callable, Generator, Type, Dict, Set, Tuple, List, Any
from abc import ABC, abstractmethod
import copy
import re

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

    def walk(self) -> Generator["Match", None, None]:
        yield self
        for child in self.children:
            yield from child.walk()

    def slice(self, tokens: str) -> str:
        """Return the matched text from the input token stream."""
        return tokens[self.start:self.end] if self.start < self.end else ""

    def __iter__(self):
        return self.walk()

    def __getitem__(self, index: int):
        return self.children[index]

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
        self.parent: MatchError | None = None  # Parent MatchError, if any
        for child in self.children:
            child.parent = self

    def walk(self) -> Generator["MatchError", None, None]:
        yield self
        for child in self.children:
            yield from child.walk()

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
        self.identity: str | None = None  # identifier for the rule for reverse lookup
        self.strict: bool = False # suspends ignores when true, srictly parsed

    def consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
        """Consume tokens based on the rule."""
        if self.strict:
            ignore = None
        return self._consume(tokens, pos, ignore)

    @abstractmethod
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
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

    def duplicate(self) -> "Rule":
        """Create a duplicate of this rule."""
        return copy.deepcopy(self)

    def __eq__(self, other):
        return isinstance(other, Rule) and self.__class__ == other.__class__

    def __repr__(self):
        if self.identity:
            return f"{self.identity}<{self.__class__.__name__}>(%s)"
        return f"{self.__class__.__name__}(%s)"


class RuleReference(Rule):
    """
    Represents a reference to a rule identified by name.
    During initial parsing, this stands in for rules not yet resolved.
    The reference can be resolved later to point to the actual rule object.
    """
    def __init__(self, identifier: str):
        self.identity = identifier

    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
        raise NotImplementedError(
            f"Unresolved rule reference '{self.identity}' in grammar. "
            "Check that all rules are defined.")

    def __repr__(self):
        return super().__repr__().replace("%s", str(self.identity))

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

    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
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
        self.regex = pattern
        super().__init__(pattern.pattern.replace("\\\\", "\\"))  # escape backslashes for display

    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
        """Match if the pattern can consume tokens starting at pos."""
        if ignore and ignore.match(tokens, pos):
            pos = ignore.match(tokens, pos).end()
        match = self.regex.match(tokens, pos)
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

    def __eq__(self, other):
        return super().__eq__(other) and self.rule == other.rule


class RuleOneOrMore(RuleSingle):
    """A rule that matches one or more occurrences of a rule."""
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
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

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleZeroOrMore(RuleSingle):
    """A rule that matches zero or more occurrences of a rule."""
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
        """Match if the rule can consume zero or more tokens."""
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
                break
        return Match(self, start, pos, matches, lasterror = error)

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleOptional(RuleSingle):
    """A rule that matches zero or one occurrence of a rule."""
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
        """Match if the rule can consume zero or one token."""
        try:
            match = self.rule.consume(tokens, pos, ignore)
            return Match(self, match.start, match.end, [match])
        except MatchError as e:
            return Match(self, pos, pos, lasterror = e)

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))

# Predicates

class RulePredicate(RuleSingle, ABC):
    """Abstract base class for predicates that check conditions on rules."""

class RuleAndPredicate(RulePredicate):
    """A rule that succeeds if the inner rule matches, but consumes no tokens."""
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
        try:
            match = self.rule.consume(tokens, pos, ignore)  # Try matching inner rule, never ignore tokens all are considered significant
            # If successful, return a zero-width match at pos
            return Match(self, pos, pos, [match])
        except MatchError as e:
            raise MatchError(pos, self, [e])

    def __repr__(self):
        return super().__repr__().replace("%s", repr(self.rule))


class RuleNotPredicate(RulePredicate):
    """A rule that succeeds if the inner rule does not match, but consumes no tokens."""
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
        try:
            match = self.rule.consume(tokens, pos, ignore)
        except MatchError as e:
            # If it fails, return a zero-width match at pos
            return Match(self, pos, pos, lasterror = e)
        raise MatchError(pos, self, None, [match])  # If the inner rule matches, raise an error

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

    def __eq__(self, other):
        return super().__eq__(other) and self.rules == other.rules


class RuleAll(RuleMultiple):
    """A rule that matches all tokens in the input."""
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
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
    def _consume(self, tokens: str, pos: int = 0, ignore: re.Pattern | None = None) -> Match:
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


class AST:
    def __init__(self, lineNumbers: List[int], matches: List[Match], tokens: str):
        """
        Represents an abstract syntax tree (AST) generated from parsed tokens.

        Wraps the list of Match objects produced by the PEG grammar parser, along with
        the original source tokens. This makes the AST self-contained, supporting
        traversal, transformation, and pretty-printing with context-sensitive slicing.
        """
        self.lineNumbers = lineNumbers
        self.matches = matches
        self.tokens = tokens

    def first(self) -> Match:
        """Return the first match in the AST (typically the root node)."""
        if not self.matches:
            raise RuntimeError("AST is empty, no matches found.")
        return self.matches[0]

    def walk(self):
        """Generator to walk through all matches in the AST."""
        for match in self.matches:
            yield from match.walk()

    def pretty_print(self, highlight: str = "\033[94m"):
        """Pretty print the match tree, showing the rule and matched text."""
        reset = "\033[0m"
        def render(match: Match, tokens, depth=0):
            if issubclass(match.rule.__class__, RulePrimitive):
                out = f"{' ' * depth}{highlight}{match.rule.identity}<{match.rule.__class__.__name__}>{reset}:{match.slice(tokens)!r}\n"
            else:
                out = f"{' ' * depth}{highlight}{match.rule.identity}<{match.rule.__class__.__name__}>{reset}\n"
            for child in match.children:
                out += render(child, tokens, depth + 2)
            return out
        for match in self.matches:
            print(render(match, self.tokens).rstrip())


class GrammarError(Exception):
    """
    Raised when a grammar fails to parse.  Contains the index the failure
    occurred at, the line and column number, and the MatchError that caused
    the failure.
    """
    pass

class GrammarParseError(GrammarError):
    """
    Raised when a grammar fails to parse.
    """
    def __init__(self, grammar: "Grammar", matches: List[Match], error: MatchError, tokens: str ):
        self.grammar = grammar
        self.matches = matches
        self.error = error
        self.tokens = tokens

    def __str__(self):
        def last_match(match: Match) -> Match:
            """Return the furthest match in the match tree."""
            furthest = match
            for node in match.walk():
                if node.end > furthest.end:
                    furthest = node
            return furthest

        def deepest_error(error: MatchError) -> MatchError:
            """Return the error with the highest position in the error tree."""
            furthest = error
            for node in error.walk():
                if node.pos > furthest.pos:
                    furthest = node
            return furthest

        def find_best_error(match: List[Match], error: MatchError) -> Tuple[Match | None, MatchError]:
            if match:
                furthest = last_match(match[-1]) # look at last match
                err = error
                if furthest.error:
                    err = deepest_error(error)
                else:
                    last = furthest.end
                    for node in error.walk():
                        if node.pos >= last:
                            if not err or node.pos > err.pos:
                                err = node
                return furthest, err
            return None, deepest_error(error)

        def matched_string(error: MatchError):
            matched = []
            while error.parent:
                identity = error.expected.identity
                if identity and identity not in self.grammar.hoist:
                    matched.append(error.expected.identity)
                error = error.parent
            return " → ".join(reversed(matched)) if matched else ""

        def get_identity(rule: Rule):
            if rule.identity and rule.identity in self.grammar.macros:
                return self.grammar.macros[rule.identity]
            if isinstance(rule, RuleMultiple):
                rules = rule.rules
                match len(rules):
                    case 1:
                        return f"{get_identity(rules[0])}"
                    case 2:
                        return f"{rules[0]} or {rules[1]}"
                    case _:
                        expect = ", ".join(get_identity(r) for r in rules[:-1])
                        return expect + f" or {get_identity(rules[-1])}"
            if isinstance(rule, RulePrimitive):
                expect = rule.pattern
            else:
                expect = rule.__class__.__name__
            return expect
        lastMatch, lastError = find_best_error(self.matches, self.error)
        unexpected = False
        matched = matched_string(lastError) if lastError else None
        expect = None
        header = None
        row, column = getLineInfo(self.tokens, lastError.pos)
        line = self.tokens.split('\n')[row - 1]

        expected = lastError.expected if lastError else None

        if expected:
            if isinstance(expected, RuleNotPredicate):
                unexpected = True # got something we shouldn't have
            expect = get_identity(lastError.parent.expected)
            identity = lastError.expected.identity or lastError.expected.__class__.__name__
            header = f"Error at line {row}, column {column} in {identity!r}:"
        else:
            header = f"Error at line {row}, column {column}:"

        # unexpected?, identity, line, matched, expect
        output = [ header,  line, ("-" * (column - 2) + "^") ]
        if matched:
            output.append(f"Matched: {matched}")
        if expect:
            if unexpected:
                output.append(f"Matched {expect}, which is not valid here.")
            else:
                output.append(f"Expected: {expect}")
        return "\n".join(output)


class GrammarDeferResolve(GrammarError):
    """
    Raised when a grammar rule cannot be resolved immediately.
    This is used to defer resolution of rules until all rules are defined.
    """
    def __init__(self, identifier: str):
        super().__init__(f"Rule '{identifier}' could not be resolved.")
        self.identifier = identifier

class GrammarMissingResolve(GrammarError):
    """
    Raised when a grammar rule is missing during resolution.
    This indicates that the rule was not found in the grammar's defined rules.
    """
    def __init__(self, identifier: str):
        super().__init__(f"Rule '{identifier}' is missing from the grammar.")
        self.identifier = identifier

class Flags:
    NONE = 0x00
    IGNORE_SPACE_AND_TAB = 0x01
    IGNORE_NEWLINE = 0x02
    IGNORE_WHITESPACE = IGNORE_SPACE_AND_TAB | IGNORE_NEWLINE
    FLATTEN = 0x04

IGNORABLE = [
    None,
    re.compile(r'[ \t]+'),      # Matches whitespace only
    re.compile(r'\n|\r\n|\r'),  # Matches newlines in various formats
    re.compile(r'\s+')          # Matches all whitespace including newlines
]
TOKEN_RE = re.compile(
    r'(\"(?:[^\"\\]|\\.)*\")'   # Double-quoted string
    r'|(\'(?:[^\'\\]|\\.)*\')'  # Single-quoted string
    r'|([^\s]+)'                # Plain token
)

def getLineInfo(tokens: str, pos: int) -> Tuple[int, int]:
    """Returns the row and column indicated by pos in tokens."""
    row = tokens.count('\n', 0, pos) + 1
    column = pos if row == 1 else pos - tokens.rfind('\n', 0, pos) + 1
    return row, column

class Grammar:
    """A grammar definition for the Firestarter parser."""
    def __init__(self, flags: int = Flags.NONE):
        self.rule: Rule | None = None
        self.rules: Dict[str, Rule] = {}
        self.dirty = False
        self.flags = flags  # bitmask for ignored lexemes (e.g. whitespace, newlines)
        self.discard = set()  # rules to discard from the grammar
        self.hoist = set() # rules that should be hoisted out
        self.merge = set() # rules that should be merged
        self.conditional = set() # rules that should be conditionally hoisted
        self.macros: Dict[str, str] = {} # used for parsing failures to provide better error messages

    def register(self, **kwargs: Rule | str):
        """Register a rule with the grammar."""
        for identifier, rule in kwargs.items():
            if isinstance(rule, str):
                self.rules[identifier] = RuleReference(rule)
            else:
                self.rules[identifier] = rule
                rule.identity = identifier
            if not self.rule:
                if isinstance(rule, str):
                    raise GrammarError(f"First rule '{identifier}' cannot be a reference.")
                self.rule = rule # first registered rule becomes the root
        self.dirty = True
        return self

    def resolve(self):
        """Resolve all rule references in the grammar."""
        def handle_rule(rule, callback):
            nonlocal stack, misses
            if isinstance(rule, RuleReference):
                if isinstance(self.rules[rule.identity], RuleReference):
                    misses += 1
                    raise GrammarDeferResolve(rule.identity)
                if rule.identity not in self.rules:
                    raise GrammarMissingResolve(rule.identity)
                callback(self.rules[rule.identity])
            else:
                stack.append(rule)

        toVisit = [(identifier, base) for identifier, base in self.rules.items()]
        misses = 0
        while toVisit:
            if misses == len(self.rules):
                raise GrammarError(f"Circular dependency detected in grammar rules. Triggered by: {toVisit[-1][0]}")
            identifier, base = toVisit.pop(0)
            stack, visited = [base], []
            try:
                while stack:
                    this = stack.pop()
                    if this in visited:
                            continue
                    visited.append(this)
                    if isinstance(this, RuleReference):
                        self.rules[identifier] = self.rules[this.identity]
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

    def parse(self, tokens: str) -> AST:
        def do_flatten(node: Match) -> List[Match]:
            """Flatten AST by discarding scaffolding."""
            if node.rule.identity in self.merge:
                node.children[0].rule = node.children[0].rule.duplicate()
                node.children[0].rule.identity = node.rule.identity
                return node.children[0]

            children = []

            for child in node.children:
                child = do_flatten(child)
                if child:
                    if isinstance(child, list):
                        children.extend(child)
                    else:
                        children.append(child)

            if node.rule.identity is None or node.rule.identity in self.hoist:
                return children

            if node.rule.identity in self.discard:
                return []

            if node.rule.identity in self.conditional and len(children) == 1:
                return children[0]

            node.children = children

            return node

        """Parse the input tokens using the defined grammar rules."""
        if not self.rule:
            raise RuntimeError(f"No rule defined for {self.__class__.__name__}.")
        if self.dirty:
            self.resolve()
        pos = 0
        matches: List[Match] = []
        ignore = IGNORABLE[self.flags & 0x03]
        try:
            while pos < len(tokens):
                match = self.rule.consume(tokens, pos, ignore)
                if len(match) == 0:
                    raise match.error
                matches.append(match)
                pos = match.end
        except MatchError as e:
            raise GrammarParseError(self, matches, e, tokens)
        if self.flags & Flags.FLATTEN:
            flattened = []
            for match in matches:
                flat = do_flatten(match)
                if isinstance(flat, list):
                    flattened.extend(flat)
                else:
                    flattened.append(flat)
            matches = flattened
            lineNumbers = []
            for line in matches:
                line, _ = getLineInfo(tokens, line.start)
                lineNumbers.append(line)
        return AST(lineNumbers, matches, tokens)

    def __repr__(self):
        rules_repr = "\n".join(f"{k}: {v}" for k, v in self.rules.items())
        return f"Grammar(\n{rules_repr}\n)"

PEG = Grammar(Flags.IGNORE_SPACE_AND_TAB | Flags.FLATTEN).register(
        Grammar=RuleOneOrMore(RuleChoice("Rule", "Newline","Comment")),
        Rule=RuleAll(RuleChoice("Strict","Identifier"), "Priority", "Expression", RuleOptional("Comment")),
        Priority=RuleChoice(RuleString("<-"), RuleString("--"), RuleString("->"), RuleString("<>"), RuleString("~>")),
        Comment=RuleAll(RuleString("#"), RulePattern(re.compile(r'[^\n]*'))),
        Expression="Choice",
        Choice=RuleAll("Sequence", RuleZeroOrMore(RuleAll(RuleString("/"), "Sequence"))),
        Sequence=RuleZeroOrMore(RuleChoice("Prefix","Suffix")),
        Prefix=RuleAll("Primary", RuleOptional("Quantifier")),
        Suffix=RuleAll("Predicate", "Primary"),
        Primary=RuleChoice("String", "RegEx", "Identifier", "Group"),
        Group=RuleAll(RuleString("("), "Expression", RuleString(")")),
        Predicate=RuleChoice(RuleString("&"), RuleString("!")),
        Quantifier=RuleChoice(RuleString("*"), RuleString("+"), RuleString("?")),
        String=RulePattern(re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')),
        RegEx=RulePattern(re.compile(r"~(['\"])(?:\\.|(?!\1).)*\1")),
        Strict=RuleAll(RuleString("["), "Identifier", RuleString("]")),
        Identifier=RulePattern(re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*')),
        Newline=RulePattern(re.compile(r'\n|\r\n|\r'))
    ).resolve()
PEG.discard.add("Newline")

def make_grammar_from_file(file_path: str, flags: int = Flags.NONE) -> Grammar:
    """
    Load a grammar from a file.

    This function reads the grammar definition from the specified file and returns a Grammar object.
    It raises GrammarError if the grammar is invalid or cannot be resolved.
    """
    with open(file_path, 'r') as f:
        text = f.read()
    return make_grammar(text, flags)

def make_grammar(text: str, flags: int = Flags.NONE) -> Grammar:
    """
    Load a grammar from a string definition.

    This function parses the grammar text and returns a Grammar object.
    It raises GrammarError if the grammar is invalid or cannot be resolved.
    """
    # Grammar,Rule,Identifier,Prefix,Choice,Newline,Sequence,String,Expression,Quantifier,RegEx
    def visit(node: Match, tokens: str) -> Any:
        """Visit a node in the AST and return its value."""
        if node.rule.identity == "Grammar":
            return visit_grammar(node, tokens)
        elif node.rule.identity == "Rule":
            return visit_rule(node, tokens)
        elif node.rule.identity == "Priority":
            return node.slice(tokens)
        elif node.rule.identity == "Strict":
            return visit_identifier(node.children[0], tokens)
        elif node.rule.identity == "Comment":
            return visit_comment(node, tokens)
        elif node.rule.identity == "Choice":
            return visit_choice(node, tokens)
        elif node.rule.identity == "Sequence":
            return visit_sequence(node, tokens)
        elif node.rule.identity == "Prefix":
            return visit_prefix(node, tokens)
        elif node.rule.identity == "Suffix":
            return visit_suffix(node, tokens)
        elif node.rule.identity == "Quantifier":
            return visit_quantifier(node, tokens)
        elif node.rule.identity == "Primary":
            return visit_primary(node, tokens)
        elif node.rule.identity == "Group":
            return visit_group(node, tokens)
        elif node.rule.identity == "Predicate":
            return visit_predicate(node, tokens)
        elif node.rule.identity == "Identifier":
            return visit_identifier(node, tokens)
        elif node.rule.identity == "String":
            return visit_string(node, tokens)
        elif node.rule.identity == "RegEx":
            return visit_regex(node, tokens)
        else:
            raise GrammarError(f"Unknown rule identifier {node.rule.identity!r}")

    def visit_grammar(node: Match, tokens: str) -> Dict[str, Rule | str]:
        grammar = {}
        for child in node.children:
            if child.rule.identity == "Comment":
                continue # skip line comments
            identifier, rule = visit(child, tokens)
            grammar[identifier] = rule
        return grammar

    def visit_comment(node: Match, tokens: str):
        return RuleString(node.slice(tokens)[2:].strip()) # remove # and whitespace

    def visit_rule(node: Match, tokens: str) -> Tuple[str, Rule | str]:
        nonlocal macros, discard, hoist, merge, cond
        strict = False
        if node.children[0].rule.identity == "Strict":
            strict = True
        identifier = visit(node.children[0], tokens)
        match visit(node.children[1], tokens):
            case "--":
                discard.add(identifier)
            case "->":
                hoist.add(identifier)
            case "<>":
                merge.add(identifier)
            case "~>":
                cond.add(identifier)
        rule = visit(node.children[2], tokens)
        if isinstance(rule, Rule):
            rule.strict = strict
        if len(node.children) > 3:
            macros[identifier] = visit_comment(node.children[3], tokens).pattern
        return (identifier, rule)

    def visit_choice(node: Match, tokens: str) -> Rule:
        rules = [visit(child, tokens) for child in node.children]
        if len(rules) == 1:
            return rules[0]
        return RuleChoice(*rules)

    def visit_sequence(node: Match, tokens: str) -> Rule:
        rules = [visit(child, tokens) for child in node.children]
        if len(rules) == 1:
            return rules[0]
        return RuleAll(*rules)

    def visit_prefix(node: Match, tokens: str) -> Rule:
        identifier = visit(node.children[0], tokens)
        if len(node.children) == 2:
            quantifier = visit(node.children[1], tokens)
            return quantifier(identifier)
        return identifier

    def visit_suffix(node: Match, tokens: str) -> Rule:
        predicate = visit(node.children[0], tokens)
        identifier = visit(node.children[1], tokens)
        return predicate(identifier)

    def visit_quantifier(node: Match, tokens: str) -> Type[Rule]:
        match node.slice(tokens):
            case "+":
                return RuleOneOrMore
            case "*":
                return RuleZeroOrMore
            case "?":
                return RuleOptional

    def visit_primary(node: Match, tokens: str) -> Any:
        return visit(node.children[0], tokens)

    def visit_group(node: Match, tokens: str) -> Any:
        return visit(node.children[0], tokens)

    def visit_predicate(node: Match, tokens: str) -> Type[Rule]:
        match node.slice(tokens):
            case "&":
                return RuleAndPredicate
            case "!":
                return RuleNotPredicate

    def visit_identifier(node: Match, tokens: str) -> str:
        return node.slice(tokens)

    def visit_string(node: Match, tokens: str) -> Rule:
        return RuleString(node.slice(tokens)[1:-1].encode().decode("unicode_escape"))  # remove quotes

    def visit_regex(node: Match, tokens: str) -> Rule:
        pattern = node.slice(tokens)[2:-1] # remove ~
        return RulePattern(re.compile(pattern))

    discard = set()
    hoist = set()
    merge = set()
    cond = set()
    macros = {}
    try:
        if not text.strip():
            raise GrammarError("Empty grammar definition provided.")
        try:
            rules = PEG.parse(text).first()
            keys = visit(rules, text)
            grammar = Grammar(flags).register(**keys).resolve()
            grammar.macros = macros
            grammar.discard = discard
            grammar.hoist = hoist
            grammar.merge = merge
            grammar.conditional = cond
        except KeyError as e:
            raise GrammarError(f"Missing rule in grammar definition: {e}")
        return grammar
    except GrammarError as e:
        raise GrammarError(f"Failed to parse grammar: {e}") from e

class CompareError(Exception):
    """Raised when two grammars cannot be compared."""
    def __init__(self, node1: Rule, node2: Rule):
        super().__init__(f"Rules {node1} and {node2} do not match.")
        self.node1 = node1
        self.node2 = node2

def compare_grammars(g1: Grammar, g2: Grammar, verbose: bool = False) -> bool:
    """Compare two grammars for equality."""
    def drill(a: Rule, b: Rule) -> bool:
        nonlocal verbose
        if verbose:
            print(f"Drilling into {a} and {b}")
        # returns whether or not two rules are equal
        if type(a) != type(b):
            if verbose:
                print(f"Rule {a} is of type {type(a)}, but {b} is of type {type(b)}.")
            raise CompareError(a, b)
        if isinstance(a, RulePrimitive):
            return a == b
        if isinstance(a, RuleSingle):
            return drill(a.rule, b.rule)
        if isinstance(a, RuleMultiple):
            if len(a.rules) != len(b.rules):
                if verbose:
                    print(f"Rule {a} has {len(a.rules)} children, but {b} has {len(b.rules)} children.")
                raise CompareError(a, b)
            for i, child in enumerate(a.rules):
                return drill(child, b.rules[i]) 
            return True
        if isinstance(a, RuleReference):
            return a.identity == b.identity
        return False # no idea what the hell this is, so return False
    try:
        for identifier, rule in g1.rules.items():
            if identifier not in g2.rules:
                if verbose:
                    print(f"Rule {identifier} not found in second grammar.")
                raise CompareError(rule, None)
            if verbose:
                print(f"Comparing {identifier} in {g1} with {g2}")
            if not drill(rule, g2.rules[identifier]):
                raise CompareError(rule, g2.rules[identifier])
    except CompareError as e:
        print(f"Grammar comparison failed: {e}")
        return False
    return True
