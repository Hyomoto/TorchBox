from typing import List, Dict, Tuple, Optional, Any
import os

class Permissions:
    """Subclass this to define custom permissions."""
    def __init__(self, permissions: Optional[List[str]] = None, **kwargs):
        self.permissions = permissions or []
        super().__init__(**kwargs)
    def hasPermission(self, api: "API"):
        return api.canImport(self.permissions)
    def __contains__(self, permission: str) -> bool:
        return permission in self.permissions
    def __repr__(self):
        return f"Permissions({self.permissions})"

class API(dict):
    def __init__(self, api: Dict[str, Any], permissions: Optional[Tuple[str] | str] = None):
        super().__init__(api)
        self.update(api)
        self.permissions = [permissions] if isinstance(permissions, str) else permissions

    def canImport(self, permissions: List[str]) -> bool:
        """
        Check if the API can import a file based on its permissions and the file's path.
        If no permissions are set, it allows all imports, otherwise returns False if
        the file path does not start with any of the allowed permissions.
        """
        if not self.permissions:
            return True
        for permission in self.permissions:
            if permission in permissions:
                return True
        return False

    def __repr__(self):
        return f"API({self.permissions}): {super().__repr__()}"