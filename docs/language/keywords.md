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

#### Foriter Labels

A **foriter label** provides a simple way to write C-style for-loops using labels. Syntax:

```tinder
#for i = 0; i < 5; endfor
```

This expands to:

```tinder
set i to 0
#for
jump endfor if not i < 5
```

* Initialize the loop variable.
* Label marks loop start.
* Conditional jump checks the loop condition.

Use a matching label (`#endfor`) as your loop exit.

---

#### Foreach Labels

A **foreach label** makes iterating over arrays or tables easier, auto-assigning variables to each item or key/value pair.

**Arrays:**

```tinder
#foreach item in ITEMS; enditems
```

Desugars to:

* Sets up iteration over `ITEMS`
* Assigns each value to `item` in turn
* Jumps to `enditems` when done

**Tables:**

```tinder
#foreach key, value in MAP; endmap
```

Desugars to:

* Assigns key and value for each entry in `MAP`
* Jumps to `endmap` when done

?> **Note:**
Tinder automatically handles the setup, index/key extraction, and loop control—making iteration easy and readable.

## Statement Keywords

Statement keywords are the heart of Tinder’s scripting logic. Each statement begins with a keyword that tells the interpreter what to do—assign variables, control flow, perform I/O, or interact with APIs. Statements can be made conditional with an `if <expression>` clause at the end of the line.

---

### Else

`else` allows you to specify an alternate action if the *last* evaluated condition was false.

```tinder
write "Hello there!" if JUST_ENTERED
else write "Anything else?"
```

!> **Note:**
Because Tinder is blockless, `else` always refers to the last evaluated condition—even if there are unrelated lines in between.
It does **not** create a block or require direct adjacency. Be careful to keep your conditional logic clear and well-organized.

**In short:**
`else` is a flat-language shorthand for fallback actions after a failed condition. It helps avoid writing multiple conditionals, but always remember: it doesn’t group statements the way structured languages do.

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
