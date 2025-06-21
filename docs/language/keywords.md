## Directive Keywords

**Directives** are special instructions that configure your script, import tools, or define constants and error handling. They always execute when encountered and are not conditional.

---

### Importing

#### `import`

Brings an external library as a set of functions, utilities, or constants—into your script’s namespace. After importing, you access its contents using dot notation.

```tinder
import math
import text as txt
```

* Use `as` to assign a custom name.

---

#### `from`

Imports specific functions or values from an API directly into your script’s local scope. This allows you to use them without a prefix.

```tinder
from math import sqrt, pow
sqrt(25)
```

* Imported items appear as if they were defined directly in your script.

?> **Note:**
`from` is best used when you need only a few symbols from a large library.

---

### Constants

#### `const`

Declares a constant variable, which cannot be changed after its initial assignment.

```tinder
const MAX_TRIES = 5
```

* Attempting to assign a new value to a constant will raise an error.

---

### Error Handling

#### `catch`

Sets up an error handler, letting your script respond to specific exceptions by jumping to a label when an error is raised.

```tinder
catch "CrucibleValueNotFound" at handle_missing
```

* Used for graceful error recovery.

---

### Control Flow

#### Basic Labels

A **label** defines a jump target for control flow. Use `# label` to mark a point in your script that other statements (such as `jump`) can refer to.

```tinder
#retry
#end
```

?> **Tip:** Labels are the core building blocks of Tinder’s flat, explicit control flow.

---

#### Or Labels

You can define a label with an `or` clause to specify where control should go if this label is reached "naturally" (by falling through), rather than by a jump.

```tinder
#end or retry
```

* If you `jump end`, execution continues at `#end` as normal.
* If execution *falls through* to `#end`, it jumps instead to `retry`.

**Equivalent sugar:**

```tinder
jump retry
#end
```

---

#### For Blocks

Tinder supports C-style **for** loops as structured blocks, using the `for ... endfor` syntax.

**Syntax:**

```tinder
for i = 0; i < 5; inc i
  call debug(i)
endfor
```

* The first part (`i = 0`) is the initializer (must be a single assignment).
* The second part (`i < 5`) is the loop condition (checked before each iteration).
* The third part (`inc i`) is any valid statement (executed after each iteration).
* All statements inside the block will run in order until the condition fails.

**Note:**
The entire loop—including condition checks and updates—is handled automatically. You do not need to use labels for most loops, but labels remain available for advanced/manual flow.

---

#### Foreach Blocks

A **foreach** block lets you iterate over arrays or tables directly, with easy variable assignment.

**Arrays:**

```tinder
foreach item in ITEMS
  call debug(item)
endfor
```

**Tables:**

```tinder
foreach key, value in MAP
  call debug(key)
  call debug(value)
endfor
```

* In arrays, `item` is set to each element in turn.
* In tables, `key` and `value` are set to each entry in the table.

?> **Note:**
Tinder handles setup, iteration, and index/key extraction. Just provide the variables and collection—no extra boilerplate required.

---

## Statement Keywords

Statement keywords are the heart of Tinder’s scripting logic. Each statement begins with a keyword—assign variables, control flow, perform I/O, or call libraries.
Statements can be single lines, or part of structured blocks (like `if ... endif`, `for ... endfor`, or `foreach ... endfor`).
Statements can be made conditional with an `if <expression>` clause at the end of the line.

---

### If/Else/Else If Blocks

Conditional logic in Tinder uses block syntax:

```tinder
if condition
  write "Condition met"
else if other_condition
  write "Other branch"
else
  write "Fallback branch"
endif
```

* Use `if` to start a condition block.
* Optionally use one or more `else if` or a single `else` for branching.
* Always end with `endif`.
* Only the first true branch runs; nesting is allowed.

---

### Assignment and Mutation

#### `set`

Assigns a value to a variable—or several at once. By separating identifiers and values with commas, you can batch assign multiple variables in one line.

```tinder
set x, y to 0, 0
set user to input()
```

#### `inc`

Increments a variable by 1 or a specified amount.

```tinder
inc score
inc tries 3
```

#### `dec`

Decrements a variable by 1 or a specified amount.

```tinder
dec lives
dec time 5
```

#### `put`

Places an item before or after an array.

```tinder
put "this" before list
put "that" after list
```

#### `swap`

Swap two variable values.

```tinder
swap a, b
```

---

### Input and Output

#### `write`

Appends text (with a newline) to a variable, or outputs it directly.

```tinder
write "Hello, world!" to output
"Welcome!"   \`\` Implicit write to default output
```

#### `input`

Prompts for user input, assigns result to a variable, and yields execution.

```tinder
input "Enter name:" to username
```

---

### Function Calls

#### `call`

Invokes a function or procedure from an API or variable.

```tinder
call login.find_user(input)
call battle.start()
```

---

### Control Flow

#### `jump`

Transfers execution to a label or line number.

```tinder
jump to retry
jump end if done
```

?> **Tip** Using an indirect expression allows you to resolve from a value to a jump target.  See (indirect)[] for more information.

#### `return`

Resumes execution at the line after the last jump.

```tinder
return
```

#### `yield`

Suspends script execution, optionally returning a value to the engine.

```tinder
yield
yield "Waiting for input"
```

#### `stop`

Ends script execution immediately.

```tinder
stop
```

---

!> **Note:**
Most statement keywords support `if <expression>` for conditional execution.
See [Conditions](language/basics.md#conditions) for details.
