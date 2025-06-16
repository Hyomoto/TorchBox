# API: base
---

The base API is always available and provides basic functionality for scene management, input matching,
debugging, and string manipulation.  It also provides access to ANSI color codes.

## `scene(scene, carry)`
Change the scene for the player, setting up the local environment.

**Parameters:**
- `scene`: *str*
- `carry`: *dict, optional*

**Returns:** _None_
## `color(color)`
Return the ANSI escape code for the given color.  Valid colors are: BLACK, RED, GREEN, BROWN, BLUE,
PURPLE, CYAN, YELLOW, WHITE, LIGHT_GRAY, LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE, LIGHT_PURPLE, LIGHT_CYAN, 
DARK_GRAY.

**Parameters:**
- `color`: *str*

**Returns:** _None_
## `debug(message)`
Print a debug message to the console.

**Parameters:**
- `message`: *str*

**Returns:** _None_
## `enter(scene, carry)`
Push a new scene onto the stack, can be returned to using exit.

**Parameters:**
- `scene`: *str*
- `carry`: *dict, optional*

**Returns:** _None_
## `exit(carry)`
Pops the current scene off the stack, returning to the previous scene.  If there is no previous
scene, it will close the user's session.

**Parameters:**
- `carry`: *dict, optional*

**Returns:** _None_
## `len(value)`
Return the length of the given value.

**Parameters:**
- `value`: *Any*

**Returns:** *- int: The length of the value.*

## `match(input, matches, otherwise)`
Match the input against a dictionary of possible matches and returns the corresponding value, or
jumps to otherwise if no match is found. Using a <batch> will allow you to match against more
complex inputs.  See the language documentation for more details.

**Parameters:**
- `input`: *str*
- `matches`: *dict*
- `otherwise`: *str | int, optional*

**Returns:** _None_
## `st(args)`
Concatenate multiple values into a single string.

**Parameters:**
- `args`: *Any*

**Returns:** *- str: The concatenated string.*


---
