## Basic Code Structure

Tinder scripts consist of one or more lines, each representing a single instruction. Each line must be one of the following: a *comment*, a *label*, a *directive*, or a *statement*. Empty lines are ignored, and whitespace outside of strings is insignificant.

A script is simply:

```
line
line
...
```

**Comments** begin with `\`\`` and extend to the end of the line. They can appear alone or after any instruction:

```tinder
\`\` this is a comment
import a \`\` another comment
```

**Labels** begin with `#` followed by an identifier, marking jump targets for control flow. Labels have several forms, including for each, for iter and an else (see [control flow](language/keywords.md#control-flow)), and otherwise act as anchors for jumps:

```tinder
# line_label
```

**Directives** begin with a keyword and are used to configure the script or import resources (see [Directives](language/keywords.md#directive-keywords) for all directives):

```tinder
import foo
```

**Statements** are the executable instructions of Tinder. They always begin with a keyword, may include an expression, and can optionally end with a condition. See [Statements](#statements) for structure.

```tinder
set a to 1
jump to line_label if a > 0
```

A typical script:

```tinder
import login
  set USER to login.find_user(input)
  call exit({LOGIN: "no_user"}) if not USER

  for tries = 0; tries < 3; inc tries
    input try
    set SUCCESS to login.check_password(USER, INPUT)

    if SUCCESS
      call exit({LOGIN: "success"})
    endif

  endfor
  call exit({LOGIN: "wrong_password"})
```

!> **Tinder supports both structured and unstructured flow:**  
You can use blocks (like `if ... endif`, `foreach ... endfor`) for structured logic, or line labels and jumps for explicit, unstructured flow. Blocks do not create new scopes; all variables are accessible anywhere in the script, depending on Crucible implementation. Use whichever control style fits your needs.

## Blocks

Tinder supports two major block constructs: **if-blocks** and **for/foreach blocks**.

### If Blocks

Conditional blocks use `if`, optionally followed by `else if`, `else`, and always ending with `endif`. Only the first matching branch will execute.

```tinder
if condition
  set result to "A"
else if other_condition
  set result to "B"
else
  set result to "C"
endif
````

You may nest if blocks as needed.

### For/Foreach Blocks

* **For:**
  Follows the form `for <init>; <condition>; <statement>` and ends with `endfor`. The `<statement>` must be a valid statement (e.g., `inc i`).
  Example:

  ```tinder
  for i = 0; i < 10; inc i
    call debug(i)
  endfor
  ```
* **Foreach:**
  Iterates over arrays or tables.

  ```tinder
  foreach item in ITEMS
    call debug(item)
  endfor

  foreach key, value in TABLE
    call debug(key)
    call debug(value)
  endfor
  ```

  For arrays: `foreach a in arr`.
  For tables: `foreach key, value in tbl`.

**Note:** Blocks do not create new scopes. All variables remain in the same Crucible/environment.

---

## Expressions

An **expression** is any value or calculation that produces a result. Expressions are used throughout Tinder—for assignment, conditions, arguments, and more.

### Expression Components

An expression can be:

* A **literal** (`10`, `"hello"`, `True`)
* An **identifier** or **variable** (`score`, `user.name`)
* A **function call** (`find_user(name)`)
* A **data structure**: array (`[1, 2, 3]`) or table (`{key: value}`)
* An **operation** or **comparison** (`a + 1`, `count > 0`)
* A **grouped expression** (`(x + y) * 2`)
* An **accessor chain** (see below)

### Accessors and Data Retrieval

Tinder supports both explicit and implicit data access:

* **Dot notation** allows chained access for tables and arrays:

  * `data.key` looks up `key` in `data` (if `data` is a table)
  * `list.0` looks up index `0` in `list` (if `list` is an array)

* **from** syntax provides explicit retrieval:

  * `x from [a, b, c]` gets the item at index `x`
  * `k from {foo: 1, bar: 2}` gets the value for key `k`
* There is no `a[0]` syntax; instead, use dot notation or `from`.

See [accessors and data retrieval](language/data_and_access.md#accessors-and-data-retrieval) for further details on data accessors.

---

### Operators

Tinder supports arithmetic, comparison, boolean, and membership operators, all with clear precedence. Operators may have readable aliases (`plus`, `is`, `less than`, etc.) and can be used wherever an expression is allowed.

See [operator precedence](language/data_and_access.md#operator-precedence) for a full operator list and precedence table.

---

### Example Expressions

```tinder
set health to health - 10
jump dead if health <= 0
set found to item in inventory
set n to my_table.3.foo
set val to key from {foo: 1, bar: 2}
```

### Indirect Expressions

An **indirect expression** uses the `@` symbol to resolve a value to a variable or label name, and then retrieve what that name points to. This allows dynamic lookup—your script can decide at runtime which variable, label, or value to use.

```tinder
jump @INPUT
jump @k from ACTIONS
```

?> **Why use indirects?**
Indirects are powerful for things like input-driven flow control, menu systems, or pattern matching. For example, you can store label names in a table, look up the next step based on user input, and jump there automatically.

```tinder
jump @INPUT from { q: "quit", n: "new_game", _ : "invalid_input" }
```

This allows flexible, data-driven scripts—where you can map inputs to actions or destinations without hard-coding every branch.

---

**In short:**
Indirects let you resolve a value *to* a variable or label name, then use what’s stored there—enabling dynamic and reusable script patterns.

---

## Conditions

A statement can be made conditional by appending `if <expression>` at the end of the line. The statement executes only if the condition is considered **truthy**.

### Truthiness

Tinder evaluates conditions using the following rules:

* **Falsey values:**

  * `""` (empty string)
  * `[]` (empty array)
  * `{}` (empty table)
  * `0` (zero)
  * `False` (constant)
  * `None` (undefined value)
* **All other values are truthy** (nonzero numbers, non-empty containers, non-empty strings, etc.).

If no condition is given, the statement always runs (implicit `if True`).

**Examples:**

```tinder
jump retry if tries > 0
call logout() if session == None
write "OK" if status
```

---

**Summary:**
Tinder’s structure is simple and flat: every line is a discrete instruction, conditions are always explicit, and data access is both flexible and consistent (with dot chains and `from`). This encourages clarity, determinism, and easy parsing—making Tinder ideal for scripting and interactive fiction engines where explicit control flow and state changes are key.
