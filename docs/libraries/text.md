# Library: text
---

_No description provided._
## `column(text, width, separator)`

> Take a list of strings and combines them, separated by the given width and separator.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `List[str]` |  |
| width | `int` |  |
| separator | `str` | "" |

#### **Returns:**

*- str: The formatted string with columns.*



## `find(text, substring, start, end)`

> Find the first occurrence of a substring in a string.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |
| substring | `str` |  |
| start | `int` | 0 |
| end | `int` | -1, meaning until the end |

#### **Returns:**

_None_



## `join(items, separator)`

> Join a list of items into a single string with the specified separator.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| items | `list` |  |
| separator | `str` | "" |

#### **Returns:**

*- str: The joined string.*



## `lower(text)`

> Convert a string to lowercase.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |

#### **Returns:**

*- str: The lowercase string.*



## `pad(text, width, side)`

> Pad a string to the specified width with spaces.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |
| width | `int` |  |
| side | `str` | 'left' |

#### **Returns:**

*- str: The padded string.*



## `proper(text)`

> Capitalize the first letter of a string.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |

#### **Returns:**

*- str: The capitalized string.*



## `replace(text, old, new)`

> Replace occurrences of a substring in a string with another substring.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |
| old | `str` |  |
| new | `str` |  |

#### **Returns:**

*- str: The modified string.*



## `split(text, separator)`

> Split a string into a list of items using the specified separator.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |
| separator | `str` | None, splits on whitespace |

#### **Returns:**

*- list: The list of items.*



## `strip(text)`

> Remove leading and trailing whitespace from a string.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |

#### **Returns:**

*- str: The stripped string.*



## `title(text)`

> Convert a string to title case.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |

#### **Returns:**

*- str: The title-cased string.*



## `upper(text)`

> Convert a string to uppercase.


#### **Parameters:**

| Name | Type | Default |
| ---- | ---- | ------- |
| text | `str` |  |

#### **Returns:**

*- str: The uppercase string.*




---
