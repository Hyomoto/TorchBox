from typing import Optional
from constants import Ansi
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
