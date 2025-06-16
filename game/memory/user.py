"""
This file contains the user memory module for the Sock & Sorcery game.
It contains all user-related data and game state.
"""
from typing import Optional, Dict
from typing import Tuple
from tinder.crucible import Crucible, NO_SHADOWING
from tinder import Tinder
from torchbox.realm import User
from torchbox.serializer import Serializer, serialize, deserialize
import inspect
import sys

def classes():
    classes = {}
    for name, obj in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and not inspect.isabstract(x)):
        classes[name] = obj
    return classes

class Attribute(dict, Serializer):
    def __init__(self, current: int, base: Optional[int] = None, max: Optional[int] = None, min: int = 0):
        self["current"] = current
        self["base"] = base if base is not None else current
        self["max"] = max if max is not None else current
        self["min"] = min
    
    def serialize(self) -> Dict[str, any]:
        return {key: value for key, value in self.items()}
    
    @classmethod
    def deserialize(cls, data: Dict[str, any], classes: Optional[dict] = None) -> "Attribute":
        return cls(
            current=data["current"],
            base=data["base"],
            max=data["max"],
            min=data["min"]
        )

    def __repr__(self):
        return str(self.current)

map = {
    "STACK" : [],
    "OUTPUT": "",
    "INPUT": "",
    "USER": None,
}

def new_user_data(nickname: str):
    return {
        "username" : nickname,
        "nickname" : nickname,
        "gender" : "Male",
        "race" : "Human",
        "money" : Attribute(0, max = 9_999_999),
        "hp" : Attribute(100),
        "actions" : Attribute(5),
        "profession" : None,
        "inventory" : [],
        "skills" : {
            "attack": Attribute(1),
            "defense": Attribute(1),
        }
    }
