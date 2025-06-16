# API: text
---

_No description provided._
## `column(text, width, separator)`
Take a list of strings and combines them, separated by the given width and separator.

**Parameters:**
- `text`: *List[str]*
- `width`: *int*
- `separator`: *str* (default: "")

**Returns:** *- str: The formatted string with columns.*

## `find(text, substring, start, end)`
Find the first occurrence of a substring in a string.

**Parameters:**
- `text`: *str*
- `substring`: *str*
- `start`: *int* (default: 0)
- `end`: *int* (default: -1, meaning until the end)

**Returns:** _None_
## `join(items, separator)`
Join a list of items into a single string with the specified separator.

**Parameters:**
- `items`: *list*
- `separator`: *str* (default: "")

**Returns:** *- str: The joined string.*

## `lower(text)`
Convert a string to lowercase.

**Parameters:**
- `text`: *str*

**Returns:** *- str: The lowercase string.*

## `proper(text)`
Capitalize the first letter of a string.

**Parameters:**
- `text`: *str*

**Returns:** *- str: The capitalized string.*

## `replace(text, old, new)`
Replace occurrences of a substring in a string with another substring.

**Parameters:**
- `text`: *str*
- `old`: *str*
- `new`: *str*

**Returns:** *- str: The modified string.*

## `split(text, separator)`
Split a string into a list of items using the specified separator.

**Parameters:**
- `text`: *str*
- `separator`: *str* (default: None, splits on whitespace)

**Returns:** *- list: The list of items.*

## `strip(text)`
Remove leading and trailing whitespace from a string.

**Parameters:**
- `text`: *str*

**Returns:** *- str: The stripped string.*

## `title(text)`
Convert a string to title case.

**Parameters:**
- `text`: *str*

**Returns:** *- str: The title-cased string.*

## `upper(text)`
Convert a string to uppercase.

**Parameters:**
- `text`: *str*

**Returns:** *- str: The uppercase string.*


---
