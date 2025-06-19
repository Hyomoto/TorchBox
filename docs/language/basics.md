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

**Else Statements** are a special form of statement that begins with `else`.  These can be used to chain statement checks.

```tinder
jump to foo if a > 0
else jump to baz if a < 0
```

!> Use of `else` will check if the *last* evaluated condition was false and, if so, run this line.  Much like the return keyword, this is not the same as a normal else because there is no block evaluation.  Thus this is typically meant to be used *immediately* following a failed condition.


A typical script:

```tinder
import login
  set USER to login.find_user(input)
  call exit({LOGIN: "no_user"}) if not USER

# get_password
  input try
  set SUCCESS to login.check_password(USER, INPUT)

  call exit({LOGIN: "success"}) if SUCCESS
  jump fail if tries is 0
  set try to retry
  dec tries
  jump to get_password

# fail
  call exit({LOGIN: "wrong_password"})
```

!> **Tinder is unstructured and blockless:** All logic is explicit, using jumps and labels—no indentation or braces. This design is inspired by event-driven or scripting DSLs (like Yarn or assembly), favoring explicit, deterministic flow over traditional blocks.

---

## Statements

A **statement** is a single instruction keyword followed by a expression pattern and optionally a condition.

**Format:**

```
keyword expression (condition)
```

* **keyword:** Action to perform (`set`, `call`, etc.)
* **expression:** Data or calculation (varies by keyword)
* **condition:** (Optional) `if <expression>`. If omitted, statement always executes (as if `if True`).

Example:

```tinder
set points to points + 10 if success
```

Statements may be made conditional (see [Conditions](#conditions)).

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
