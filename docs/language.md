<div style="display: flex; align-items: center">
<img src="tinder.svg" alt="drawing" width="64"/>
<font size="7">Language</font>
</div>

---
## Introduction

Tinder is a minimalist scripting language builder designed for deterministic, extensible logic in interactive scenes or nodes for Python applications.

It defines a small, declarative language optimized for ease of parsing, customization, and rapid iteration. Key features include:

- PEG-based syntax with a compact, extensible instruction set ("kindlings") for assignment, flow control, arithmetic, branching, I/O, and macros.  
- The `Firestarter` class for compiling scripts into executable Tinder instruction trees.  
- Dynamic registration of commands with support for default arguments.  
- Seamless integration with arbitrary application state via the `Crucible` class, supporting protected, global, and local scopes.  
- Syntactic sugar for common operations, including operator aliases, conditional statements, and array/list manipulation.

Tinder itself is unopinionated about how game or application state is structured. Scripts operate directly on a `Crucible`, meaning the user or host engine defines variables, memory mapping, and conventions for input, output, and control flow. Patterns and macros can be freely redefined to fit any domain.

## Basic Syntax and Structure

- Each script consists of lines; every line is one operation.  
- Valid line types are:  
  - **Keyword statements** (e.g., `set VAR 5`, `call foo()`)  
  - **Labels** (jump targets) prefixed with `#` (e.g., `# loop_start`)  
  - **Comments** starting with `//`  
  - **Strings or expressions on a line by themselves** implicitly produce output (like a `write` command).  
- Conditional execution is supported inline with commands (e.g., `jump fail if not USER`).  
- There are no block scopes or structured blocks—Tinder is unstructured and flat.  

## Top-Level Directives

- **Imports:**  
  - `import ModuleName` optionally aliased as `import ModuleName as Alias`  
  - `from Module import Name1, Name2, ...`  
- **Interrupts:**  
  - `catch ExceptionName at Label` sets up interrupt handlers.  
- **Constants:**  
  - Declared with `const NAME is VALUE` or `const NAME = VALUE`. Constants cannot be changed after declaration.  
- **Goto labels:**  
  - Lines starting with `# LabelName` define jump targets for flow control.

## Keywords

- `write` — Outputs a string or expression to the user (can be implicit by placing string/expression alone on a line).  
- `call` — Invokes a function with arguments.  
- `set` — Assigns a value to a variable.  
- `inc` / `dec` — Sugar for incrementing or decrementing a variable by 1 (shorthand for `set VAR VAR + 1` or `set VAR VAR - 1`).  
- `input` — Reads input from the user, optionally storing it in a variable.  
- `yield` — Pauses execution, optionally returning a value.  
- `stop` — Halts script execution.  
- `jump` — Transfers control to a label, optionally conditional.  
- `return` — Returns from a function or script.

## Expressions

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
