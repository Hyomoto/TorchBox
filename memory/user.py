"""
This file contains the user memory module for the Sock & Sorcery game.
It contains all user-related data and game state.
"""
from typing import Dict

class Attribute(dict):
    def __init__(self, current: int, base: int = None, max: int = None, min: int = 0):
        self.current = current
        self.base = base if base is not None else current
        self.max = max if max is not None else current
        self.min = min
    def __repr__(self):
        return str(self.current)

map = {
    "OUTPUT": "",
    "INPUT": "",
    "LINE": 0,
    "SCENE": "",
    "USER": None,
    "PLAYER": None,
}

class UserData(dict):
    def __init__(self):
        super().__init__(getUserData())
    def update(self):
        # TODO: implement update logic
        pass

def getUserData():
    return {
        "nickname" : "",
        "gender" : "",
        "race" : "",
        "money" : Attribute(0, max = 9_999_999),
        "hp" : Attribute(100),
        "actions" : Attribute(5),
        "skills" : {
            "attack": Attribute(1),
            "defense": Attribute(1),
        }
    }
