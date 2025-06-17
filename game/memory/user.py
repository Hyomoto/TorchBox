"""
This file contains the user memory module for the Sock & Sorcery game.
It contains all user-related data and game state.
"""
from typing import Optional, Dict, List, Any
from typing import Tuple
from tinder.crucible import Crucible, NO_SHADOWING
from tinder import Tinder
from torchbox.realm import User
from torchbox.serializer import Serializer, serialize, deserialize
from abc import ABC, abstractmethod
import operator
import inspect
import sys


def classes():
    classes = {}
    for name, obj in inspect.getmembers(
            sys.modules[__name__],
            lambda x: inspect.isclass(x) and not inspect.isabstract(x)):
        classes[name] = obj
    return classes

class Player(dict, Serializer):
    def __init__(self, name=None):
        self["username"] = name
        self["nickname"] = name
        self["money"] = Attribute(0, max=9_999_999)
        self["attributes"] = {
            "hp": Attribute(100),
            "actions": Attribute(5),
            "combat": Attribute(1),
            "defense": Attribute(1),
        }
        self["modifiers"] = {
            "gender": NamedModifier("Male", modifiers=[("combat", 1, "+")]),
            "race": NamedModifier("Human"),
            "background": NamedModifier("Urchin"),
            "profession": None,
            "weapon" : None,
            "armor" : None,
        }
        self["inventory"] = []

    def serialize(self) -> Dict[str, Any]:
        return {key: serialize(value) for key, value in self.items()}

    @classmethod
    def deserialize(cls,
                    data: Dict[str, Any],
                    classes: Optional[dict] = None) -> "Player":
        player = cls()
        for key, value in data.items():
            player[key] = deserialize(value, classes)

class Modifier(ABC):
    @abstractmethod
    def __init__(self, modifiers=[], **kwargs):
        self.modifiers = modifiers
        super().__init__(**kwargs)

    def __contains__(self, key: str) -> bool:
        return len([item for item in self.modifiers if item[0] == key]) > 0

class NamedModifier(Modifier, Serializer):
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def serialize(self) -> Dict[str,Any]:
        return {
            "name": self.name,
            "modifiers": self.modifiers,
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any], classes: Optional[dict] = None) -> "NamedModifier":
        return cls(
            name=data["name"],
            modifiers=[(a,b,c) for a,b,c in data["modifiers"]]
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"NamedModifier(name={self.name}, modifiers={self.modifiers})"
        
class Attribute(Serializer):
    def __init__(self,
                 current: int,
                 base: Optional[int] = None,
                 max: Optional[int] = None,
                 min: int = 0):
        self.current = current
        self.base = base if base is not None else current
        self.max = max if max is not None else current
        self.min = min

    def __contains__(self, key: str) -> bool:
        return key in ["current", "base", "max", "min"]
        
    def mutate(self, other, op):
        if isinstance(other, Attribute):
            value = other.current
        elif isinstance(other, (int, float)):
            value = other
        else:
            raise TypeError(
                f"Cannot modify Attribute with {type(other).__name__}.")
        result = min(max(op(self.current, value), self.min ), self.max )
        return Attribute(result, self.base, self.max, self.min)

    def compare(self, other, op) -> bool:
        if isinstance(other, Attribute):
            value = other.current
        elif isinstance(other, (int, float)):
            value = other
        else:
            return False
        return op(self.current, value)

    def unary(self, op):
        value = min(max(op(self.current), self.min),self.max)
        return Attribute(value, self.base, self.max, self.min)

    def __add__(self, other): return self.mutate(other, operator.add)
    def __radd__(self, other): return self.__add__(other)
    def __sub__(self, other): return self.mutate(other, operator.sub)
    def __rsub__(self, other): return self.mutate(other, lambda x, y: y - x)
    def __mul__(self, other): return self.mutate(other, operator.mul)
    def __rmul__(self, other): return self.__mul__(other)
    def __truediv__(self, other): return self.mutate(other, operator.truediv)
    def __rtruediv__(self, other): return self.mutate(other, lambda x, y: y / x)
    def __floordiv__(self, other): return self.mutate(other, operator.floordiv)
    def __rfloordiv__(self, other): return self.mutate(other, lambda x, y: y // x)
    def __mod__(self, other): return self.mutate(other, operator.mod)
    def __rmod__(self, other): return self.mutate(other, lambda x, y: y % x)
    def __pow__(self, other): return self.mutate(other, operator.pow)
    def __rpow__(self, other): return self.mutate(other, lambda x, y: y**x)
    def __eq__(self, other): return self.compare(other, operator.eq)
    def __ne__(self, other): return self.compare(other, operator.ne)
    def __lt__(self, other): return self.compare(other, operator.lt)
    def __le__(self, other): return self.compare(other, operator.le)
    def __gt__(self, other): return self.compare(other, operator.gt)
    def __ge__(self, other): return self.compare(other, operator.ge)

    def __iadd__(self, other): return self.mutate(other, operator.add)
    def __isub__(self, other): return self.mutate(other, operator.sub)
    def __imul__(self, other): return self.mutate(other, operator.mul)
    def __itruediv__(self, other): return self.mutate(other, operator.truediv)
    def __ifloordiv__(self, other): return self.mutate(other, operator.floordiv)
    def __imod__(self, other): return self.mutate(other, operator.mod)
    def __ipow__(self, other): return self.mutate(other, operator.pow)

    def __str__(self): return str(self.current)
    def __bool__(self): return self.unary(operator.truth)
    def __int__(self): return self.unary(int)
    def __float__(self): return self.unary(float)
    def __neg__(self): return self.unary(operator.neg)
    def __pos__(self): return self.unary(operator.pos)
    def __abs__(self): return self.unary(operator.abs)
    def __invert__(self): return self.unary(operator.invert)

    def serialize(self) -> List[int]:
        return [self.current, self.base, self.max, self.min]

    @classmethod
    def deserialize(cls,
                    data: List[int],
                    classes: Optional[dict] = None) -> "Attribute":
        return cls(
            current=data[0],
            base=data[1],
            max=data[2],
            min=data[3],
        )

    def __repr__(self):
        return f"Attribute(current={self.current}, base={self.base}, max={self.max}, min={self.min})"


map = {
    "STACK": [],
    "OUTPUT": "",
    "INPUT": "",
    "USER": None,
}


def new_user_data(nickname: str):
    return {
        "username": nickname,
        "nickname": nickname,
        "gender": "Male",
        "race": "Human",
        "money": Attribute(0, max=9_999_999),
        "hp": Attribute(100),
        "actions": Attribute(5),
        "modifiers": {},
        "background": "A mysterious stranger.",
        "profession": None,
        "inventory": [],
        "skills": {
            "attack": Attribute(1),
            "defense": Attribute(1),
        }
    }
