from typing import Dict, List, Any
from torchbox.api import API, exportable, exportableAs, import_api as _import_api
from torchbox.realm import Realm, User
from .memory.user import UserData
from tinder import Kindling, TinderBurn, Yielded, Jumped, Array
from tinder.crucible import Crucible, NO_SHADOWING
from typing import Optional
from .canvas import Canvas, Sprite
from constants import Ansi
from .sprites import SPRITES
import random

def import_api(context: object, include: List[str] = ["all"], exclude: List[str] = []):
    return _import_api(__name__, context, include=include, exclude=exclude)

class BaseAPI(API):
    def __init__(self, context: object):
        super().__init__("base", context=context)
        self.colors = {name.lower(): color for name, color in Ansi.__dict__.items() if isinstance(color, str)}

    @exportable
    def changeScene(self, env: Crucible, scene: str, carry: Optional[dict] = None):
        """Change the scene for the player, setting up the local environment."""
        script = self.context.get(scene)
        if not script:
            raise TinderBurn(f"Scene '{scene}' not found.")
        user = env.parent # grab user scope
        local = Crucible(NO_SHADOWING, parent=user) # initialize new local scope
        user["STACK"] = [(0, scene, local)]
        raise Yielded(line=0, carry=carry)  # Yield to allow the game loop to continue

    @exportableAs("enter")
    def enterScene(self, env: Crucible, scene: str, carry: Optional[dict] = None):
        """Push a new scene onto the stack."""
        script = self.context.get(scene)
        if not script:
            raise TinderBurn(f"Scene '{scene}' not found.")
        user = env.parent # grab user scope
        local = Crucible(NO_SHADOWING, parent=user) # initialize new local scope
        stack: list = user["STACK"]
        stack.append((0, scene, local))
        raise Yielded(line=0, carry=carry)  # Yield to allow the game loop to continue

    @exportableAs("exit")
    def exitScene(self, env: Crucible, carry: Optional[dict] = None):
        """Pop the current scene off the stack."""
        user = env.parent # grab user scope
        stack: list = user["STACK"]
        stack.pop()
        raise Yielded(line=0, carry=carry)  # Yield to allow the game loop to continue

    @exportableAs("match")
    def matchInput(self, env: Crucible, input: str, matches: dict, otherwise: str | int = None):
        """Match the input against a dictionary of possible matches."""
        if input not in matches and otherwise:
            raise Jumped(otherwise)
        return matches.get(input)
    
    @exportable
    def debug(self, env: Crucible, message: str):
        print(f"[debug] {message}")
    
    @exportable
    def len(self, env: Crucible, value: Any):
        return len(value)
    
    @exportable
    def concat(self, env: Crucible, *args: Any) -> str:
        return ''.join(str(arg) for arg in args)
    
    @exportable
    def color(self, env: Crucible, color: str):
        """Return the ANSI escape code for the given color."""
        return self.colors.get(color.lower(), Ansi.RESET)

class LoginAPI(API):
    def __init__(self, context: object):
        super().__init__("login", context, permissions=["login"])

    @exportable
    def find_user(self, env: Crucible, username: str) -> User:
        return self.context.realm.getUser(username)

    @exportable
    def check_password(self, env: Crucible, user: User, password: str) -> bool:
        return user.checkPassword(password)

    @exportable
    def set_password(self, env: Crucible, user: User, password: str):
        user.setPassword(password)

    @exportable
    def set_nickname(self, env: Crucible, user: User, nickname: str):
        user.setNickname(nickname)

    @exportable
    def new_user(self, env: Crucible, username: str, password: str) -> User:
        return self.context.realm.addUser(User(username, password, UserData()))

class RandomAPI(API):
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
    
class CanvasAPI(API):
    def __init__(self, context: object):
        super().__init__("canvas", context)

    @exportable
    def create(self, env: Crucible, width: int, height: int) -> Canvas:
        return Canvas(width, height)
    
    @exportable
    def write(self, env: Crucible, canvas: Canvas, text: str, kwargs: dict = None):
        canvas.write(text, **(kwargs or {}))

    @exportable
    def draw(self, env: Crucible, canvas: Canvas, sprite: Sprite, kwargs: dict = None):
        canvas.draw(sprite, **(kwargs or {}))

    @exportable
    def bar(self, env: Crucible, canvas: Canvas, x: int, y: int, width: int, progress: float, kwargs: dict = None):
        canvas.bar(x, y, width, progress, **(kwargs or {}))

    @exportable
    def line(self, env: Crucible, canvas: Canvas, x1: int, y1: int, x2: int, y2: int, kwargs: dict = None):
        canvas.line(x1, y1, x2, y2, **(kwargs or {}))

    @exportable
    def linea(self, env: Crucible, canvas: Canvas, x: int, y: int, length: int, kwargs: dict = None):
        canvas.linea(x, y, length, **(kwargs or {}))

    @exportable
    def box(self, env: Crucible, canvas: Canvas, x: int, y: int, width: int, height: int, kwargs: dict = None):
        canvas.box(x, y, width, height, **(kwargs or {}))

    @exportable
    def clear(self, env: Crucible, canvas: Canvas):
        canvas.clear()

    @exportable
    def render(self, env: Crucible, canvas: Canvas):
        return canvas.render()  # Return the string representation of the rendered canvas.

class SpritesAPI(API):
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
