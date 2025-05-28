from testing import UnitTest, TestException
from firestarter import *

def test_all_lexemes(verbose: bool = True):
    def test_lexeme_value(description: str, lexeme: Lexeme, expected: Any):
        nonlocal errors, verbose, depth
        errors += UnitTest.test_legal_op_with_assertion(description, (lexeme.value), expected, verbose=verbose, depth=depth)
    errors = 0
    depth = 0

def test_all_rules(verbose: bool = True):
    def test_consume_success(description: str, rule: Rule, tokens: List[Lexeme], expected: int):
        nonlocal errors, verbose,depth
        errors += UnitTest.test_legal_op(description, (rule.consume, tokens, 0), expected, verbose=verbose, depth=1)
    def test_consume_failure(description: str, rule: Rule, tokens: List[Lexeme]):
        nonlocal errors, verbose,depth
        errors += UnitTest.test_illegal_op(description, (rule.consume, tokens, 0), MatchError, verbose=verbose, depth=1)
    errors = 0
    depth = 0

