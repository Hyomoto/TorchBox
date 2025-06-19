from typing import List, Tuple
from wcwidth import wcswidth
import re

ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]*m')
RESET = "\033[0m"

class Span:
    def __init__(self, start: tuple, end: tuple):
        self.start = start
        self.end = end
        self.horizontal = start[1] == end[1]

    def __len__(self):
        return max(abs(self.end[0] - self.start[0]), abs(self.end[1] - self.start[1])) + 1

    def __repr__(self):
        return f"[{self.start}-{self.end}]"

class ColorSpan:
  def __init__(self, start: int, end: int, color: str):
    self.start = start
    self.end = end
    self.color = color

  def __len__(self):
    return self.end - self.start

  def __repr__(self):
    return f"{self.color}{self.start}-{self.end}{RESET}"

  def __eq__(self, other):
    if not isinstance(other, ColorSpan):
      return False
    return self.start == other.start and self.end == other.end and self.color == other.color

class ColorCode:
  def __init__(self, position: int, code: str):
    self.position = position
    self.code = code

  def __repr__(self):
    return f"{self.code}@{self.position}{RESET}"

  def __eq__(self, other):
    if not isinstance(other, ColorCode):
      return False
    return self.position == other.position and self.code == other.code

class Sticker:
    def __init__(self, x: int, text: str):
        self.x = x
        self.text = text
        self.width = wcswidth(text)

    def __repr__(self):
        return f"Sticker({self.x}, {self.y}, {self.text})"

class Sprite:
    def __init__(self, lines: List[str], stickers: List[Sticker], width):
        self.lines = lines
        self.stickers = stickers
        self.width = width
        self.height = len(lines)

    def __repr__(self):
        output = [line for line in self.lines]

        for i, stickers in enumerate(self.stickers):
            for sticker in stickers:
                x, y = sticker.x, i
                count, offset= x, 0
                while count:
                    match = ANSI_PATTERN.match(output[y], offset)
                    if match:
                        offset = match.end()
                    else:
                        offset += 1
                        count -= 1
                while True:
                    sanity = ANSI_PATTERN.match(output[y], offset)
                    if not sanity:
                        break
                    offset = sanity.end()
                output[y] = output[y][:offset] + sticker.text + output[y][offset + sticker.width:]
        return "\n".join(output)

def getColorSpans(text: str, color = None) -> Tuple[list[str], List[List[ColorSpan]]]:
    lines = text.split("\n")
    colors = [[] for _ in range(len(lines))]
    if len(lines) == 0:
        return lines, colors
    span = None
    i, line = 0, lines[0]

    for i, line in enumerate(lines):
        matches = list(ANSI_PATTERN.finditer(line))
        offset = 0
        span = None

        for match in matches:
            start, end = match.span()
            start -= offset  # adjust position after removals
            end -= offset

            line = line[:start] + line[end:]
            offset += end - start

            code = match.group()
            if span:
                colors[i].append(ColorSpan(span[0], start, span[1]))
            if code == RESET:
                span = None
            else:
                span = (start, code)
            lines[i] = line
        if span:
            colors[i].append(ColorSpan(span[0], len(line), span[1]))
            span = None

    if span:
        colors[i].append(ColorSpan(span[0], len(line), span[1]))

    if color:
        colors[i].insert(0, ColorSpan(0, len(line), color))

    lines[i] = line
    return lines, colors

class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.clear()

    def newline(self):
        self.canvas.append(" " * self.width)
        self.colors.append([])

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self.clear()

    def clear(self, char = " "):
        self.canvas = [char * self.width for _ in range(self.height)]
        self.colors = [[] for _ in range(self.height)]
        self.cursor = [0, 0]
        self.color = None
        self.stickers = [[] for _ in range(self.height)]

    def moveTo(self, x: int, y: int):
        self.cursor = [x, y]
        return self

    def draw(self, sprite: Sprite, x: int = None, y: int = None, color = None):
        for i, line in enumerate(sprite.lines):
            for sticker in sprite.stickers[i]:
                self.stickers[y].append(Sticker(sticker.x + x, sticker.text))
            self.write(line, x=x, y=y, color = color, newline=False)
            y = self.cursor[1] + 1

    def write(self, text: str, **kwargs):
        """
        Write text to the canvas at the current cursor position.

        Args:
            text (str): The text to write.
            kwargs (dict): Optional keyword arguments.
                - x (int): The x-coordinate to write at. Defaults to the current cursor position.
                - y (int): The y-coordinate to write at. Defaults to the current cursor position.
                - color (str): The color to write in. Defaults to the current color.
                - align (str): The alignment of the text. Can be 'left', 'center', or 'right'. Defaults to 'left'.
        """
        def applySubCanvas(subCanvas, x, y):
            if subCanvas == [""]:
                return x, y
            width = 0
            for i, line in enumerate(subCanvas):
                row = y + i
                if row >= self.height:
                    self.newline()
                self.canvas[row] = (
                    self.canvas[row][:x] +
                    line[:max(0, self.width - x)] +
                    self.canvas[row][x + len(line):]
                )
                width = max(width, len(line[:max(0, self.width - x)]))
            return x + width, y + len(subCanvas) - 1

        def applyColorSpans(x, spans: List[ColorSpan], table: List[ColorCode]):
            tableIndex = 0
            spanIndex = 0
            spanLast = spans[ 0 ] if spans else None

            while spanLast:
                if tableIndex < len(table) and table[tableIndex].position < spanLast.start + x:
                    tableIndex += 1
                else:
                    table.insert(tableIndex, ColorCode(spanLast.start + x, spanLast.color))
                    tableIndex += 1
                    while tableIndex < len(table):
                        if table[tableIndex].position >= spanLast.end + x:
                            break
                        table.pop(tableIndex)
                    table.insert(tableIndex, ColorCode(spanLast.end + x, RESET))
                    spanIndex += 1
                    spanLast = spans[spanIndex] if spanIndex < len(spans) else None
            return table
        color = kwargs.get("color", self.color)
        align = kwargs.get("align", "left")
        width = kwargs.get("width", self.width)
        x = self.cursor[0] if kwargs.get("x") is None else kwargs.get("x")
        y = self.cursor[1] if kwargs.get("y") is None else kwargs.get("y")
        newline = kwargs.get("newline", True)
        if align == "center":
            text = text.center(width)
        elif align == "right":
            text = text.rjust(width)

        canvas, colors = getColorSpans(text, color)
        x0, y0 = applySubCanvas(canvas, x, y)

        for i, spans in enumerate(colors):
            row = y + i
            if not spans:
                continue
            applyColorSpans(x, spans, self.colors[row])
        if newline:
            y0 += 1
        while len(self.canvas) > self.height:
            self.canvas.pop(0)
            self.colors.pop(0)
            y0 -= 1
        self.cursor = [x0, y0]

    def bar(self, x, y, width, progress, vertical=False, pattern="░▒▓█ ", split = None, **kwargs):
        """Draw a progress bar at the specified position with the given width and progress."""
        if len(pattern) == 1:
            pattern = pattern + " "
        if not split:
            split = pattern[-2] # second to last character in pattern
        empty = pattern[-1]
        # Clamp progress
        progress = max(0.0, min(1.0, progress))
        filled = int(progress * width)
        chars = []
        patlen = len(pattern) - 1
        for i in range(filled):
            if filled == 1:
                idx = 0
            else:
                idx = int(round(i * (patlen - 1) / max(filled - 1, 1)))
            chars.append(pattern[idx])
        remaining = width - filled
        if progress < 1.0 and remaining > 0 and filled > 0:
            barstr = "".join(chars[:-1]) + split + empty * remaining
        else:
            barstr = "".join(chars) + empty * remaining
        self.linea(x, y, width, vertical=vertical, pattern=barstr, **kwargs)

    def linea(self, x0, y0, length, vertical=False, **kwargs):
        """Draw a line of specified length in the given direction (vertical or horizontal)."""
        x1 = x0 if vertical else x0 + (length - 1 if length > 0 else length + 1)
        y1 = y0 + (length - 1 if length > 0 else length + 1) if vertical else y0
        self.line(x0, y0, x1, y1, **kwargs)

    def line(self, x0, y0, x1, y1, **kwargs):
        """Draw a line from (x0, y0) to (x1, y1) with the specified pattern and color."""
        def generateSpans(x0, y0, x1, y1):
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            steps = [ 1 if x1 > x0 else -1, 1 if y1 > y0 else -1 ]
            coords = [x0, y0]
            h = dx > dy
            major, minor = int(not h), int(h)
            err = (dx if h else dy) // 2
            end = x1 if h else y1

            start = (x0, y0)
            spans = []

            while coords[major] != end:
                err -= (dy if h else dx)
                if err < 0:
                    spans.append(Span(start, tuple(coords)))
                    coords[minor] += steps[minor]
                    err += (dx if h else dy)
                    start = None
                coords[major] += steps[major]
                if not start:
                    start = tuple(coords)
            spans.append(Span(start, tuple(coords)))

            return spans

        color = kwargs.get("color", None)
        pattern = kwargs.get("pattern", "*")

        if len(pattern) == 1:
            left, mid, right = pattern, pattern, pattern
        elif len(pattern) == 3:
            left, mid, right = pattern
        else:
            raise ValueError("Pattern must have 1 or 3 elements.")

        inner = 1 + max(abs(x0-x1),abs(y0-y1)) - len(left) - len(right)
        repeat = (inner // len(mid)) + 2
        template = f"{left}{(mid * repeat)[:inner]}{right}"

        spans = generateSpans(x0, y0, x1, y1)
        offset = 0

        for span in spans:
            slice = template[offset:offset + len(span)]
            self.write(slice if span.horizontal else "\n".join(slice), x=span.start[0], y=span.start[1], color=color)
            offset += len(span)

    def box(self, x, y, width, height, outline=True, color=None, pattern="█"):
        # Pattern resolution
        fill = " "
        if len(pattern) == 1:
            ul = ur = bl = br = v = h = pattern[0]
            fill = pattern[0] if not outline else fill
        elif len(pattern) == 2 and outline:
            ul = ur = bl = br = v = h = pattern[0]
            fill = pattern[1]
        elif len(pattern) == 3 and outline:
            corner, h, v = pattern
            ul = ur = bl = br = corner
        elif len(pattern) == 4:
            corner, h, v, fill = pattern
            ul = ur = bl = br = corner
        elif len(pattern) == 6 and outline:
            ul, h, ur, v, br, bl = pattern
        elif len(pattern) == 7:
            ul, h, ur, v, br, bl, fill = pattern
        else:
            raise ValueError("Pattern must have 1, 4, or 7 elements." if not outline else "Pattern must have 1, 3, or 6 elements.")

        if len(ul) != len(ur) != len(bl) != len(br) != len(v) != len(h) != len(fill):
            raise ValueError("All pattern elements must have the same length.")
        size = len(ul)
        lines = []
        inner = width - 2 * size
        repeat = (inner // size) + 2

        for row in range(height):
            if row == 0:
                body = (h * repeat)[:inner]
                lines.append(f"{ul}{body}{ur}")
            elif row == height - 1:
                body = (h * repeat)[:inner]
                lines.append(f"{bl}{body}{br}")
            else:
                body = (fill * repeat)[:inner]
                lines.append(f"{v}{body}{v}")
        # Draw to canvas
        for i, line in enumerate(lines):
            self.write(line, x=x, y=y + i, color=color, newline=False)

    def sticker(self, x, y, text):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        self.stickers[y].append(Sticker(x, text))

    def render(self):
        output = [line for line in self.canvas]
        for i, colors in enumerate(self.colors):
            if not colors:
                continue
            stack = []
            for color in colors:
                if color.code == RESET:
                    if stack:
                        stack.pop()
                    color.code = stack[-1].code if stack else RESET
                else:
                    stack.append(color)

            for color in reversed(colors):
                output[i] = output[i][:color.position] + color.code + output[i][color.position:]
        return Sprite(output, self.stickers, self.width)
