"""

"""
from typing import Dict, List, Tuple, Callable, Type, Any
from abc import ABC, abstractmethod
import inspect

# Firestarter compiler

class Value(ABC):
    @classmethod
    def args(cls) -> List[str]:
        """Return the argument pattern for the Value."""
        args = []
        for name, param in inspect.signature(cls.__init__).parameters.items():
            if name == "self":
                continue
            if param.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD):
                if param.default is inspect.Parameter.empty:
                    args.append(".")  # required
                else:
                    args.append("?")  # optional
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                args.append("*")  # *args
        return args

# primitive

class Primitive(Value):
    """A primitive untyped value."""
    def __init__(self, var: Any):
        self.var = self.primitive(var)

    @property
    def primitive(self) -> Type:
        """The type of the primitive value."""
        return str
