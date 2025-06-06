from typing import Any, Callable, Tuple

class TestException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class Ansi:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    YELLOW = "\033[1;33m"
    WHITE = "\033[1;37m"
    LIGHT_GRAY = "\033[0;37m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    DARK_GRAY = "\033[1;30m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    RESET = "\033[0m"

class UnitTest:
    PASS_EMOJI = "✅ "
    FAIL_EMOJI = "❌ "
    INFO_EMOJI = "ℹ️  "
    WARN_EMOJI = "⚠️ "
    def __init__(self):
        raise NotImplementedError("UnitTest is a static class and cannot be instantiated.")

    @classmethod
    def info(cls, text: str, verbose: bool = True, icon: str = None, depth: int = 0):
        if verbose:
            print(f"{'  ' * depth}{icon or ''}{Ansi.BOLD}{text}{Ansi.RESET}")

    @classmethod
    def start(cls, text: str, icon: str = None):
        cls.info(text, verbose=True, icon=icon, depth=0)

    @classmethod
    def finished(cls, text: str, errors: int):
        if errors:
            cls.info(f"{Ansi.RED}{text} finished with {errors} errors.", verbose=True, icon=cls.FAIL_EMOJI, depth=0)
        else:
            cls.info(f"{Ansi.GREEN}{text} finished successfully!", verbose=True, icon=cls.PASS_EMOJI, depth=0)

    @classmethod
    def passed(cls, text: str, verbose: bool = True, depth: int = 1):
        cls.info(f"{text}{Ansi.RESET} {Ansi.GREEN}- passed.", verbose, cls.PASS_EMOJI, depth)

    @classmethod
    def failed(cls, text: str, verbose: bool = True, depth: int = 1):
        cls.info(f"{text}{Ansi.RESET} {Ansi.RED}- failed.", verbose, cls.FAIL_EMOJI, depth)
    
    @classmethod
    def test(cls, description: str, result: Any, expected: Any, verbose: bool = True, depth: int = 0):
        try:
            assert result == expected, TestException(f"returned {result} but expected {expected}")
        except AssertionError as e:
            cls.failed(f"{description}{Ansi.RED} {e}", verbose, depth)
            return 1
        cls.passed(description, verbose, depth)
        return 0
    
    @classmethod
    def test_with_assertion(cls,
                            description: str,
                            result: Any,
                            expected: Any,
                            assertion: Callable | Tuple[Callable, ...],
                            verbose: bool = True,
                            depth: int = 0
                            ):
        if type(assertion) is Tuple:
            result = assertion[0](*assertion[1:])
        else:
            result = assertion(result)
        return cls.test(description, result, expected, verbose, depth)
    
    @classmethod
    def test_legal_op(cls,
                      description: str,
                      action: Tuple[Any, ...],
                      expected: Any,
                      verbose: bool = True,
                      depth: int = 0
                      ):
        try:
            result = action[0](*action[1:])
        except Exception as e:
            cls.failed(f"{description}{Ansi.RED} raised {e}", verbose, depth)
            return 1
        return cls.test(description, result, expected, verbose, depth)
        
    @classmethod
    def test_legal_op_with_assertion(cls,
                                     description: str, 
                                     action: Tuple[Any, ...], 
                                     expected: Any, 
                                     assertion: Callable | Tuple[Callable, ...],
                                     verbose: bool = True, 
                                     depth: int = 0
                                     ):
        try:
            result = action[0](*action[1:])
        except Exception as e:
            raise e
            cls.failed(f"{description}{Ansi.RED} raised {e}", verbose, depth)
            return 1
        return cls.test_with_assertion(description, result, expected, assertion, verbose, depth)
    
    @classmethod
    def test_illegal_op(cls,
                        description: str,
                        action: Tuple[Any, ...],
                        expected: Exception,
                        verbose: bool = True,
                        depth: int = 0
                        ):
        try:
            action[0](*action[1:])
        except expected as e:
            cls.passed(f"{description} (expected raise): {e.__class__.__name__}", verbose, depth)
            return 0
        except Exception as e:
            cls.failed(f"{description} raised {e} but expected {expected}", verbose, depth)
            return 1
        cls.failed(f"{description} should have raised an exception but did not.", verbose, depth)
        return 1
