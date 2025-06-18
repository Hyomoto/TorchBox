from typing import Any, Dict, Optional
from serializer import Serializer, serialize, deserialize

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

class CrucibleValueNotFound(CrucibleError):
    """Raised when a variable is not found in the crucible."""
    def __init__(self, var: str):
        super().__init__(f"Variable '{var}' not found in the crucible.")

class CrucibleWriteError(CrucibleError):
    """Raised when a write operation fails."""
    def __init__(self, var: str, message: str):
        super().__init__(f"Cannot write '{var}': {message}")

class CrucibleWriteErrorShadowing(CrucibleWriteError):
    """Raised when a write operation cannot shadow an existing variable."""
    def __init__(self, var: str):
        super().__init__(var, "shadowing is not allowed in this scope.")

class CrucibleWriteErrorProtected(CrucibleWriteError):
    """Raised when a write operation is attempted on a protected variable."""
    def __init__(self, var: str, is_type: str, violation: str):
        super().__init__(var, f"variable is {is_type} and cannot be mutated to {violation}.")

class CrucibleWriteErrorReadOnly(CrucibleWriteError):
    """Raised when a write operation is attempted on a read-only scope."""
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

    def __contains__(self, var: str):
        try:
            self.get(var)
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

    def __getitem__(self, var: str):
        return self.get(var)

    def __setitem__(self, var: str, value):
        self.set(var, value)

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

    def set(self, var: str, value):
        def write(var, key, value):
            if isinstance(var, dict):
                var[key] = value
            elif isinstance(var, list):
                var[int(key)] = value
            else:
                setattr(var, key, value)

        def read(var, key):
            if isinstance(var, dict):
                return var[key]
            elif isinstance(var, list):
                return var[int(key)]
            return getattr(var, key)

        def write_to_self(var, value):
            points = var.split('.')
            scope = self.variables
            if points[0] in self.constants:
                raise CrucibleWriteError(var, "variable is a constant.")
            while len(points) > 1:
                if points[0] not in scope:
                    if self.access & CrucibleAccess.READ_ONLY or self.access & CrucibleAccess.PROTECTED:
                        break # break error to outer scope
                    write(scope, points[0], {})
                scope = read(scope, points[0])
                points.pop(0)
            if self.access & READ_ONLY:
                raise CrucibleWriteErrorReadOnly(var)
            if self.access & PROTECTED:
                if points[0] in scope:
                    if not isinstance(value, type(scope[points[0]])):
                        raise CrucibleWriteErrorProtected(var, type(scope[points[0]]), type(value))
                else:
                    raise CrucibleWriteError(var, "scope is protected.")
            write(scope, points[0], value)

        def write_to_base(var, value):
            if not self.parent:
                raise CrucibleWriteError(var, "no parent scope available.")
            self.parent.set(var, value)

        def is_shadowing(var):
            scope = self.parent
            key = var.split('.')[0]
            while scope:
                if key in scope.variables:
                    return True
                scope = scope.parent
            return False

        try:
            if not self.access & WRITE_TO_BASE:
                raise CrucibleWriteError(var, "scope does not allow writing to base.")
            write_to_base(var, value)
        except CrucibleError:
            if self.access & NO_SHADOWING and is_shadowing(var):
                try:
                    write_to_base(var, value)
                except CrucibleError:
                    raise CrucibleWriteErrorShadowing(var)
            else:
                write_to_self(var, value)


    def get(self, var: str) -> Any:
        def read(var, key):
            if isinstance(var, dict):
                return var[key]
            elif isinstance(var, list):
                return var[int(key)]
            return getattr(var, key)

        def read_from_self(var):
            points = var.split('.')
            scope = self.variables
            for point in points:
                if point not in scope:
                    raise CrucibleValueNotFound(var)
                scope = read(scope, point)
            return scope

        def read_from_base(var):
            if self.parent:
                return self.parent.get(var)
            raise CrucibleValueNotFound(var)

        if self.access & CrucibleAccess.READ_FROM_BASE:
            try:
                return read_from_base(var)
            except CrucibleError:
                return read_from_self(var)
        else:
            try:
                return read_from_self(var)
            except CrucibleError:
                return read_from_base(var)

    def call(self, func: str, *args):
        toCall = self.get(func)
        if not callable(toCall):
            raise CrucibleError(f"Function '{func}' is not callable.")
        return toCall(*args)
