from typing import Any, Dict, Optional

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

class CrucibleSuccess(CrucibleError):
    """Flags a successful write operation."""

class Crucible:
    parent: Optional["Crucible"]
    variables: Dict[str, Any]
    def __init__(self, access: int = 0, parent: Optional["Crucible"] = None):
        self.variables = {}
        self.parent = parent
        self.access = access

    def __contains__(self, var: str):
        scope = self.variables
        for var in var.split("."):
            if var not in self.variables:
                return False
            scope = scope[var]
        return True

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

    def update(self, source: Dict[str, Any]):
        """Update the crucible with a dictionary of variables."""
        self.variables.update(source)
        return self
    
    def set(self, var: str, value):
        def write_to_self(var, value):
            points = var.split('.')
            scope = self.variables
            while len(points) > 1:
                if points[0] not in scope:
                    if self.access & CrucibleAccess.READ_ONLY or self.access & CrucibleAccess.PROTECTED:
                        break # break error to outer scope
                    scope[points[0]] = {}
                scope = scope[points[0]]
                points.pop(0)
            if self.access & READ_ONLY:
                raise CrucibleError(f"Cannot write '{var}': scope is read-only.")
            if self.access & PROTECTED:
                if points[0] in scope:
                    if not isinstance(value, type(scope[points[0]])):
                        raise CrucibleError(f"Cannot mutate '{var}': type {type(scope[points[0]])} → {type(value)} is invalid.")
                else:
                    raise CrucibleError(f"Cannot write '{var}': scope is protected.")
            scope[points[0]] = value
            
        def write_to_base(var, value):
            if not self.parent:
                raise CrucibleError(f"Cannot write '{var}': no parent scope available.")
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
                raise CrucibleError(f"Cannot write '{var}': scope is write-only to base.")
            write_to_base(var, value)
        except CrucibleError:
            if self.access & NO_SHADOWING and is_shadowing(var):
                try:
                    write_to_base(var, value)
                except CrucibleError:
                    raise CrucibleError(f"Cannot shadow variable '{var}': no shadowing allowed in this scope.")
            else:
                write_to_self(var, value)


    def get(self, var: str) -> Any:
        def read_from_self(var):
            points = var.split('.')
            scope = self.variables
            for point in points:
                if point not in scope:
                    raise CrucibleError(f"Variable '{var}' not found.")
                scope = scope[point]
            return scope
        
        def read_from_base(var):
            if self.parent:
                return self.parent.get(var)
            raise CrucibleError(f"Variable '{var}' not found in base scope.")
        
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
