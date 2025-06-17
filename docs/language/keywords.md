## Directive Keywords

**Directives** are special instructions that configure your script, import tools, or define constants and error handling. They always execute when encountered and are not conditional.

---

### Importing

#### `import`

Brings an external API—such as a set of functions, utilities, or constants—into your script’s namespace. After importing, you access its contents using dot notation.

```tinder
import math
import text as txt
```

* Use `as` to assign a custom name.
* Only APIs provided by the engine or standard library can be imported this way.

?> **Tip:**
APIs let you extend Tinder with engine-level features or reusable libraries, while keeping your script logic separate.

---

#### `from`

Imports specific functions or values from an API directly into your script’s local scope. This allows you to use them without a prefix.

```tinder
from math import sqrt, pow
sqrt(25)
```

* Imported items appear as if they were defined directly in your script.

?> **Note:**
`from` is best used when you need only a few symbols from a large API.

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

### Control flow

---

#### `# <label>`

Defines a jump target for control flow. Labels may optionally use `else` to provide an alternate destination when the label is reached "naturally" (not via a jump).

```tinder
# retry
# end else retry
```

?> **Labels** are the core building blocks of Tinder’s flat, explicit flow control.

## Statement Keywords

Statement keywords are the heart of Tinder’s scripting logic. Each statement begins with a keyword that tells the interpreter what to do—assign variables, control flow, perform I/O, or interact with APIs. Statements can be made conditional with an `if <expression>` clause at the end of the line.

---

### Assignment and Mutation

#### `set`

Assigns a value to a variable.

```tinder
set counter to 0
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

---

### Input and Output

#### `write`

Appends text (with a newline) to a variable, or outputs it directly.

```tinder
write "Hello, world!" to output
"Welcome!"   // Implicit write to default output
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

Transfers execution to a label, line number, or string identifier.

```tinder
jump to retry
jump end if done
```

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
