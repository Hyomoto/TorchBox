from typing import List, Dict, Tuple, Optional, Any
from abc import ABC, abstractmethod
from mixins.permissions import PermissionRequirer
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

def static_eval_safe (fn):
    """
    Marks a function as safe for static (compile-time) evaluation.

    This decorator signals to the compiler resolver that the function
    can be *safely* evaluated during compilation if desired, because it
    has no side effects and produces deterministic output for the same inputs.
    
    Note:
        - The resolver uses this as a hint to optimize code by folding
          function calls into constant values when possible.
        - Marking a function with this does not guarantee it will be
          resolved at compile time, only that it is safe to try.
        - Functions that cause side effects or rely on runtime state
          should not be marked as static_eval_safe.
    """
    fn._resolvable = True
    return fn

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