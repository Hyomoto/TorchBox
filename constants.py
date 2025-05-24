from typing import List, Dict, Optional, Any
import random
import re

class Ansi:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    YELLOW = "\033[1;33m"
    WHITE = "\033[1;37m"
    LIGHT_GRAY = "\033[0;37m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    DARK_GRAY = "\033[1;30m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    RESET = "\033[0m"


class BaseItem:
    count: int
    maxcount: int
    def __init__(self, count: int = 1):
        self.count = count
        self.maxcount = 1
    def clone(self, count):
        return self.__class__(count)


class Item(BaseItem): # unique item
    name: str
    description: str
    def __init__(self, name: str, description: str):
        super().__init__(1)
        self.name = name
        self.description = description
    def __repr__(self):
        return f"Item({self.name})"
    def __eq__(self, other):
        if isinstance(other, Item):
            return self.name == other.name
        return False


class ItemStack(Item): # stackable item
    def __init__(self, name: str, description: str, maxcount: int = 99):
        super().__init__(name, description)
        self.maxcount = maxcount
    def __repr__(self):
        return f"ItemStack({self.name}, {self.count}/{self.maxcount})"

    def add(self, count: int):
        if self.count + count > self.maxcount:
            return count - (self.maxcount - self.count) # return excess
        self.count += count
        return 0

    def remove(self, count: int):
        if self.count - count < 0:
            return count - self.count # return excess
        self.count -= count


class Inventory:
    items: List[Item]
    size: int
    def __init__(self, size = 0):
        self.items = []
        self.size = size
    def __len__(self):
        return len(self.items)
    def __repr__(self):
        return f"Inventory({len(self.items)}/{self.size if self.size > 0 else '∞'})"
    def __getitem__(self, index: int):
        if index < 0 or index >= len(self.items):
            raise IndexError("Inventory index out of range")
        return self.items[index]
    def __setitem__(self, index: int, item: Item):
        if index < 0 or index >= len(self.items):
            raise IndexError("Inventory index out of range")
        if not isinstance(item, Item):
            raise TypeError("Inventory item must be an instance of Item")
        self.items[index] = item
    def __contains__(self, item: Item):
        return item in self.items
    def __iter__(self):
        return iter(self.items)
    def isFull(self):
        return 0 if self.size == 0 else len(self.items) >= self.size

    def resize(self, size: int):
        """Resize the inventory to a new size."""
        if size < len(self.items):
            self.items = self.items[:size]
        self.size = size

    def find(self, item: Item, start: int = 0):
        """Find an item in the inventory."""
        if start < 0 or start >= len(self.items):
            return -1
        for i in range(start, len(self.items)):
            if self.items[i] == item:
                return i
        return -1

    def has(self, item: Item):
        """Check if the inventory has an item."""
        last = 0
        while item.count > 0:
            last = self.find(item, last)
            if last == -1:
                return False
            item.count -= self.items[last].count
            last += 1
        return True

    def add(self, item: Item):
        """Add an item to the inventory."""
        if self.isFull():
            return item.count
        if isinstance(item, ItemStack):
            last = 0
            while item.count > 0:
                last = self.find(item, last)
                if last == -1:
                    break
                item.count = self.items[last].add(item.count)
                last += 1
        while item.count > 0:
            if self.isFull():
                return item.count
            copy = item.clone(min(item.count, item.maxcount))
            item.count -= copy.count
            self.items.append(copy)
        return item.count if item.count > 0 else 0

    def remove(self, item: Item):
        """Remove an item from the inventory."""
        last = 0
        while item.count > 0:
            last = self.find(item, last)
            if last == -1:
                return item.count
            item.count = self.items[last].remove(item.count)
            if self.items[last].count == 0:
                del self.items[last]
            else:
                last += 1


class FixedInventory(Inventory):
    items: List[Optional[Item]]
    size: int
    def __init__(self, size = 0):
        super().__init__(size)
        self.items = [None] * size

    def nextEmpty(self):
        """Find the next empty slot in the inventory."""
        for i, item in enumerate(self.items):
            if item is None:
                return i
        return -1

    def resize(self, size: int):
        """Resize the inventory to a new size."""
        if size < len(self.items):
            self.items = self.items[:size]
        else:
            self.items.extend([None] * (size - len(self.items)))
        self.size = size

    def isFull(self):
        return self.nextEmpty() == -1

    def add(self, item: Item):
        """Add an item to the inventory."""
        if self.isFull():
            return item.count
        if isinstance(item, ItemStack):
            last = 0
            while item.count > 0:
                last = self.find(item, last)
                if last == -1:
                    break
                item.count = self.items[last].add(item.count)
                last += 1
        while item.count > 0:
            if self.isFull():
                return item.count
            copy = item.clone(min(item.count, item.maxcount))
            item.count -= copy.count
            self.items[self.nextEmpty()] = copy
        return item.count if item.count > 0 else 0

    def remove(self, item: Item):
        """Remove an item from the inventory."""
        last = 0
        while item.count > 0:
            last = self.find(item, last)
            if last == -1:
                return item.count
            item.count = self.items[last].remove(item.count)
            if self.items[last].count == 0:
                self.items[last] = None
            last += 1

class Player:
    name: str
    weapon: Item
    armor: Item
    items: Inventory
    gold: int
    def __init__(self):
        self.name = "Player"
        self.weapon = None
        self.armor = None
        self.items = Inventory()
        self.gold = 0


class Monster:
    def __init__(self, name: str, weapon: str, strength: int, hp: int, gold: int, xp: int, message: str):
        self.name = name
        self.weapon = weapon
        self.strength = strength
        self.hp = hp
        self.gold = gold
        self.xp = xp
        self.message = message

    def clone(self):
        return self.__class__(self.name, self.weapon, self.strength, self.hp, self.gold, self.xp, self.message)


class Dice:
    num: int
    sides: int
    def __init__(self, notation="6"):
        self.total = 0

        pattern = re.fullmatch(r"(?:(\d*)d)?(\d+)", notation.lower())
        if not pattern:
            raise ValueError(f"Invalid dice format: {notation}")

        self.num = int(pattern.group(1)) if pattern.group(1) else 1
        self.sides = int(pattern.group(2))

    def roll(self):
        rolls = [random.randint(1, self.sides) for _ in range(self.num)]
        return sum(rolls)

    def __str__(self):
        return f"Dice({self.num}d{self.sides})"

class PercentileDice(Dice):
    def __init__(self):
        super().__init__("2d10")

    def roll(self):
        rolls = [random.randint(1, self.sides) for _ in range(self.num)]
        return rolls[0] + (rolls[1] - 1) * 10


class Macro:
    """
    A macro is a simple string replacement.  The terminal will replace a matched key with the macro value.
    """
    replace: str
    def __init__(self, replace: str):
        self.replace = replace


class Crucible:
    parent: Optional["Crucible"]
    variables: Dict[str, Any]
    def __init__(self, source = None, parent = None, protected = False):
        self.variables = source or {}
        self.parent = parent
        self.protected = protected

    def __contains__(self, var: str):
        first = var.split(".")[0]
        if first in self.variables:
            return True
        if self.parent:
            return first in self.parent
        return False
    
    def __repr__(self):
        if self.protected:
            return f"Crucible({self.variables}, protected, {self.parent})"
        return f"Crucible({self.variables}, {self.parent})"

    def set(self, var: str, value, protected = False):
        if self.parent and var in self.parent:
            if self.parent.protected:
                raise Ember(f"Tried to write to a protected scope: '{var}'!")
            self.parent.set(var, value, protected = True)
            return
        points = var.split('.')
        scope = self.variables
        while len(points) > 1:
            if points[0] not in scope:
                if protected:
                    break # push error to outer scope
                scope[points[0]] = {}
            scope = scope[points[0]]
            points.pop(0)
        if protected:
            if points[0] not in scope:
                raise Ember(f"Tried to write non-existing '{var}' in protected scope.")
            if not isinstance(value, type(scope[points[0]])):
                raise Ember(f"Tried to mutate '{var}' from '{type(scope[points[0]])}' to {type(value)}.")
        scope[points[0]] = value

    def get(self, var: str) -> Any:
        points = var.split('.')
        if points[0] in self.variables:
            scope = self.variables
            for point in points:
                if point not in scope:
                    raise Ember(f"Variable '{var}' not found.")
                scope = scope[point]
            return scope
        if self.parent:
            return self.parent.get(var)
        raise Ember(f"Variable '{var}' not found.")

    def call(self, func: str, *args):
        toCall = self.get(func)
        if not callable(toCall):
            raise Ember(f"Function '{func}' is not callable.")
        return toCall(*args)


class Ember(Exception):
    """
    Raised when TorchBox encounters an unrecoverable error.
    Remember: where there's smoke, there's fire.
    """
    pass
