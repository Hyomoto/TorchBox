from typing import List, Dict, Optional
import random
import re

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
    xp: int
    level: int
    strength: int
    defense: int
    weapon: Item
    armor: Item
    items: Inventory
    gender: str
    profession: str
    days: int
    gold: int
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "Player")
        self.xp = 0
        self.level = 1
        self.strength = kwargs.get("strength", 1)
        self.defense = kwargs.get("defense", 1)
        self.weapon = None
        self.armor = None
        self.items = Inventory()

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
    def __init__(self, notation="6"):
        self.notation = notation.lower()
        self.rolls = []
        self.total = 0
        self._parse_notation()

    def _parse_notation(self):
        if self.notation in {"p", "perc", "percentile"}:
            self.notation = "percentile"
            self.num = 2
            self.sides = 10
            self.special = "percentile"
        else:
            pattern = re.fullmatch(r"(?:(\d*)d)?(\d+)", self.notation)
            if not pattern:
                raise ValueError(f"Invalid dice format: {self.notation}")
            self.num = int(pattern.group(1)) if pattern.group(1) else 1
            side = int(pattern.group(2))
            self.sides = side
            self.special = None

    def roll(self,modifier = 0):
        self.rolls.clear()
        if self.special == "percentile":
            units = random.randint(1, 10)
            tens = (random.randint(1, 10) - 1) * 10
            self.rolls = [units, tens]
            self.total = units + tens
        else:
            self.rolls = [random.randint(1, self.sides) for _ in range(self.num)]
            self.total = sum(self.rolls)
        return max(self.total+modifier,0)

    def format(self, pattern="Rolling %n: [%r] → Total: %t"):
        return (pattern
                .replace("%n", self.notation)
                .replace("%r", ', '.join(map(str, self.rolls)))
                .replace("%t", str(self.total)))

    def __str__(self):
        return f"{self.notation}: {self.rolls} → Total: {self.total}"

