from typing import Any, Union, Dict, List, Sequence, Optional
from mixins.serializer import Serializer, serialize, deserialize

class CrucibleAccess:
    READ_FROM_BASE = 0x01
    WRITE_TO_BASE = 0x02
    READ_ONLY = 0x04
    PROTECTED = 0x08
    NO_SHADOWING = 0x10

READ_FROM_BASE = CrucibleAccess.READ_FROM_BASE
WRITE_TO_BASE = CrucibleAccess.WRITE_TO_BASE
READ_ONLY = CrucibleAccess.READ_ONLY
PROTECTED = CrucibleAccess.PROTECTED
NO_SHADOWING = CrucibleAccess.NO_SHADOWING

class CrucibleError(Exception):
    """Base class for all Crucible-related exceptions."""
    pass

class CrucibleKeyNotFound(CrucibleError):
    """
    Raised when a key is not found in the crucible.
    Key 'key' not found at 'path'.
    """
    def __init__(self, key: str | int, path: str):
        super().__init__(f"{'Key' if isinstance(key, str) else 'Index'} '{key}' not found at '{path}' in the crucible.")

class CrucibleValueNotFound(CrucibleError):
    """
    Raised when a variable is not found in the crucible.
    Variable 'var' not found in the crucible.
    """
    def __init__(self, var: str | int):
        super().__init__(f"Variable '{var}' not found in the crucible.")

class CrucibleWriteError(CrucibleError):
    """Raised when a write operation fails.
    Cannot write 'var': message
    """
    def __init__(self, var: str | int, message: str):
        super().__init__(f"Cannot write '{var}': {message}")

class CrucibleWriteErrorShadowing(CrucibleWriteError):
    """
    Raised when a write operation cannot shadow an existing variable.
    Shadowing is not allowed in this scope.
    """
    def __init__(self, var: str | int):
        super().__init__(var, "shadowing is not allowed in this scope.")

class CrucibleWriteErrorProtected(CrucibleWriteError):
    """
    Raised when a write operation is attempted on a protected variable.
    Variable 'var' is protected and cannot be mutated to 'violation'.
    """
    def __init__(self, var: str | int, is_type: str, violation: str):
        super().__init__(var, f"variable is {is_type} and cannot be mutated to {violation}.")

class CrucibleWriteErrorReadOnly(CrucibleWriteError):
    """
    Raised when a write operation is attempted on a read-only scope.
    Scope is read-only and cannot be written to.
    """
    def __init__(self, var: str):
        super().__init__(var, "scope is read-only and cannot be written to.")

class Crucible(Serializer):
    parent: Optional["Crucible"]
    variables: Dict[str, Any]
    def __init__(self, access: int = 0, parent: Optional["Crucible"] = None):
        self.variables = {}
        self.parent = parent
        self.access = access
        self.constants = []
        super().__init__()

    def _walk_path(self, path: Sequence[str | int]):
        walk = 0
        try:
            scope = self
            for point in path:
                scope = scope[point] # type: ignore
                walk += 1
        except Exception:
            walked = '.'.join([str(v) for v in path[:walk]] or ['root'])
            raise CrucibleKeyNotFound(path[walk], walked)
        return scope

    def __contains__(self, path: List[str | int]):
        try:
            self._walk_path(path)
            return True
        except CrucibleError:
            return False

    def __repr__(self):
        flags = ""
        if self.access & CrucibleAccess.READ_FROM_BASE:
            flags += "RFB "
        if self.access & CrucibleAccess.WRITE_TO_BASE:
            flags += "WTB "
        if self.access & CrucibleAccess.READ_ONLY:
            flags += "RO "
        if self.access & CrucibleAccess.PROTECTED:
            flags += "PT "
        if self.access & CrucibleAccess.NO_SHADOWING:
            flags += "NS "
        flags = flags.strip()
        return f"Crucible[{flags}]({self.variables})"

    def __getitem__(self, key: str):
        return self.variables[key]

    def __setitem__(self, key: str, value):
        self.variables[key] = value

    def serialize(self) -> Dict[str, Any]:
        """Serialize the crucible to a dictionary representation."""
        return {
            "access": self.access,
            "variables": serialize(self.variables)
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any], classes: Optional[Dict[str, Any]] = None) -> "Crucible":
        """Deserialize the crucible from a dictionary representation."""
        crucible = cls(data["access"])
        crucible.variables = deserialize(data["variables"], classes)
        return crucible

    def update(self, source: Dict[str, Any], constants: Optional[list] = None):
        """Update the crucible with a dictionary of variables."""
        self.variables.update(source)
        if constants:
            self.constants.extend(constants)
        return self

    def set(self, path: Sequence[str | int], value):
        def write_to_self(var, value):
            key = path[-1]
            if key in self.constants:
                raise CrucibleWriteError(var, "variable is constant and cannot be mutated.")
            scope = self._walk_path(path[:-1])
            protected = self.access & PROTECTED
            if self.access & READ_ONLY:
                raise CrucibleWriteErrorReadOnly(var)
            if isinstance(scope, list):
                if not isinstance(key, int):
                    raise CrucibleKeyNotFound(key,'.'.join([str(v) for v in path[:-1]]))
                if key < 0 or key >= len(scope):
                    raise CrucibleError(f"Index '{key}' out of range for list.")
                if protected and not isinstance(value, type(scope[key])):
                    raise CrucibleWriteErrorProtected('.'.join([str(v) for v in path]), type(scope[key]), type(value))
                scope[key] = value
            elif isinstance(scope, dict):
                if protected:
                    if key not in scope:
                        raise CrucibleWriteError('.'.join([str(v) for v in path]), "scope is protected.")
                    if not isinstance(value, type(scope[key])):
                        raise CrucibleWriteErrorProtected('.'.join([str(v) for v in path]), type(scope[key]), type(value))
                scope[key] = value
            else:
                raise CrucibleError(f"Cannot write to '{'.'.join([str(v) for v in path])}': scope is not a list or dictionary.")

        def write_to_base(path, value):
            if not self.parent:
                raise CrucibleWriteError(path[0], "no parent scope available.")
            self.parent.set(path, value)
        
        def is_shadowing(key: str | int):
            scope = self.parent
            while scope:
                if key in scope.variables:
                    return True
                scope = scope.parent
            return False

        key = path[0]
        try:
            if not self.access & WRITE_TO_BASE:
                raise CrucibleWriteError(key, "scope does not allow writing to base.")
            write_to_base(path, value)
        except CrucibleError:
            if self.access & NO_SHADOWING and is_shadowing(key):
                try:
                    write_to_base(path, value)
                except CrucibleError:
                    raise CrucibleWriteErrorShadowing(key)
            else:
                write_to_self(path, value)


    def get(self, path: Sequence[str | int]) -> Any:
        def read_from_base(path):
            if self.parent:
                return self.parent.get(path)
            raise CrucibleValueNotFound(path)

        if self.access & CrucibleAccess.READ_FROM_BASE:
            try:
                return read_from_base(path)
            except CrucibleError:
                return self._walk_path(path)
        else:
            try:
                return self._walk_path(path)
            except CrucibleError:
                return read_from_base(path)
