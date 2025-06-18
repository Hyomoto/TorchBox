from typing import List, Dict, Tuple, Optional, Any
from abc import ABC, abstractmethod
import inspect
import sys

def import_libraries(module: str, context: object, include: List[str] = ["all"], exclude: List[str] = []):
    apis = {}
    for name, obj in inspect.getmembers(sys.modules[module], lambda x: inspect.isclass(x) and issubclass(x, Library) and not inspect.isabstract(x)):
        if name in exclude:
            continue
        if name in include or "all" in include:
            new: Library = obj(context)
            apis[new.name] = new
    return apis

def exportable(fn):
    fn._exportable = True
    return fn

def exportableAs(name: str):
    def decorator(fn):
        fn._exportable = True
        fn._export_name = name
        return fn
    return decorator

class PermissionHolder:
    """An entity that has permissions."""
    def __init__(self, permissions: Optional[List[str]] = None, **kwargs):
        self.permissions = permissions or []
        super().__init__(**kwargs)

class PermissionRequirer:
    """An entity that requires permissions."""
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

class Library(PermissionRequirer, dict, ABC):
    """Base class for APIs, providing permission management and export functionality."""
    @abstractmethod
    def __init__(self, name: str, context: object, **kwargs):
        self.name = name
        self.context = context
        super().__init__(**kwargs)

    def export(self, matches: Optional[List[str]] = None) -> Dict[str, Any]:
        """Export the API's contents as a dictionary."""
        exported = {}
        for name in dir(self):
            if name.startswith("_"):
                continue
            attr = getattr(self, name)
            class_attr = getattr(type(self), name, None)
            if callable(attr) and getattr(attr, "_exportable", False):
                export_name = getattr(attr, "_export_name", name)
                if matches and export_name not in matches:
                    continue
                exported[export_name] = attr
            # If it's a property and exportable
            elif isinstance(class_attr, property) and getattr(class_attr.fget, "_exportable", False):
                export_name = getattr(class_attr.fget, "_export_name", name)
                if matches and export_name not in matches:
                    continue
                exported[export_name] = attr
        return exported

    def __repr__(self):
        return f"API({self.permissions}): {super().__repr__()}"