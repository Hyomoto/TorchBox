# Library: base
---

The base Library is always available and provides basic functionality for scene management, input matching,
debugging, and string manipulation.  It also provides access to ANSI color codes.

## `batch(items)`

> Create a batch mapping from a list of strings, where each string is split by '.' and the parts are
concatenated to form keys.  If the key begins with a '_', it will be stripped and used as a default
argument in the map.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| items | `str` |  |

#### **Returns:**

*- dict: A dictionary mapping each concatenated key to its full string.*

?> This method can be pure.



## `scene(scene, carry)`

> Change the scene for the player.  The dictionary 'carry' will pass those keys to the new scene.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| scene | `str` |  |
| carry | `dict, optional` |  |

#### **Returns:**

_None_



## `color(color)`

> Return the ANSI escape code for the given color.  Valid colors are: BLACK, RED, GREEN, BROWN, BLUE,
PURPLE, CYAN, YELLOW, WHITE, LIGHT_GRAY, LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE, LIGHT_PURPLE, LIGHT_CYAN, 
DARK_GRAY.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| color | `str` |  |

#### **Returns:**

_None_

?> This method can be pure.



## `str(args)`

> Concatenate multiple values into a single string.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| args | `Any` |  |

#### **Returns:**

*- str: The concatenated string.*

?> This method can be pure.



## `debug(message)`

> Print a debug message to the console.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| message | `str` |  |

#### **Returns:**

_None_



## `enter(scene, carry)`

> Push a new scene onto the stack, can be returned to using exit.  This allows for nested scenes and
scene transitions.  The dictionary 'carry' will pass those keys to the new scene.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| scene | `str` |  |
| carry | `dict, optional` |  |

#### **Returns:**

_None_



## `exit(carry)`

> Pops the current scene off the stack, returning to the previous scene.  If there is no previous
scene, it will close the user's session.  This allows for scene transitions and returning to
previous scenes.  The dictionary 'carry' will pass those keys to the previous scene.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| carry | `dict, optional` |  |

#### **Returns:**

_None_



## `keys(value)`

> Return a list of keys from the given dictionary.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| value | `dict` |  |

#### **Returns:**

*- list: A list of keys from the dictionary.*

?> This method can be pure.



## `len(value)`

> Return the length of the given value.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| value | `Any` |  |

#### **Returns:**

*- int: The length of the value.*

?> This method can be pure.




---
