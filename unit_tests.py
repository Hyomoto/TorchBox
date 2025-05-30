from testing import UnitTest, TestException
from firestarter.grammar import *
from constants import Ansi

VERBOSE = True

def start(text: str, icon: str = None):
    UnitTest.start(text, icon=icon)
def finished(text: str, errors: int, tests: int = None):
    UnitTest.finished(text, errors, tests)
def passed(text: str, verbose: bool = True, depth: int = 1):
    UnitTest.passed(text, verbose, depth)
def failed(text: str, verbose: bool = True, depth: int = 1):
    UnitTest.failed(text, verbose, depth)
def info(text: str, verbose: bool = True, depth: int = 0):
    UnitTest.info(text, verbose, icon="ℹ️  ", depth=depth)

def test_all_rules(verbose: bool = True):
    def test_consume_success(description: str, rule: Rule, tokens: str, expected: int, startAt: int = 0):
        def matches(x: Match) -> bool:
            return len(x)
        nonlocal errors, verbose,depth,tests
        tests += 1
        errors += UnitTest.test_legal_op_with_assertion(description, (rule.consume, tokens, startAt), expected, matches, verbose=verbose, depth=depth)
    def test_consume_failure(description: str, rule: Rule, tokens: str, error: Type[Exception] = MatchError):
        nonlocal errors, verbose,depth,tests
        tests += 1
        errors += UnitTest.test_illegal_op(description, (rule.consume, tokens, 0), error, verbose=verbose, depth=depth)
    errors, tests, depth = 0, 0, 2
    start("Testing all rules", icon="📖")
    info("Testing consume method of single rules", verbose=verbose, depth=1)
    rule = RuleReference("test")
    test_consume_failure("RuleReference consume failure", rule, "test", error=NotImplementedError)
    rule = RuleString("test")
    test_consume_success("RuleString consume success", rule, "test", 4)
    test_consume_failure("RuleString consume failure", rule, "tes")
    test_consume_success("RuleString consume success mid-string", rule, "   test   ", 4, startAt=3)
    rule = RulePattern(re.compile(r"\d+"))
    test_consume_success("RulePattern consume success", rule, "123", 3)
    test_consume_failure("RulePattern consume failure", rule, "a12")
    test_consume_success("RulePattern consume success mid-string", rule, "   123   ", 3, startAt=3)
    rule = RuleOneOrMore(RuleString("test"))
    test_consume_success("RuleOneOrMore consume success", rule, "test test", 4)
    test_consume_success("RuleOneOrMore multi consume success", rule, "testtesttest", 12)
    test_consume_failure("RuleOneOrMore consume failure", rule, "abctestabc")
    rule = RuleZeroOrMore(RuleString("test"))
    test_consume_success("RuleZeroOrMore consume success", rule, "test test", 4)
    test_consume_success("RuleZeroOrMore multi consume success", rule, "testtesttest", 12)
    test_consume_success("RuleZeroOrMore consume success with no match", rule, "quatestke", 0)
    rule = RuleOptional(RuleString("test"))
    test_consume_success("RuleOptional consume success", rule, "test", 4)
    test_consume_success("RuleOptional consume success with no match", rule, "quatestke", 0)
    rule = RuleAndPredicate(RuleString("test"))
    test_consume_success("RuleAndPredicate consume success", rule, "test", 0)
    test_consume_failure("RuleAndPredicate consume failure", rule, "tes")
    rule = RuleNotPredicate(RuleString("test"))
    test_consume_success("RuleNotPredicate consume success", rule, "quatestke", 0)
    test_consume_failure("RuleNotPredicate consume failure", rule, "test")
    info("Testing consume method of rule groups", verbose=verbose, depth=1)
    rule = RuleAll(RuleString("test"), RulePattern(re.compile(r'\s+')), RuleString("test2"))
    test_consume_success("RuleAll consume success", rule, "test test2", 10)
    test_consume_failure("RuleAll consume failure", rule, "test test3")
    rule = RuleChoice(RuleString("foo"), RuleString("bar"))
    test_consume_success("RuleChoice consume success", rule, "foo", 3)
    test_consume_success("RuleChoice consume success", rule, "bar", 3)
    test_consume_failure("RuleChoice consume failure", rule, "test3")
    finished("Testing all rules", errors, tests)

def test_all(verbose: bool = True):
    test_all_rules(verbose=True)

if __name__ == "__main__":
    test_all(VERBOSE)