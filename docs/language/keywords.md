## Directive Keywords

**Directives** configure the script, import libraries, define constants, or set up error handling. Directives always execute when encountered and cannot be conditional.

---

### Importing Libraries

#### `import`

Imports a library and makes its functions, constants, and utilities available under a name in your script.

```tinder
import math
import text as txt
```

* Use `as` to import the library under a custom name.
* Access imported contents using dot notation: `math.sqrt(16)`

---

#### `from`

Imports specific symbols from a library directly into your script’s namespace, so you can use them without a prefix.

```tinder
from math import sqrt, pow
sqrt(25)
```

* Only the listed functions/values are imported.
* Good for when you only need a few symbols from a large library.

---

### Constants

#### `const`

Defines a constant variable. Constants cannot be reassigned after their initial value.

```tinder
const MAX_TRIES = 5
```

* Assigning a new value to a constant raises an error.

---

### Error Handling

#### `catch`

Defines a handler for a specific exception, so your script can recover or branch to a label if an error occurs.

```tinder
catch "CrucibleValueNotFound" at handle_missing
```

## Control Flow with Labels and Blocks

#### Basic Labels

Labels mark jump targets. Use `#label` to anchor a spot in your script for use with `jump`.

```tinder
#retry
#end
```

---

#### Or Labels

Labels can include `or` to specify where to jump if the label is reached by falling through, not via `jump`.

```tinder
#end or retry
```

* If reached by fallthrough, execution jumps to `retry` instead.
* Syntactic sugar for:

```tinder
jump retry
#end
```

---

#### For Blocks

Tinder supports structured for-loops in two forms: traditional C-style and simplified “while-style.”

**C-style For Loop:**
Initializes, checks a condition, then executes a step each iteration.

```tinder
for i = 0; i < 5; inc i
  debug(i)
endfor
```

* **Initialization** (`i = 0`): Sets up the loop variable, runs once at the start.
* **Condition** (`i < 5`): Checked before every iteration.
* **Step** (`inc i`): Runs after each iteration.

**While-Style For Loop:**
Acts like a `while` loop; only a condition is required. Any initialization or updates must be written inside the block.

```tinder
for i < 10
  debug(i)
  inc i
endfor
```

* **Condition** (`i < 10`): Checked before every iteration.
* **Initialization and updates** must be done inside the block.

?> Use C-style form for loops with a clear start, stop, and step.
Use while-style for simpler cases, or when you want manual control of variable updates.

---

#### Foreach Blocks

Iterates over arrays or tables, assigning variables to values or key/value pairs.

* **Single variable:** Iterate values.

  ```tinder
  foreach item in ITEMS
    debug(item)
  endfor
  ```

* **Two variables:** For arrays, iterates index and value. For tables, key and value.

  ```tinder
  foreach i, x in ITEMS
    debug(i)
    debug(x)
  endfor
  ```

?> Use a single variable if you only care about the value. Add a second variable if you need the index (arrays) or key (tables).

#### break and continue

Inside a `for`, `foreach`, or `while-style` loop, use `break` to exit the current loop immediately, or `continue` to skip to the next iteration.

```tinder
for i < 10
  if should_stop(i)
    break
  endif
  if should_skip(i)
    continue
  endif
  debug(i)
endfor
```

* Both support conditions:
  `break if error`, `continue if x < 5`

?> Note:
break and continue always affect the innermost loop (the closest for, foreach, or while-style block). This matches behavior in most languages.

If you need to exit multiple levels (for example, breaking out of an outer loop from deep inside), use jump to a label after the desired loop. Be careful: jumping out of a loop block skips automatic iterator cleanup, which could cause unexpected results if not managed deliberately.

## Statement Keywords

Statements do the work in Tinder: variable assignment, mutation, control flow, input/output, and calling libraries.

Statements can be single lines, or part of blocks (`if ... endif`, `for ... endfor`, `foreach ... endfor`). Most support a trailing `if <expression>` for conditional execution.

---

### Conditional Blocks

```tinder
if condition
  write "Condition met"
else if other_condition
  write "Other branch"
else
  write "Fallback branch"
endif
```

* `if` starts a block. Optionally chain `else if` and `else`.
* End every conditional block with `endif`.
* Only the first branch with a true condition is executed.

---

### Assignment & Mutation

#### `set`

Assigns values to one or more variables. The assignment mode is determined by the presence of `to`, `from`, or omission of both.

---

**Basic Assignment:**

```tinder
set a, b          `` Sets both a and b to None
```

---

**Direct Assignment (with `to`):**

```tinder
set a, b to 10, 15   `` a = 10, b = 15
set x, y, z to 5, 10 `` x = 5, y = 10, z = 10 (last value repeats)
set foo, bar to 42   `` foo = 42, bar = 42
```

* If there are more variables than values, the last value is repeated.
* If there are more values than variables, extra values are ignored.

---

**Unpacking from Lists or Tables (with `from`):**

```tinder
set a, b from [0, 1]       `` a = 0, b = 1
set k, v from {k: 7, v: 9} `` k = 7, v = 9
set x, y, z from [1]       `` x = 1, y = None, z = None
set a, b from {a: 2}       `` a = 2, b = None
```

* When unpacking, values are assigned left-to-right.
* Fewer values than variables: remaining variables are set to `None`.
* Fewer variables than values: only as many values as variables are assigned.
* For tables: keys must match variable names to assign values; unmatched variables get `None`.

---

?> **Tip:**
The `from` form is especially useful for unpacking lists or dicts (such as arguments or configuration) when scripts are initialized by the engine.

#### `inc` / `dec`

Increments or decrements a variable by 1 or a specified amount.

```tinder
inc score
dec lives 3
```

#### `put`

Inserts an item before or after a list.

```tinder
put "this" before list
put "that" after list
```

#### `swap`

Swaps values between two variables.

```tinder
swap a, b
```

---

### Input and Output

#### `write`

Outputs text to the default output or a variable.

```tinder
write "Hello, world!" to output
```

?> If a line starts with a string, `write` is implied:

```tinder
"Welcome!"  `` Implicit write to default output
```

#### `input`

Prompts for user input, stores the result, and yields.

```tinder
input "Enter name:" to username
```

---

### Function Calls

#### `call`

Calls a function from a library or variable.

```tinder
call login.find_user(input)
call battle.start()
```

?> If the line contains only a function call, `call` is implied:

```tinder
login.find_user(input)
```

---

### Control Flow

#### `jump`

Transfers execution to a label or line number.

```tinder
jump to retry
jump end if done
```

?> You can use indirect expressions as jump targets for dynamic flow.

#### `return`

Resumes execution at the line after the last jump.

```tinder
return
```

#### `yield`

Pauses execution, optionally returning a value to the engine.

```tinder
yield
yield "Waiting for input"
```

#### `stop`

Ends execution immediately.

```tinder
stop
```

---

!> **Note:**
Most statement keywords support trailing `if <expression>` for conditional execution.
See [Conditions](language/basics.md#conditions) for details.