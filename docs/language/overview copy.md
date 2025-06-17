<div style="display: flex; align-items: center">
<img src="tinder.svg" alt="drawing" width="64"/>
<font size="7">Language</font>
</div>

## Introduction

Tinder is a minimalist scripting language builder designed for deterministic, extensible logic.  It is entirely unopinionated about how the engine it is implemented in works, and operates directly on a 'Crucible'.  This generally means interactions with the engine generally come in the form of reading the changes to the crucible, though certain features are implemented via exceptions that can be caught to pass messages to the engine.

It is a small, declarative language optimized for ease of parsing text data, making it useful especially for writing interactive fiction or similar text-based applications.  The language is also defined entirely in a PEG-based syntax,
meaning it is possible to change or update the language relatively easily.

### Highlights:

- PEG-based syntax with a compact, extensible instruction set ("kindlings") for assignment, flow control, arithmetic, branching, I/O, and macros.
- Seamless integration with arbitrary application state via the `Crucible` class, supporting protected, global, and local scopes.  
- Syntactic sugar for common operations, including operator aliases, conditional statements, and array/list manipulation.

## Basic Syntax and Structure

- A script is one more more lines, with each line being interpreted as a single command.  Empty lines are ignored.
- A valid line must be one of:
  - **Directives** (e.g., import text, catch "a" to b)
  - **Statement** (e.g., `set VAR 5`, `call foo()`)  
  - **Labels** (jump targets) prefixed with `#` (e.g., `# loop_start`)  
  - **Comments** starting with `//`

## Top-Level Directives

Directives are non-conditional statements.

### Imports

Loads the specified API into the local scope.  If as is specified, it will be loaded into that value instead. See the various APIs for more information.  The APIs are used to include specialty actions and could be seen as a type of plugin.  Using from allows you to selective import parts of the API.

```
import api (as name)
from api import a, b, c
```

!> Using from will import the items directly into the local scope without any namespacing.

### Catch

It is possible to handle exceptions directly in Tinder scripts using catch.  Once declared, any matching exception will cause a jump to the specified line.  Interrupts can be redeclared while the script is running.

```
catch "Exception" at line_label
```

### Constants

Declaring a constant creates a read-only variable.

```
const variable = 10
```

?> Tinder constants will be fully resolved at compile time if able.  Because complex operations can be costly, using const is a useful way to reduce script execution complexity.

### Goto labels

These line labels are used as jump targets and can optionally serve as a conditional jump.  If a conditional jump is provided, it will be taken if this line is reached by any means other than a jump.

```
# this (else that)
```

?> The else form is a convenience to avoid having to put jumps before each branch.  If code execution reaches a jump by a means other than jumping to it, the else branch is taken.

## Statements

All statements begin with a keyword and optionally may include a condition.
```
Keyword Expression (Condition)
```

!> There are no block scopes or structured blocks—Tinder is unstructured and flat.  

### Write

Append the string to the indicated variable along with a newline character.  It is essentially sugar for `set a to a + text + "\n"`.  Additionally, if the entire statement is a string (and no keyword) then it will be implictly treated as a write.

```
write "Hello World!" to output

"Hello World!"
```

### Call

Calls a function.  While functions do not require the call keyword to be used *in* expressions, if the entire expression is a function call, call must be used.

```
call foo()
```

### Set

Used to mutate the crucible.

```
set value to 10
```

?> The use of to is optional.

### Inc

Sugar for `set x to x + 1`

```
inc value (expression)
```

?> If an expression is provided, it will be used instead of the normal 1.

### Dec

Sugar for `set x to x - 1`

```
dec value (expression)
```

?> If an expression is provided, it will be used instead of the normal 1.

### Yield

Yield halts the execution of the script by raising Yielded, along with the line number of the last execution.

```
yield
```

### Stop

Stop halts the execution of the script, but does not capture the line.

```
stop
```

### Input

Input is sugar for `set x to "text"` followed by `yield`.  It will write the string to the specified variable and then halt execution of the script.

```
input "Enter Command:" to value
```

### Jump

Handles control flow by changing the next line to be executed.  In short, it jumps execution to the specified line.

```
jump to end
```

?> While line labels are the intended use, numbers can also be used as a jump target.

### Return

When a jump takes place, the last line is remembered.  Calling return will return execution to the last line that triggered a jump.

```
# above
return
jump to above
```

?> In this example, it would normally be an infinite loop, except after jumping to above, return is reached returning execution to the jump line and then incrementing.

## Expressions

An expression could be as simple as a function call or a complex series of math problems.

- Support arithmetic, comparison (`==`, `!=`, `<`, `>`, `<=`, `>=`), boolean logic (`and`, `or`, `not`), and membership (`in`, `at`, `from`).  
- Expressions can include nested function calls and sub-operations.  
- String interpolation is supported using `[[VARNAME]]` syntax at runtime.  
- Operator aliases like `plus`, `minus`, `times`, `div`, `mod`, `is`, and `is not` provide readable alternatives.  
- Conditions may be attached inline to any command (e.g., `jump end if USER == True`).  
- Membership operators:  
  - `in` returns the matched item if present.  
  - `at` returns the position or key if the item is present.  
  - `from` returns the value at the index or key.

## Data Types and Structures

- **Constants:** `True`, `False`  
- **Strings:** Quoted with single `'` or double `"` quotes, supporting interpolation.  
- **Numbers:** Integers and decimals.  
- **Arrays:** Ordered lists using square brackets, e.g., `[1, 2, 3]`.  
- **Tables:** Dictionary structures using curly braces, e.g., `{key1: value1, key2: value2}`.  
- **Batch:** Sugar for creating tables used in input matching, e.g., `<"f.ight", "run">` produces a dictionary mapping prefixes and full words for quick validation.

## Gotchas and Notes

- Tinder is **unstructured**; there are no block scopes or nested blocks. All control flow is explicit via jumps and labels.  
- `Batch` sugar lets you break up words with periods (`.`), mapping prefixes to full words, useful for input validation.  
- `const` declarations create immutable constants.  
- Accessors: dot notation (e.g., `table.key`) works for dictionary structures.  
- `in`, `from`, and `at` operators are used for accessing and testing membership in arrays and tables.  
- Remember that `in` returns the left value if present in the right; `at` returns the position or key; `from` returns the value at that key or index.
