from typing import Set
from tinder.crucible import Crucible, CrucibleAccess
import bcrypt

class RealmError(Exception):
    """Base class for all realm-related exceptions."""
    pass

class User:
    def __init__(self, username: str, password: str, data: dict = None):
        self.username = username
        self.salt = bcrypt.gensalt()  # Generate a new salt for the user
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), self.salt)  # Hash the password with the salt
        print(data)
        self.data = data or { "nickname": username } # Additional user data
        print(self.data)

    def update(self, data: dict):
        """Update the user's data with a dictionary."""
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary.")
        self.data.update(data)
        return self

    def setPassword(self, password: str):
        """Set a new password for the user, hashing it with the stored salt."""
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), self.salt)
        return self

    def checkPassword(self, password: str) -> bool:
        """Check if the provided password matches the stored hashed password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password)
    
    def setNickname(self, nickname: str):
        """Set a nickname for the user."""
        self.nickname = nickname
        return self

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

    def __contains__(self, username: str) -> bool:
        """Check if a user exists in the realm by username."""
        return any(user.username == username for user in self.users)

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

    def __repr__(self):
        return f"Realm(name={self.name}, description={self.description})"

    def __str__(self):
        return f"{self.name}: {self.description}"