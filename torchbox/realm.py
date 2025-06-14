import os
from typing import Set, Optional
from tinder.crucible import Crucible, CrucibleAccess
import threading
import bcrypt
import json

class RealmError(Exception):
    """Base class for all realm-related exceptions."""
    pass

class User:
    def __init__(self, username: str, password: str, data: Optional[Crucible] = None):
        self.username = username
        salt = bcrypt.gensalt()  # Generate a new salt for the user
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        self.data = data

    def update(self, data: dict):
        """Update the user's data with a dictionary."""
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary.")
        self.data.update(data)
        return self

    def setPassword(self, password: str):
        """Set a new password for the user, hashing it with the stored salt."""
        salt = bcrypt.gensalt()  # Generate a new salt for the user
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return self

    def checkPassword(self, password: str) -> bool:
        """Check if the provided password matches the stored hashed password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password)
    
    def setNickname(self, nickname: str):
        """Set a nickname for the user."""
        self.nickname = nickname
        return self
    
    def serialize(self) -> dict:
        """Serialize the user to a dictionary representation."""
        return {
            "username": self.username,
            "hashed_password": self.hashed_password.decode('utf-8'),  # Convert bytes to string for serialization
            "data": self.data.serialize() if self.data else {}
        }
    
    @classmethod
    def deserialize(cls, data: dict):
        """Deserialize the user from a dictionary representation."""
        username = data.get("username")
        hashed_password = data.get("hashed_password")
        user_data = data.get("data", {})
        crucible_data = Crucible.deserialize(user_data) if user_data else None
        user = cls(username, "", crucible_data)
        user.hashed_password = hashed_password.encode('utf-8')
        return user

    def __contains__(self, key: str) -> bool:
        """Check if the user's data contains a specific key."""
        return key in self.data

    def __getitem__(self, key: str):
        """Get an item from the user's data."""
        return self.data.get(key)
    
    def __setitem__(self, key: str, value):
        """Set an item in the user's data."""
        self.data[key] = value

    def __repr__(self):
        return f"User(username={self.username}, nickname={self.data.get('nickname', '')})"

class Realm:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.users: Set[User] = set()  # Set of users in the realm
        self.data = Crucible(access=CrucibleAccess.PROTECTED)  # Protected Crucible for realm data

    def getRankings(self) -> list:
        """Retrieve a list of users sorted by their username."""
        return sorted(self.users, key=lambda user: user.username)

    def getUser(self, username: str) -> User:
        """Retrieve a user by username."""
        for user in self.users:
            if user.username == username:
                return user
        raise RealmError(f"User '{username}' not found in the realm.")

    def addUser(self, user: User):
        """Add a user to the realm with a hashed password."""
        if not isinstance(user, User):
            raise RealmError("Only User instances can be added to the realm.")
        if any(u.username == user.username for u in self.users):
            raise RealmError(f"User '{user.username}' already exists in the realm.")
        self.users.add(user)
        return user

    def removeUser(self, user: User):
        """Remove a user from the realm."""
        if not isinstance(user, User):
            raise RealmError("Only User instances can be removed from the realm.")
        if user not in self.users:
            raise RealmError(f"User '{user.username}' does not exist in the realm.")
        self.users.remove(user)

    def serialize(self) -> str:
        """Serialize the realm to a string representation."""
        return {
            "name": self.name,
            "description": self.description,
            "users": {user.username: user.serialize() for user in self.users}
        }

    @classmethod
    def deserialize(cls, data: str):
        """Deserialize the realm from a string representation."""
        realm_data = json.loads(data)
        name = realm_data.get("name")
        description = realm_data.get("description", "")
        users_data = realm_data.get("users", {})
        realm = cls(name, description)
        for user_data in users_data.values():
            user = User.deserialize(user_data)
            realm.addUser(user)
        return realm

    def save(self, to: str):
        """Save the realm to a file asynchronously."""
        def serialize_and_save():
            try:
                with open(to + ".temp", "w") as f:
                    json.dump(self.serialize(), f, indent=4)
                if os.path.exists(to):
                    if os.path.exists(to + ".bak"):
                        os.remove(to + ".bak")
                    os.rename(to, to + ".bak")
                os.rename(to + ".temp", to)
            finally:
                self._saving.release()
        self._saving = getattr(self, "_saving", threading.Lock())
        if not self._saving.acquire(blocking=False):
            raise RealmError("Realm is already being saved.")
        threading.Thread(target=serialize_and_save, daemon=False).start()

    @classmethod
    def load(cls, from_path: str):
        """Load the realm from a file."""
        with open(from_path, "r") as f:
            data = f.read()
        return cls.deserialize(data)

    def __contains__(self, username: str) -> bool:
        """Check if a user exists in the realm by username."""
        return any(user.username == username for user in self.users)

    def __repr__(self):
        return f"Realm(name={self.name}, description={self.description})"

    def __str__(self):
        return f"{self.name}: {self.description}"