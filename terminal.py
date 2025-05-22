import textwrap

class Terminal:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.lines = []

    def write(self, *args: str):
        """Print text to the terminal."""
        for line in args:
            lines = line.split("\n")
            for subline in lines:
                if subline == "":
                    self.lines.append("")
                    continue
                wrapped = textwrap.wrap(subline, self.width)
                self.lines.extend(wrapped)
        while len(self.lines) > self.height:
            self.lines.pop(0)

    def writer(self, *args: str):
        """Print text to the terminal without wrapping."""
        for line in args:
            lines = line.split("\n")
            self.lines.extend(lines)
        while len(self.lines) > self.height:
            self.lines.pop(0)

    def clear(self):
        self.lines = []

    def render(self):
        return "\n".join(self.lines)
