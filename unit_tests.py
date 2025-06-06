from testing import UnitTest, TestException
from firestarter.grammar import *
from firestarter import FirestarterError
from constants import Ansi
from tinder.crucible import Crucible
from tinder import Kindling, Value, Yield, JumpTo, String, Number, Boolean, Lookup, Redirect, Group, Set, Write, Input
from tinder import From, In, And, Or, Not, Less, Greater, Max, Min, Add, Subtract, Call, NoOp, Goto
from tinder import Stop, Jump, Tinder, Tinderstarter, TinderBurn

VERBOSE = True

def start(text: str, icon: str = None):
    UnitTest.start(text, icon=icon)
def finished(text: str, errors: int, tests: int = None):
    UnitTest.finished(f"{text} ({tests} tests)", errors)
def passed(text: str, verbose: bool = True, depth: int = 1):
    UnitTest.passed(text, verbose, depth)
def failed(text: str, verbose: bool = True, depth: int = 1):
    UnitTest.failed(text, verbose, depth)
def info(text: str, verbose: bool = True, depth: int = 0):
    UnitTest.info(text, verbose, icon="ℹ️  ", depth=depth)

def test_all_kindling(verbose: bool = True):
    def test_kindling(description: str, symbol: Kindling, expected: Any, assertion: Callable | Tuple[Callable, ...]):
        nonlocal errors, verbose, depth, tests, crucible
        tests += 1
        errors += UnitTest.test_legal_op_with_assertion( description, (symbol.transmute, crucible), expected, assertion, verbose=verbose, depth=depth)
    def test_value(description: str, symbol: Value, expected: Any):
        test_kindling(description, symbol, True, lambda x: x == expected)
    def test_yield(description: str, kindling: Kindling, expected: Any, assertion: Tuple[Callable, ...] = None):
        nonlocal errors, verbose, depth, tests, crucible
        test_illegal(description, (kindling.transmute, crucible), expected)
        if assertion:
            try:
                kindling.transmute(crucible)
            except expected as e:
                if assertion[0](e) != assertion[1]:
                    errors += 1
                    failed(f"{description} - assertion failed, got {e}, expected {assertion[1]}", verbose=verbose, depth=depth)
                
    def test_illegal(description: str, action: Tuple[Any,...], exception = TinderBurn):
        nonlocal errors, verbose, depth, tests, crucible
        tests += 1
        errors += UnitTest.test_illegal_op(description, action, exception, verbose=verbose, depth=depth)
    def test(description: str, result: Any, expected: Any):
        nonlocal errors, verbose, depth, tests
        tests += 1
        errors += UnitTest.test(description, result, expected, verbose=verbose, depth=depth)
    crucible = Crucible().update({ "foo": "bar", "baz": "foo" })
    errors, tests, depth = 0, 0, 2
    start("Testing all kindling", icon="📖")
    info("Testing values", verbose=verbose, depth=1)
    test_value("String", String("test"), "test")
    test_value("Number", Number(123), 123)
    test_value("Boolean", Boolean(True), True)
    info("Testing identifiers", verbose=verbose, depth=1)
    test_value("Lookup", Lookup("foo"), "bar")
    test_value("Redirect", Redirect("baz"), "bar")
    test_value("Group (Multiple)", Group(Lookup("foo"), Number(10)), ["bar", 10])
    test_value("Group (Single)", Group(Lookup("foo")), ["bar"])
    info("Testing setters", verbose=verbose, depth=1)
    test_kindling("Set", Set(Lookup("foo"), String("new_value")), True, lambda x: crucible["foo"] == "new_value")
    test_kindling("Write", Write(Lookup("output"), String("first line"), Boolean(True)), True, lambda x: crucible["output"] == "first line\n")
    test_kindling("Write append", Write(Lookup("output"), String("second line"), Boolean(False)), True, lambda x: crucible["output"] == "first line\nsecond line")
    test_yield("Input yield", Input(Lookup("input"), String(">>")), Yield)
    test("Input write", crucible["input"], ">>")
    info("Testing getters", verbose=verbose, depth=1)
    crucible.set("foo", 1)
    test_kindling("From", From(Lookup("foo"), Group(Lookup("baz"), String("test"))), True, lambda x: x == "test")
    info("Testing comparisons", verbose=verbose, depth=1)
    test_kindling("In", In(String("test"), Group(Lookup("baz"), String("test"))), True, lambda x: x == "test")
    test_kindling("And", And(Number(5), Number(3), Number(2)), True, lambda x: x)
    test_kindling("And False", And(Number(5), Number(3), Number(0)), False, lambda x: x)
    test_illegal("And illegal", (And, Number(5)), TinderBurn)
    test_kindling("Or", Or(Number(0), Number(0), Number(2)), True, lambda x: x)
    test_kindling("Or False", Or(Number(0), Number(0), Number(0)), False, lambda x: x)
    test_illegal("Or illegal", (Or, Number(5)), TinderBurn)
    test_kindling("Not (Number)", Not(Number(0)), True, lambda x: x)
    test_kindling("Not (Other)", Not(Lookup("baz")), False, lambda x: x)
    test_kindling("Less (True)", Less(Number(1), Number(2)), True, lambda x: x)
    test_kindling("Less (False)", Less(Number(2), Number(1)), False, lambda x: x)
    test_kindling("Greater (True)", Greater(Number(2), Lookup("foo")), True, lambda x: x)
    test_kindling("Greater (False)", Greater(Lookup("foo"), Number(2)), False, lambda x: x)
    test_kindling("Max", Max(Number(1), Number(2), Number(3)), 3, lambda x: x)
    test_kindling("Min", Min(Number(1), Number(2), Number(3)), 1, lambda x: x)
    test_kindling("Add", Add(Group(Number(1), Number(2), Number(3))), 6, lambda x: x)
    test_kindling("Add with max", Add(Group(Number(1), Number(2), Number(3)), Number(3)), 3, lambda x: x)
    test_illegal("Add illegal", (Add, Group(Number(1))), TinderBurn)
    test_kindling("Subtract", Subtract(Group(Number(5), Number(2))), 3, lambda x: x)
    test_kindling("Subtract with min", Subtract(Group(Number(2), Number(5)), Number(0)), 0, lambda x: x)
    test_illegal("Subtract illegal", (Subtract, Group(Number(5))), TinderBurn)
    info("Testing control flow", verbose=verbose, depth=1)
    def test_call(input: Any):
        return input
    crucible.set("test_call", test_call)
    test_kindling("Call", Call(Lookup("test_call"), Number(1)), 1, lambda x: x)
    test_illegal("Call illegal", (Call(Lookup("foo")).transmute, crucible), TinderBurn)
    def test_no_op():
        return True
    crucible.set("test_no_op", test_no_op)
    crucible.set("foo", "test_no_op")
    test_kindling("Call NoArgs (w/redirect)", Call(Redirect("foo")), True, lambda x: x)
    test_kindling("NoOp", NoOp(), None, lambda x: x)
    test_kindling("Goto", Goto(Lookup("foo")), None, lambda x: x)
    test_yield("Stop", Stop(), Yield)
    crucible.set("foo", 99)
    test_yield("Jump", Jump(Lookup("foo")), JumpTo, (lambda x: x.line, 99))
    test_illegal("Jump non-number", (Jump(Lookup("baz")).transmute, crucible), TinderBurn)
    finished("Testing all kindling", errors, tests)

def test_tinderstarter(verbose: bool = True):
    def compile(description: str, input:str) -> Tinder:
        nonlocal errors, verbose, depth, tests
        tests += 1
        try:
            script = tinderstarter.compile(input)
            passed(f"Compiled '{description}' successfully", verbose=verbose, depth=depth)
        except FirestarterError as e:
            errors += 1
            failed(f"Failed to compile script:\n{e}", verbose=verbose, depth=depth)
            finished("Testing Tinderstarter", errors, tests)
            raise TestException("Compilation failed")
        return script
    def test_run(description: str, script: Tinder, line: int = 0, exception: Type = None):
        nonlocal errors, verbose, tests, crucible, depth
        tests += 1
        try:
            line = script.run(line, crucible)
        except Exception as e:
            if type(e) is not exception:
                errors += 1
                failed(f"{description} - raised exception {e}", verbose=verbose, depth=depth)
                return None
        passed(f"{description} - ran successfully", verbose=verbose, depth=depth)
        return line
    def test_result(description: str, result: Any, expected: Any, assertion: Callable = None, depth: int = 0):
        nonlocal errors, verbose, tests
        tests += 1
        if assertion:
            result = assertion(result)
        if result == expected:
            passed(description, verbose=verbose, depth=depth)
        else:
            errors += 1
            failed(f"{description} - expected {expected}, got {result}", verbose=verbose, depth=depth)
    errors, tests, depth = 0, 0, 2
    crucible = Crucible()
    start("Testing Tinderstarter", icon="🔥")
    try:
        info("Testing compilation of a simple script", verbose=verbose, depth = 1)
        tinderstarter = Tinderstarter()
        script = compile("set foo to bar", 'v1\n  set foo "bar"')
        line = test_run("Run script to set foo", script)
        test_result("foo is set to bar", crucible["foo"], "bar", depth = depth + 1)
        test_result("script returns correct line (1)", line, 1, depth = depth + 1)
        script = compile("test jumpto", 'v1\n  jump jump_to\n  stop\n# jump_to\n  stop')
        script.writeJumpTable(crucible)
        line = test_run("Run script with jump", script, 0, JumpTo)
        test_result("script returns to correct line (0)", line, 4, depth = depth + 1)
    except TestException:
        pass # If compilation fails, we don't continue testing
    finished("Testing Tinderstarter", errors, tests)

def test_all_tinder(verbose: bool = True):
    test_all_kindling(verbose=verbose)
    test_tinderstarter(verbose=verbose)

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
    test_tinderstarter(VERBOSE)