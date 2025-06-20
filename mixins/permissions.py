from typing import Optional, List

class PermissionHolder:
    """An mixin for objects that have permissions."""
    def __init__(self, permissions: Optional[List[str]] = None, **kwargs):
        self.permissions = permissions or []
        super().__init__(**kwargs)

class PermissionRequirer:
    """An mixin for objects that require permissions."""
    def __init__(self, permissions: Optional[List[str]] = None, **kwargs):
        self.permissions = permissions or []
        super().__init__(**kwargs)

    def hasPermission(self, check: object) -> bool:
        """Check if the required permissions are present in the given holder."""
        if not self.permissions:
            return True
        if not isinstance(check, PermissionHolder):
            return False
        return all(perm in check.permissions for perm in self.permissions)
