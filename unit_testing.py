from typing import Any
from tinder import Value, Kindling, Crucible, Lookup, String, Number, Group
from tinder import Set, Write, Input, In, And, Or, Not
from tinder import Less, Greater, Max, Min, Add, Subtract
from tinder import Call, Goto, Stop, Jump
from tinder import Yield, JumpTo
from constants import Ember, Crucible, Ansi

# -- Emojis and formatting
PASS_EMOJI = f"{Ansi.GREEN}✅{Ansi.RESET}"
FAIL_EMOJI = f"{Ansi.RED}❌{Ansi.RESET}"
INFO_EMOJI = f"{Ansi.BLUE}ℹ️ {Ansi.RESET}"
WARN_EMOJI = f"{Ansi.YELLOW}⚠️ {Ansi.RESET}"

class TestException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

def vprint(verbose: bool, text:str):
    """Prints text if verbose is True."""
    if verbose:
        print(text)

def test_all_values(verbose: bool = True):
    def test_value(text: str, value: Value, env: Crucible, expected: Any):
        nonlocal errors
        test = value.get(env)
        try:
            try:
                assert test == expected, TestException(f"returned {test} but expected {expected}")
            except Exception as e:
                raise TestException(f"raised {e} with '{expected}'.")
            vprint(verbose, f"\t{PASS_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.GREEN}- passed.{Ansi.RESET}")
        except Exception as e:
            print(f"\t{FAIL_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.RED}- failed: {e}{Ansi.RESET}")
            errors += 1

    errors = 0
    print(f"{INFO_EMOJI}{Ansi.BOLD} Testing all values...{Ansi.RESET}")
    # Setup environment
    env = Crucible()
    env.set('foo', 123)
    env.set('bar', 'baz')
    env.set('n', 99)
    env.set('s', "stringy")
    # Lookup
    test_value("Lookup foo", Lookup('foo'), env, 123)
    test_value("Lookup bar", Lookup('bar'), env, 'baz')
    # String
    test_value("String hello", String('hello'), env, 'hello')
    test_value("String world", String('world'), env, 'world')
    # Number
    test_value("Number 42", Number(42), env, 42.0)
    test_value("Number 3.14", Number(3.14), env, 3.14)
    # Group
    test_value("Group [1, x, bar]", Group([Number(1), String('x'), Lookup('bar')]), env, [1.0, 'x', 'baz'])
    print(f"{Ansi.BOLD}{Ansi.RED if errors else Ansi.GREEN}All value unit tests complete. {FAIL_EMOJI if errors else PASS_EMOJI}{Ansi.RESET}")

def test_all_kindling(verbose: bool = True):
    def test_kindling(text: str, kindling: Kindling, env: Crucible, expectedReturn: Any, expectedKey: tuple[str, Any] | None = None):
        nonlocal errors
        output = None
        try:
            try:
                output = kindling.get(env)
            except Exception as e:
                raise TestException(f"raised {e}.")
            assert output == expectedReturn, TestException(f"returned {output} but expected {expectedReturn}")
            if expectedKey is not None:
                assert env.get(expectedKey[0]) == expectedKey[1], TestException(f"should have written {expectedKey[0]} = {expectedKey[1]} but got {env.get(expectedKey[0])}.")
            vprint(verbose, f"\t{PASS_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.GREEN}- passed.{Ansi.RESET}")
        except Exception as e:
            print(f"\t{FAIL_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.RED}- failed: {e}{Ansi.RESET}")
            errors += 1

    def test_yield_kindling(text: str, kindling: Kindling, env: Crucible, expectedRaise: Yield, expectedLine: int, expectedKey: tuple[str, Any] | None = None):
        nonlocal errors
        exception = None
        try:
            try:
                kindling.get(env)
            except Exception as e:
                exception = e
            if not isinstance(exception, expectedRaise):
                raise TestException(f"raised {exception} but expected {expectedRaise}.")
            if expectedRaise == JumpTo and exception.line != expectedLine:
                raise TestException(f"raised {expectedRaise} but with '{exception.line}' when {expectedLine} was expected.")
            if expectedKey is not None:
                assert env.get(expectedKey[0]) == expectedKey[1], TestException(f"should have written {expectedKey[0]} = {expectedKey[1]} but got {env.get(expectedKey[0])}.")
            vprint(verbose, f"\t{PASS_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.GREEN}- passed.{Ansi.RESET}")
        except Exception as e:
            print(f"\t{FAIL_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.RED}- failed: {e}{Ansi.RESET}")
            errors += 1

    def test_call_add(a, b):
        return a + b
    
    def test_call_noop():
        return "called:noop()"
    
    errors = 0
    print(f"{INFO_EMOJI}{Ansi.BOLD} Testing all kindling...{Ansi.RESET}")
    # Setup environment
    env = Crucible()
    env.set('x', 0)
    env.set('y', 10)
    env.set('foo', 2)
    env.set('bar', 5)
    env.set('output', "")
    env.set('input', "")
    env.set('sum', test_call_add)
    env.set('noop', test_call_noop)

    # --- Set ---
    test_kindling("Set x = 77", Set(String('x'), Number(77)), env, None, expectedKey=('x', 77.0))

    # --- Write ---
    test_kindling("Write output = 'out!'", Write(String('output'), String('out!')), env, None, expectedKey=('output', 'out!\n'))

    # --- Input (should raise Yield) ---
    test_yield_kindling("Input input = 'gimme'", Input(String('input'), String('gimme')), env, Yield, None, expectedKey=('input', 'gimme'))

    # --- Comparison: In ---
    test_kindling("In 5 in (3, 4, 5)", In(Number(5), Number(3), Number(4), Number(5)), env, True)
    test_kindling("In 'a' in ('x', 'y')", In(String('a'), String('x'), String('y')), env, False)
    test_kindling("In bar in (1, 2, 5)", In(Lookup('bar'), Number(1), Number(2), Number(5)), env, True)

    # --- And ---
    test_kindling("And (1<2 and 3 in (2,3))", And(Less(Number(1), Number(2)), In(Number(3), Number(2), Number(3))), env, True)
    test_kindling("And (1<0 and 3 in (2,4))", And(Less(Number(1), Number(0)), In(Number(3), Number(2), Number(4))), env, False)

    # --- Or ---
    test_kindling("Or (1<2 or 3 in (5,4))", Or(Less(Number(1), Number(2)), In(Number(3), Number(5), Number(4))), env, True)
    test_kindling("Or (5<2 or 7 in (8,9))", Or(Less(Number(5), Number(2)), In(Number(7), Number(8), Number(9))), env, False)

    # --- Not ---
    test_kindling("Not 0", Not(Number(0)), env, True)
    test_kindling("Not 1", Not(Number(1)), env, False)
    test_kindling("Not (5<2)", Not(Less(Number(5), Number(2))), env, True)

    # --- Less / Greater ---
    test_kindling("Less 1<2", Less(Number(1), Number(2)), env, True)
    test_kindling("Less 3<2", Less(Number(3), Number(2)), env, False)
    test_kindling("Greater 3>2", Greater(Number(3), Number(2)), env, True)
    test_kindling("Greater 1>2", Greater(Number(1), Number(2)), env, False)

    # --- Max / Min ---
    test_kindling("Max(3,8,2)", Max(Number(3), Number(8), Number(2)), env, 8.0)
    test_kindling("Min(3,8,2)", Min(Number(3), Number(8), Number(2)), env, 2.0)

    # --- Add ---
    test_kindling("Add(1,2)", Add(Number(1), Number(2)), env, 3.0)
    test_kindling("Add(2.5,7.5)", Add(Number(2.5), Number(7.5)), env, 10.0)
    test_kindling("Add(2,4,5)", Add(Number(2), Number(4), Number(5)), env, 5.0)  # Capped at max

    # --- Subtract ---
    test_kindling("Subtract(5,2)", Subtract(Number(5), Number(2)), env, 3.0)
    test_kindling("Subtract(5,10)", Subtract(Number(5), Number(10)), env, -5.0)
    test_kindling("Subtract(5,10,-2)", Subtract(Number(5), Number(10), Number(-2)), env, -2.0)  # Floored at min

    # --- Call ---
    test_kindling("Call(sum,2,3)", Call(String("sum"), Number(2), Number(3)), env, 5.0)
    test_kindling("Call(noop)", Call(String("noop")), env, "called:noop()")

    # --- Goto (no op, returns None) ---
    test_kindling("Goto(scene1)", Goto(String("scene1")), env, None)
    assert Goto(Lookup("scene1")).var == "scene1", "Goto(scene1) -> Internal value conversion to string failed."

    # --- Stop (should raise Yield) ---
    test_yield_kindling("Stop", Stop(), env, Yield, None)

    # --- Jump ---
    env.set("target", 99)
    # Unconditional jump
    test_yield_kindling("Jump unconditional", Jump(Lookup("target"), None), env, JumpTo, 99)
    # Conditional jump, Value true
    test_yield_kindling("Jump value true", Jump(Lookup("target"), Number(1)), env, JumpTo, 99)
    # Conditional jump, Value false (no jump)
    test_kindling("Jump value false", Jump(Lookup("target"), Number(0)), env, None)
    # Conditional jump, Comparison true
    test_yield_kindling("Jump comparison true", Jump(Lookup("target"), Less(Number(1), Number(2))), env, JumpTo, 99)
    # Conditional jump, Comparison false (no jump)
    test_kindling("Jump comparison false", Jump(Lookup("target"), Greater(Number(3), Number(5))), env, None)
    # Unconditional jump to a specific line
    test_yield_kindling("Jump to line 42", Jump(Number(42)), env, JumpTo, 42)
    # Conversion of String to Lookup
    test_yield_kindling("Conversion of string to lookup", Jump(String("target")), env, JumpTo, 99)
    print(f"{Ansi.BOLD}{Ansi.RED if errors else Ansi.GREEN}All kindling unit tests complete. {FAIL_EMOJI if errors else PASS_EMOJI}{Ansi.RESET}")

def test_crucible(verbose: bool = True):
    def test_legal_write(text: str, env: Crucible, key: str, value: Any):
        nonlocal errors
        try:
            env.set(key, value)
            assert env.get(key) == value, TestException(f"returned {env.get(key)} but expected {value}")
            if verbose:
                print(f"\t{PASS_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.GREEN}- passed.{Ansi.RESET}")
        except Exception as e:
            print(f"\t{FAIL_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.RED}- failed: {e}{Ansi.RESET}")
            errors += 1

    def test_illegal_write(text: str, env: Crucible, key: str, value: Any):
        nonlocal errors
        try:
            env.set(key, value)
            print(f"\t{FAIL_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.RED}- failed: did not raise as expected.{Ansi.RESET}")
            errors += 1
        except Exception as e:
            if verbose:
                print(f"\t{PASS_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.GREEN}- raised successfully: {e}{Ansi.RESET}")

    def test_read(text: str, env: Crucible, key: str, expected: Any):
        nonlocal errors
        try:
            test = env.get(key)
            assert test == expected, TestException(f"returned {test} but expected {expected}")
            if verbose:
                print(f"\t{PASS_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.GREEN}- passed.{Ansi.RESET}")
        except Exception as e:
            print(f"\t{FAIL_EMOJI} {Ansi.BOLD}{text}{Ansi.RESET} {Ansi.RED}- failed: {e}{Ansi.RESET}")
            errors += 1
    errors = 0
    print(f"{INFO_EMOJI}{Ansi.BOLD} Testing Crucible...{Ansi.RESET}")
    # Setup three layers: protected (top), global (middle), local (bottom)
    protected_vars = {"const": 7, "unchange": "fixed"}
    global_vars = {"score": 100, "shared": 9, "nest": {"sub": 1}}
    local_vars = {"temp": 1, "foo": 42}

    # Create the hierarchy: protected > global > local
    protected = Crucible(protected_vars, None, protected=True)
    global_scope = Crucible(global_vars, protected)
    local = Crucible(local_vars, global_scope)

    vprint(verbose, "Testing Crucible reads (should succeed):")
    test_read("read protected const", local, "const", 7)
    test_read("read global score", local, "score", 100)
    test_read("read local temp", local, "temp", 1)
    test_read("read local foo", local, "foo", 42)
    test_read("read global shared", local, "shared", 9)
    test_read("read protected from global", global_scope, "const", 7)

    vprint(verbose, "Testing Crucible legal writes:")
    test_legal_write("write new local var", local, "newvar", 555)
    test_read("verify new local var", local, "newvar", 555)
    test_legal_write("overwrite global (type ok)", local, "score", 123)
    test_read("verify overwritten global", global_scope, "score", 123)
    test_legal_write("overwrite local", local, "temp", 99)
    test_read("verify overwritten local", local, "temp", 99)
    test_legal_write("write new nested key to local", local, "nested.sub", 42)
    test_read("verify nested key", local, "nested.sub", 42)
    test_legal_write("write nested key to global", local, "nest.sub", 2)
    test_read("verify nested key in global", local, "nest.sub", 2)

    vprint(verbose, "Testing Crucible illegal writes:")
    test_illegal_write("mutate global type", local, "nest", "not a number")
    test_illegal_write("write nested to partial global path", local, "nest.foo.bar", 1)
    test_illegal_write("mutate nested global", local, "nest.sub", "not a number")
    test_illegal_write("write to protected", local, "const", 8)

    vprint(verbose, "Testing Crucible call:")
    def myfunc(a, b):
        return a + b
    test_legal_write("write function to local", local, "adder", myfunc)
    try:
        result = local.call("adder", 3, 4)
        assert result == 7, TestException(f"call returned {result} but expected 7")
        if verbose:
            print(f"\tcall('adder') -> call adder (3, 4) passed.")
    except Exception as e:
        print(f"\tcall('adder') -> call adder (3, 4) failed: {e}")
    test_legal_write("write not-callable to local", local, "not_callable", 42)
    try:
        local.call("not_callable", 1)
        print(f"\tnot_callable -> call not_callable failed: did not raise as expected.")
    except Exception as e:
        if verbose:
            print(f"\tnot_callable -> call not_callable passed: {e}")

    print(f"{Ansi.BOLD}{Ansi.RED if errors else Ansi.GREEN}Crucible unit tests complete. {FAIL_EMOJI if errors else PASS_EMOJI}{Ansi.RESET}")

def test_all(verbose = True):
    test_all_values(verbose)
    test_all_kindling(verbose)
    test_crucible(verbose)

if __name__ == "__main__":
    test_all(False)
    