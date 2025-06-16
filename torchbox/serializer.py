from typing import Any, Callable, Dict, Optional

class DeserializationError(Exception):
    """Raised when deserialization fails."""
    pass

def serialize(item: Any):
    if item is None:
        return { "type": "NoneType", "value": None }
    elif isinstance(item, Serializer):
        return { "type": item.__class__.__name__, "value": item.serialize() }
    elif isinstance(item, dict):
        return { "type" : "dict", "value" : {key: serialize(value) for key, value in item.items()}}
    elif isinstance(item, list):
        return { "type" : "list", "value" : [serialize(item) for item in item] }
    elif isinstance(item, tuple):
        return { "type" : "tuple", "value" : [serialize(item) for item in item] }
    elif isinstance(item, (int, float, str, bool)):
        return { "type": type(item).__name__, "value": item }
    else:
        raise TypeError(f"Cannot serialize item of type {type(item).__name__}.")

def deserialize(data: Dict[str, Any], classes: Optional[Dict[str, Callable]] = None) -> Any:
    t = data.get("type")
    v = data.get("value")
    match t:
        case "NoneType":
            return None
        case "dict":
            return {key: deserialize(value, classes) for key, value in v.items()}
        case "list":
            return [deserialize(item, classes) for item in v]
        case "tuple":
            return tuple(deserialize(item, classes) for item in v)
        case "int" :
            return int(v)
        case "float":
            return float(v)
        case "str":
            return str(v)
        case "bool":
            return bool(v)
        case _:
            if classes and t in classes:
                cls = classes[t]
                if issubclass(cls, Serializer):
                    return cls.deserialize(v, classes)
                else:
                    raise DeserializationError(f"Class {t} does not have a deserialize method.")
            raise DeserializationError(f"Unknown type '{t}' in serialized data.")

class Serializer:
    def serialize(self) -> Dict[str, Any]:
        """Serialize this class to dictionary representation."""
        pass

    @classmethod
    def deserialize(cls, data: Dict[str, Any], classes: Optional[Dict[str, Any]] = None) -> "Serializer":
        """Deserialize some data to this class."""
        pass