from typing import Type, List, Optional
from constants import Ansi
from abc import ABC, abstractmethod
import time
import os

class Log(ABC):
    @abstractmethod
    def __init__(self, level: int, text: str, icon: Optional[str] = None, color=Ansi.WHITE):
        self.level = level
        self.icon = (icon + " ") if icon else ""
        self.color = color
        self.text = text
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    def full(self):
        return f"[{self.timestamp}] {self.text}"
    def __str__(self):
        return f"{self.icon}{self.color}{self.text}{Ansi.RESET}"

class Debug(Log):
    def __init__(self, text, custom: Optional[str] = None, color: Ansi = Ansi.WHITE):
        super().__init__(0, text, custom or "🐞", color)

class Info(Log):
    def __init__(self, text, custom: Optional[str] = None, color: Ansi = Ansi.CYAN):
        super().__init__(1, text, custom or "ℹ️ ", color)

class Warning(Log):
    def __init__(self, text, custom: Optional[str] = None, color: Ansi = Ansi.YELLOW):
        super().__init__(2, text, custom or "⚠️ ", color)

class Critical(Log):
    def __init__(self, text, custom: Optional[str] = None, color: Ansi = Ansi.RED):
        super().__init__(3, text, custom or "⛔", color)

class Logger:
    def __init__(self, level: Type[Log] = Debug, length: int = 0, output: Optional[str] = None):
        self.level = level("").level
        self.show = True
        self.logs: List[Log] = []
        self.output = output
        self.length = length
        if output is not None:
            # create directory if it doesn't exist
            os.makedirs(os.path.dirname(output), exist_ok=True)
            # create file, overwriting if it exists
            with open(output, "w") as f:
                f.write("")

    def log(self, message: Log):
        if message.level >= self.level:
            self.logs.append(message)
            if self.show:
                print(self.logs[-1])
        return self
    
    def write(self, clear = True):
        if self.output is not None:
            with open(self.output, "a") as f:
                for log in self.logs[-self.length:]:
                    f.write(log.full() + "\n")
        if clear:
            self.clear()
        return self

    def filter(self, level: Type[Log], only=False):
        level = level("").level
        if only:
            return [str(log) for log in self.logs if log.level == level]
        return [str(log) for log in self.logs if log.level >= level]

    def setLevel(self, level: Type[Log]):
        self.level = level("").level
        return self

    def clear(self):
        self.logs = []
        return self
