from typing import Optional
from canvas import Ansi, ColorSpan, ColorCode

def testMethod(method, cases):
    failures = 0
    for test, args, expected in cases:
        print(f"Testing {method.__name__} : {test} {args}")
        output = method(*args)
        for i, assertion in enumerate(expected):
            try:
                assert output[i] == assertion
            except AssertionError:
                print("Expected:", repr(expected))
                print("     Got:", repr(output))
                failures += 1
                break
    print(f"Total failures: {failures}" if failures else "All tests passed.")

def test_getColorSpans(method):
    testMethod(method, [
        ((f"Hello, {Ansi.BLUE}World{Ansi.RESET}!",), (["Hello, World!"], [[ColorSpan(7, 12, Ansi.BLUE)]])),
        ((f"Hello, {Ansi.RED}World!",), (["Hello, World!"], [[ColorSpan(7, 13, Ansi.RED)]])),
        ((f"{Ansi.BLUE}Hel{Ansi.RED}lo{Ansi.RESET}, world!",), (["Hello, world!"], [[ColorSpan(0, 3, Ansi.BLUE), ColorSpan(3, 5, Ansi.RED)]])),
        ((f"X{Ansi.RED}Y{Ansi.RESET}{Ansi.BLUE}Z{Ansi.RESET}",), (["XYZ"], [[ColorSpan(1, 2, Ansi.RED), ColorSpan(2, 3, Ansi.BLUE)]])),
        (("Just plain text",), (["Just plain text"], [[]])),
    ])

def test_applyColorSpans(method):
    RED = Ansi.RED
    BLUE = Ansi.BLUE
    RESET = Ansi.RESET

    testMethod(method, [
        # 1. Insert RED from 2–5 on line 0
        (
            "Insert RED from 2–5",
            ([ColorSpan(2, 5, RED)], []),
            [ColorCode(2, RED), ColorCode(5, RESET)]
        ),
        # 2. Two non-overlapping spans
        (
            "Two non-overlapping spans",
            ([ColorSpan(1, 3, RED), ColorSpan(5, 7, BLUE)], []),
            [ColorCode(1, RED), ColorCode(3, RESET), ColorCode(5, BLUE), ColorCode(7, RESET)]
        ),
        # 3. Overlapping span overwrites previous
        (
            "Overlapping span overwrites previous",
            ([ColorSpan(1, 6, RED)], [ColorCode(2, BLUE), ColorCode(4, RESET)]),
            [ColorCode(1, RED), ColorCode(6, RESET)]
        ),
        # 4. Existing color at start, new span overwrites and resumes correctly
        (
            "Existing color at start, new span overwrites and resumes",
            ([ColorSpan(2, 5, BLUE)], [ColorCode(0, RED), ColorCode(7, RESET)]),
            [ColorCode(0, RED), ColorCode(2, BLUE), ColorCode(5, RED), ColorCode(7, RESET)]
        ),
        # 5. Span matches existing, no duplicates
        (
            "Span matches existing, no duplicates",
            ([ColorSpan(0, 5, RED)], [ColorCode(0, RED), ColorCode(5, RESET)]),
            [ColorCode(0, RED), ColorCode(5, RESET)]
        ),
        # 6. Span is fully inside another, should overwrite inner part only
        (
            "Span fully inside another, overwrites inner part only",
            ([ColorSpan(2, 4, BLUE)], [ColorCode(0, RED), ColorCode(6, RESET)]),
            [ColorCode(0, RED), ColorCode(2, BLUE), ColorCode(4, RED), ColorCode(6, RESET)]
        ),
    ])

def test_ansi():
    from canvas import Ansi, Canvas
    canvas = Canvas(20, 10)
    canvas.box(0, 0, 20, 10, color=Ansi.GREEN, outline=True, pattern=("┌","─","┐","│","┘","└"))
    canvas.write(f"Hello, {Ansi.BLUE}w{Ansi.RESET}{Ansi.RESET}{Ansi.RED}orld!{Ansi.RESET}", color=Ansi.RED, x = 3, y = 5)
    canvas.sticker(1,5,"🍲")
    canvas.sticker(1,6,"🔥")
    canvas.sticker(15,5,"🍲")
    canvas.sticker(15,6,"🔥")
    canvas.sticker(5, 2, "😂")
    canvas.sticker(7, 2, "😂")
    canvas.sticker(9, 2, "😂")
    canvas.bar(2, 3, 16, 0.5, color = Ansi.BLUE)
    sprite = canvas.render()
    canvas.resize(30, 20)
    canvas.draw(sprite, x = 5, y = 5)
    print(canvas.render())

import time

class Message:
    def __init__(self, level: int, text: str, icon: Optional[str] = None, color=Ansi.WHITE):
        self.level = level
        self.icon = (icon + " ") if icon else ""
        self.color = color
        self.text = text
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    def __str__(self):
        return f"{self.icon}{self.color}{self.text}{Ansi.RESET}"

class Debug(Message):
    def __init__(self, text):
        super().__init__(0, text, "🐞", Ansi.WHITE)

class Info(Message):
    def __init__(self, text):
        super().__init__(1, text, "ℹ️", Ansi.CYAN)

class Warning(Message):
    def __init__(self, text):
        super().__init__(2, text, "⚠️", Ansi.YELLOW)

class Error(Message):
    def __init__(self, text):
        super().__init__(3, text, "❌", Ansi.RED)

class Logger:
    def __init__(self, level: type = Debug):
        self.level = level("").level
        self.show = level is Debug
        self.logs = []

    def log(self, message):
        if self.level >= message.level:
            self.logs.append(message)
        if self.show:
            print(self.logs[-1].text)

    def filter(self, level: type, only=False):
        level = level("").level
        if only:
            return [str(log) for log in self.logs if log.level == level]
        return [str(log) for log in self.logs if log.level >= level]

    def clear(self):
        self.logs = []