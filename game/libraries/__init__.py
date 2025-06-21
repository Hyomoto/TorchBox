from typing import Dict, List, Any
from tinder.library import Library, exportable, exportableAs, import_libraries as _import_libraries, static_eval_safe
from torchbox.realm import Realm, User
from ..memory.user import Player
from tinder import TinderBurn, Yielded
from tinder.crucible import Crucible, NO_SHADOWING
from typing import Optional
from .canvas import Canvas, Sprite
from constants import Ansi
from .sprites import SPRITES
import random
import re

def import_libraries(context: object, include: List[str] = ["all"], exclude: List[str] = []) -> Dict[str, Library]:
    return _import_libraries(__name__, context, include=include, exclude=exclude)

class BaseLibrary(Library):
    """
    The base Library is always available and provides basic functionality for scene management,
    input matching, debugging, and string manipulation.  It also provides access to ANSI color codes.
    """
    def __init__(self, context: object):
        super().__init__("base", context=context)
        self.colors = {name.lower(): color for name, color in Ansi.__dict__.items() if isinstance(color, str)}

    @exportableAs("scene")
    def changeScene(self, env: Crucible, scene: str, carry: Optional[dict] = None):
        """
        Change the scene for the player, setting up the local environment.
        Args:
            - scene (str): The name of the scene to change to.
            - carry (dict, optional): Additional data to carry over to the new scene.
        """
        user = env.parent # grab user scope
        stack: list = user["STACK"]
        while stack:
            stack.pop()
        stack.append(self.context.new_scope(scene, user))
        raise Yielded(carry=carry)  # Yield to allow the game loop to continue

    @exportableAs("enter")
    def enterScene(self, env: Crucible, scene: str, carry: Optional[dict] = None):
        """
        Push a new scene onto the stack, can be returned to using exit.
        Args:
            - scene (str): The name of the scene to enter.
            - carry (dict, optional): Additional data to carry over to the new scene.
        """
        user = env.parent # grab user scope
        stack: list = user["STACK"]
        stack.append(self.context.new_scope(scene, user))
        raise Yielded(carry=carry)  # Yield to allow the game loop to continue

    @exportableAs("exit")
    def exitScene(self, env: Crucible, carry: Optional[dict] = None):
        """
        Pops the current scene off the stack, returning to the previous scene.  If there is no previous
        scene, it will close the user's session.
        Args:
            - carry (dict, optional): Additional data to carry over to the previous scene.
        """
        user = env.parent # grab user scope
        stack: list = user["STACK"]
        stack.pop()
        print(user)
        raise Yielded(carry=carry)  # Yield to allow the game loop to continue

    @static_eval_safe 
    @exportableAs("keys")
    def keyList(self, env: Crucible, value: dict) -> list:
        return list(value.keys())

    @static_eval_safe 
    @exportable
    def batch(self, env: Crucible, *items: str) -> dict:
        map = {}
        for item in items:
            if not isinstance(item, str):
                raise TinderBurn(f"Batch item must be a String, got {type(item).__name__}.")
            if item.startswith("_"):
                map["_"] = item[1:]
            else:
                parts = item.split('.')
                full = "".join(parts)
                key = ""
                for part in parts:
                    key += part
                    map[key] = full
        return map
    
    @exportable
    def debug(self, env: Crucible, message: str):
        """
        Print a debug message to the console.
        Args:
            - message (str): The debug message to print.
        """
        print(f"[debug] {message}")

    @static_eval_safe 
    @exportable
    def len(self, env: Crucible, value: Any):
        """
        Return the length of the given value.
        Args:
            - value (Any): The value to get the length of.
        Returns:
            - int: The length of the value.
        """
        return len(value)

    @static_eval_safe 
    @exportableAs("str")
    def concat(self, env: Crucible, *args: Any) -> str:
        """
        Concatenate multiple values into a single string.
        Args:
            - args (Any): The values to concatenate.
        Returns:
            - str: The concatenated string.
        """
        return ''.join(str(arg) for arg in args)

    @static_eval_safe 
    @exportable
    def color(self, env: Crucible, color: str):
        """
        Return the ANSI escape code for the given color.  Valid colors are: BLACK, RED, GREEN, BROWN, BLUE,
        PURPLE, CYAN, YELLOW, WHITE, LIGHT_GRAY, LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE, LIGHT_PURPLE, LIGHT_CYAN, 
        DARK_GRAY.
        Args:
            - color (str): The name of the color.
        """
        return self.colors.get(color.lower(), Ansi.RESET)

COLOR_RE = re.compile(r'`(-?\d+)')

class TextLibrary(Library):
    def __init__(self, context: object):
        super().__init__("text", context)

    def strip_codes(self, text: str) -> str:
        return COLOR_RE.sub("", text)

    @exportable
    def join(self, env: Crucible, items: list, separator: str = "") -> str:
        """
        Join a list of items into a single string with the specified separator.
        Args:
            - items (list): The list of items to join.
            - separator (str): The separator to use (default: "").
        Returns:
            - str: The joined string.
        """
        return separator.join(str(item) for item in items)

    @exportable
    def split(self, env: Crucible, text: str, separator: str = None) -> list:
        """
        Split a string into a list of items using the specified separator.
        Args:
            - text (str): The string to split.
            - separator (str): The separator to use (default: None, splits on whitespace).
        Returns:
            - list: The list of items.
        """
        return text.split(separator) if separator else text.split()

    @exportable
    def replace(self, env: Crucible, text: str, old: str, new: str) -> str:
        """
        Replace occurrences of a substring in a string with another substring.
        Args:
            - text (str): The original string.
            - old (str): The substring to replace.
            - new (str): The substring to replace with.
        Returns:
            - str: The modified string.
        """
        return text.replace(old, new)

    @exportable
    def find(self, env: Crucible, text: str, substring: str, start: int = 0, end: int = -1) -> int:
        """
        Find the first occurrence of a substring in a string.
        Args:
            - text (str): The original string.
            - substring (str): The substring to find.
            - start (int): The starting index (default: 0).
            - end (int): The ending index (default: -1, meaning until the end).
        """
        return text.find(substring, start, end)

    @exportable
    def upper(self, env: Crucible, text: str) -> str:
        """
        Convert a string to uppercase.
        Args:
            - text (str): The string to convert.
        Returns:
            - str: The uppercase string.
        """
        return text.upper()

    @exportable
    def lower(self, env: Crucible, text: str) -> str:
        """
        Convert a string to lowercase.
        Args:
            - text (str): The string to convert.
        Returns:
            - str: The lowercase string.
        """
        return text.lower()

    @exportable
    def proper(self, env: Crucible, text: str) -> str:
        """
        Capitalize the first letter of a string.
        Args:
            - text (str): The string to capitalize.
        Returns:
            - str: The capitalized string.
        """
        return text.capitalize()

    @exportable
    def title(self, env: Crucible, text: str) -> str:
        """
        Convert a string to title case.
        Args:
            - text (str): The string to convert.
        Returns:
            - str: The title-cased string.
        """
        return text.title()

    @exportable
    def strip(self, env: Crucible, text: str) -> str:
        """
        Remove leading and trailing whitespace from a string.
        Args:
            - text (str): The string to strip.
        Returns:
            - str: The stripped string.
        """
        return text.strip()

    @exportable
    def column(self, env: Crucible, items: List[str], width: int, kwargs: dict) -> str:
        """
        Take a list of strings and combines them, separated by the given width and separator.
        Args:
            - text (List[str]): The list of strings to join.
            - width (int): The width of each column.
            - separator (str): The separator to use (default: "").
        Returns:
            - str: The formatted string with columns.
        """
        padding = kwargs.get("pad", "")
        separator = kwargs.get("separator", "")
        output = ""
        for i, v in enumerate(items):
            t = padding + str(v)
            s = self.strip_codes(t)
            if len(s) > width:
                s = s[:width]
                t = t[:width - len(s)]
            output += t + " " * (width - len(s))
            if separator and i < len(items) - 1:
                output = output[:-1] + separator
        return output

    @exportable
    def pad(self, env: Crucible, text: str, width: int, side: str = "left") -> str:
        """
        Pad a string to the specified width with spaces.
        Args:
            - text (str): The string to pad.
            - width (int): The total width of the padded string.
            - side (str): The side to pad on ('left', 'right', or 'both') (default: 'left').
        Returns:
            - str: The padded string.
        """
        text = str(text)
        if side == "left":
            return text.ljust(width)
        elif side == "right":
            return text.rjust(width)
        elif side == "both":
            return text.center(width)
        else:
            raise ValueError("Invalid side argument. Use 'left', 'right', or 'both'.")

class LoginLibrary(Library):
    """
    Library for user login and management, including finding users, checking passwords, setting passwords,
    and creating new users.  This Library requires the 'login' permission to be used.
    """
    def __init__(self, context: object):
        super().__init__("login", context, permissions=["login"])

    @exportable
    def find_user(self, env: Crucible, username: str) -> User:
        """
        Find a user by username.
        Args:
            - username (str): The username of the user to find.
        Returns:
            - User: The user object if found, otherwise None.
        """
        user: User = self.context.realm.getUser(username)
        stack = self.context.player.environment["STACK"]
        user["STACK"] = stack
        user.data.parent = self.context.shared
        self.context.player.environment = user.data
        return user

    @exportable
    def check_password(self, env: Crucible, user: User, password: str) -> bool:
        """
        Check if the provided password matches the user's password.
        Args:
            - user (User): The user object to check the password for.
            - password (str): The password to check.
        Returns:
            - bool: True if the password matches, otherwise False.
        """
        return user.checkPassword(password)

    @exportable
    def set_password(self, env: Crucible, user: User, password: str):
        """
        Set the user's password.
        Args:
            - user (User): The user object to set the password for.
            - password (str): The new password to set.
        """
        user.setPassword(password)

    @exportable
    def new_user(self, env: Crucible, username: str, password: str) -> User:
        """
        Create a new user with the given username and password.
        Args:
            - username (str): The username for the new user.
            - password (str): The password for the new user.
        Returns:
            - User: The newly created user object.
        """
        user = self.context.player.environment
        user["USER"] = Player(username) # Initialize user data
        return self.context.realm.addUser(User(username, password, user))

    @exportable
    def delete_user(self, env: Crucible, username: str):
        """
        Delete the specified user.
        Args:
            - user (User): The user object to delete.
        """
        user = self.context.realm.getUser(username)
        self.context.realm.removeUser(user)

class RandomLibrary(Library):
    def __init__(self, context: object):
        super().__init__("random", context)

    @exportable
    def randint(self, env: Crucible, a: int, b: int) -> int:
        return random.randint(a, b)

    @exportable
    def random(self, env: Crucible) -> float:
        return random.random()

    @exportable
    def choice(self, env: Crucible, x: list) -> Any:
        return random.choice(x)

    @exportable
    def shuffle(self, env: Crucible, x: list):
        random.shuffle(x)
        return x

class CanvasLibrary(Library):
    """
    Imports the canvas module and exposes its methods.  It's important to note that canvas.render() returns
    a Sprite object, so it must be converted to a string using concat() to be displayed properly.  This allows
    you to use the canvas to draw sprites and compose them into the final canvas if desired.

    ### Example:
    ```
    import canvas
    set CANVAS to canvas.create(80, 24)
    canvas.write(CANVAS, "Hello, World!", {"x": 10, "y": 5})
    set OUTPUT to concat(canvas.render(CANVAS))
    ```
    """
    def __init__(self, context: object):
        super().__init__("canvas", context)

    @exportable
    def create(self, env: Crucible, width: int, height: int) -> Canvas:
        """
        Returns a canvas with the specified width and height, which is passed to other canvas methods for drawing.

        Returns:
            Canvas: A new canvas object with the specified dimensions.
        """
        return Canvas(width, height)

    @exportable
    def write(self, env: Crucible, canvas: Canvas, text: str, kwargs: dict = None):
        """
        Write text to the canvas at the current canvas position.

        Args:
            - canvas (Canvas): The canvas to write to.
            - text (str): The text to write to the canvas.
        Kwargs:
            - color: An Ansi color code (default: None)
            - x (int): The x position to write the text (default: None, uses current position)
            - y (int): The y position to write the text (default: None, uses current position)
            - align (str): Alignment of the text ('left', 'center', 'right') (default: 'left')
        """
        canvas.write(text, **(kwargs or {}))

    @exportable
    def draw(self, env: Crucible, canvas: Canvas, sprite: Sprite, kwargs: dict = None):
        """
        Draw a sprite on the canvas at the current position.
        Args:
            - canvas (Canvas): The canvas to draw on.
            - sprite (Sprite): The sprite to draw.
        Kwargs:
            - x (int): The x position to draw the sprite (default: None, uses current position)
            - y (int): The y position to draw the sprite (default: None, uses current position)
            - color: An Ansi color code (default: None)
        """
        canvas.draw(sprite, **(kwargs or {}))

    @exportable
    def bar(self, env: Crucible, canvas: Canvas, x: int, y: int, width: int, progress: float, kwargs: dict = None):
        """
        Draw a progress bar on the canvas.  The pattern can also be a multiple character string where the bar
        is drawn gradiated from the first character to the last.
        Args:
            - canvas (Canvas): The canvas to draw on.
            - x (int): The x position to draw the bar.
            - y (int): The y position to draw the bar.
            - width (int): The width of the bar.
            - progress (float): The progress value (0.0 to 1.0).
        Kwargs:
            - color: An Ansi color code for the bar (default: None)
            - pattern (str): A character to use for the filled part of the bar (default: '█')
            - split (str): A character to use for the split between filled and empty parts (default: None)
            - vertical (bool): Whether to draw the bar vertically (default: False)
        """
        canvas.bar(x, y, width, progress, **(kwargs or {}))

    @exportable
    def line(self, env: Crucible, canvas: Canvas, x1: int, y1: int, x2: int, y2: int, kwargs: dict = None):
        """
        Draw a line on the canvas from (x1, y1) to (x2, y2).  The pattern can also be a list of characters,
        where the first will be the start, the last will be the end, and the rest will be repeated in between.
        Args:
            - canvas (Canvas): The canvas to draw on.
            - x1 (int): The starting x position.
            - y1 (int): The starting y position.
            - x2 (int): The ending x position.
            - y2 (int): The ending y position.
        Kwargs:
            - color: An Ansi color code (default: None)
            - pattern (str): A character to use for the line (default: '*')
        """
        canvas.line(x1, y1, x2, y2, **(kwargs or {}))

    @exportable
    def linea(self, env: Crucible, canvas: Canvas, x: int, y: int, length: int, kwargs: dict = None):
        """
        Draw a line on the canvas at the current position with a specified length.
        Args:
            - canvas (Canvas): The canvas to draw on.
            - x (int): The x position to start the line.
            - y (int): The y position to start the line.
            - length (int): The length of the line.
        Kwargs:
            - color: An Ansi color code (default: None)
            - pattern (str): A character to use for the line (default: '*')
            - vertical (bool): Whether to draw the line vertically (default: False)
        """
        canvas.linea(x, y, length, **(kwargs or {}))

    @exportable
    def box(self, env: Crucible, canvas: Canvas, x: int, y: int, width: int, height: int, kwargs: dict = None):
        """
        Draw a box on the canvas at the specified position with the given width and height.  The pattern can
        also be a multiple character string.  If three are provided, the first will be the corners, the second
        will be the horizontal edges, and the third will be the vertical edges.  If six are provided, the the
        order is top-left, horizontal, top-right, vertical, bottom-right, bottom-left.  Lastly, if outline is False,
        one extra character is required and will be used for the fill.
        Args:
            - canvas (Canvas): The canvas to draw on.
            - x (int): The x position to start the box.
            - y (int): The y position to start the box.
            - width (int): The width of the box.
            - height (int): The height of the box.
        Kwargs:
            - outline (bool): Whether to draw the box as an outline (default: True)
            - color (str): An Ansi color code (default: None)
            - pattern (str): A character to use for the box (default: '#')
        """
        canvas.box(x, y, width, height, **(kwargs or {}))

    @exportable
    def clear(self, env: Crucible, canvas: Canvas, char: str = ' '):
        """Clear the canvas with the specified character.
        Args:
            - canvas (Canvas): The canvas to clear.
            - char (str): The character to use for clearing (default: ' ')
        """
        canvas.clear(char)

    @exportable
    def render(self, env: Crucible, canvas: Canvas):
        """
        Render the canvas to a string representation.
        Args:
            - canvas (Canvas): The canvas to render.
        Returns:
            Sprite: The rendered canvas as a Sprite object.
        """
        return canvas.render()  # Return the string representation of the rendered canvas.

class SpritesLibrary(Library):
    """Has no exportable methods, but overrides export to allow loading from the sprites module."""
    def __init__(self, context: object):
        super().__init__("sprites", context)
        self.sprites = SPRITES

    def export(self, request: Optional[List[str]] = None) -> Dict[str, Any]:
        request = request or []
        if request:
            exported = {name: SPRITES[name] for name in SPRITES if name.lower() in request}
        else:
            exported = SPRITES
        return exported

class RealmLibrary(Library):
    """
    The Realm Library provides access to the realm, allowing you to interact with users, scenes, and other
    realm-related functionality. It requires the 'realm' permission to be used.
    """
    def __init__(self, context: object):
        super().__init__("realm", context, permissions=["realm"])

    @exportable
    def get_users(self, env: Crucible) -> List[User]:
        """
        Get a list of all users in the realm.
        Returns:
            List[User]: A list of User objects representing all users in the realm.
        """
        return list[self.context.realm.users]