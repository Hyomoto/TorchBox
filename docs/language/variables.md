## Variables <!-- {docsify-ignore} -->

Variables in Tinder are named references to data that your script can use. They are how you store, retrieve, and update information as your script runs—such as player input, status flags, counters, or results from function calls.

!> **Key Point:** Variables in Tinder belong to a Crucible—the memory map provided to your script when it runs. A script does not "own" its variables; instead, it interacts with whatever Crucible (or stack of Crucibles) it was given. This lets you decide, at runtime, what data a script can see or change.

### What is a Variable?

A variable is a name that refers to a value: a number, string, array, table, or any other data type supported by Tinder. Variables can be created, read, or updated as your script runs.

```tinder
set score to 0
set name to input()
inc tries
```

Variables do not need to be declared ahead of time; they are created as soon as you assign a value to them. Assignment is most often done with the `set` statement, but variables can also be updated by other actions or results of function calls. You use the variable’s name to read or update its value anywhere in your script.

---

### Variable Scope

Variables do not belong to a particular script. Instead, they are stored in one or more Crucibles, which may be chained together to provide *scope*. When your script looks up a variable:

1. It checks the current Crucible.
2. If not found, it checks the parent Crucible (if there is one), and so on.
3. If the variable is never found, an error is raised.

This means you can have both *local* and *global* variables in practice—simply by arranging Crucibles. For example, a typical setup might create a fresh local Crucible with a global Crucible as its parent. The script sees both as a flat set of variables, but changes affect only the local Crucible unless special rules are used.

?> **Practical note:**
You control what data a script can see and modify by controlling the Crucibles you give it, and how they are linked together.

---

### Variable Naming Rules

Variable names in Tinder follow these rules:

* Must start with a letter (A-Z, a-z) or underscore (`_`)
* May contain letters, digits (0-9), and underscores
* Are case-sensitive
* Can be of any practical length

**Examples of valid variable names:**

```
userName
_score
item123
temp_var
```

---

### Constants

To create a variable that cannot be changed after assignment, use `const`:

```tinder
const MAX_TRIES = 3
```

Constants work like any other variable but cannot be reassigned during script execution. Attempting to modify a constant will result in an error.

?> **Tip:**
Use constants for values that should never change during script execution—such as configuration limits, fixed identifiers, or static data.

---

### Errors and Exceptions

If you try to read a variable that doesn’t exist, or break a Crucible rule (like writing to a read-only scope or modifying a constant), Tinder will raise an error. You can handle these using the `catch` directive if you need to gracefully manage missing or protected data.

?> For advanced control (like preventing shadowing or enforcing type safety), see the [Crucible documentation](/#) for engine integrators.

---

**Summary:**

* Variables in Tinder are names for values living in a Crucible (or chain of Crucibles).
* Your script’s scope—what variables it sees—is defined entirely by the Crucible(s) passed in.
* Naming is flexible and familiar; use `const` for unchangeable values.
* Errors signal scope or assignment violations, and can be caught or handled if needed.
