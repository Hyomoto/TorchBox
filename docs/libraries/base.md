# Library: base
---

    The base Library is always available and provides basic functionality for scene management,
    input matching, debugging, and string manipulation.  It also provides access to ANSI color codes.
    
## `batch()`

> _No description provided._



#### **Returns:**

_None_

?> This method can be pure.



## `scene(scene, carry)`

> Change the scene for the player, setting up the local environment.


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



## `gosub(scene, carry)`

> Push a new scene onto the stack, can be returned to using exit.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| scene | `str` |  |
| carry | `dict, optional` |  |

#### **Returns:**

_None_



## `endsub(carry)`

> Pops the current scene off the stack, returning to the previous scene.  If there is no previous
        scene, it will close the user's session.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| carry | `dict, optional` |  |

#### **Returns:**

_None_



## `keys()`

> _No description provided._



#### **Returns:**

_None_

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
