from constants import Crucible
import bcrypt

class RealmError(Exception):
    """Base class for all realm-related exceptions."""
    pass

class User:
    def __init__(self, username: str, salt: bytes, hashed_password: bytes, data: {}):
        self.username = username
        self.salt = salt
        self.hashed_password = hashed_password
        self.nickname = None  # Optional nickname for the user
        self.data = data # Additional user data

    def checkPassword(self, password: str) -> bool:
        """Check if the provided password matches the stored hashed password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password)

    def __repr__(self):
        return f"User({self.username})" + f"[{self.nickname}]" if self.nickname else ""

    def __str__(self):
        return self.nickname if self.nickname else self.username

class Realm:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.users = set()  # Set of users in the realm
        self.data = Crucible(protected=True)  # Protected Crucible for realm data

    def addUser(self, user: User):
        """Add a user to the realm with a hashed password."""
        if not isinstance(user, User):
            raise RealmError("Only User instances can be added to the realm.")
        if any(u.username == user.username for u in self.users):
            raise RealmError(f"User '{user.username}' already exists in the realm.")
        self.users.add(user)

    def __repr__(self):
        return f"Realm(name={self.name}, description={self.description})"

    def __str__(self):
        return f"{self.name}: {self.description}"