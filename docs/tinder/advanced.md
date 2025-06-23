## Implementing Tinder

Integrating Tinder into your engine requires understanding how it signals control flow, errors, and requests for engine intervention. This is accomplished through a handful of exceptions, a powerful variable environment (the Crucible), and a set of special internal variables ("dunders"). Together, these form Tinder's contract with any host engine.

---

### Tinder Exceptions

Tinder scripts use a small set of exceptions to manage control flow, signal errors, and request services from the host engine. Engine authors must decide which exceptions to handle and how to interpret them.

#### Core Exceptions

* **TinderBurn**
  Raised when a script or library performs an illegal or unrecoverable operation. This is generally a fatal error—scripts should not attempt to recover, except in specialized scenarios (e.g., by manipulating `__LINE__`, though this is rarely practical).

* **Halted**
  Raised when a script calls `stop`. This signals intentional, orderly termination. The engine should clear any script stack or associated context and exit cleanly.

* **Yielded**
  Raised when a script calls `yield` or requests input. Yielded can include data (`e.carry`) to pass back to the engine. This allows scripts (or libraries) to pause, request information, or yield control for input, then resume where they left off.

* **Imported**
  Raised when a script requests a library import. The engine is responsible for resolving and injecting the requested library or symbols.

> **Note:**
> These exceptions must be handled by the host engine. If you don’t require features like library imports or pausing execution, you may ignore or remove related exceptions from your grammar or runtime.

?> Library functions can also raise **TinderBurn**, **Halted**, or **Yielded**. This allows advanced or privileged libraries to manage script flow and error handling from within custom functions.

---

### Example Engine Integration Loop

A typical engine loop for running a Tinder script might look like:

```python
while True:
    try:
        script.run(env)
    except Imported as e:
        # Handle library import, inject into environment, continue
        lib = self.libraries.get(e.library)
        if not lib:
            raise TinderBurn(f"Library '{e.library}' not found.")
        if not lib.hasPermission(script):
            raise TinderBurn(f"Library '{e.library}' cannot be imported in this context.")
        if e.request:
            env.update(lib.export(e.request))
        else:
            env[e.name or e.library] = lib.export()
        continue

    except Halted:
        # Script requested termination: clear stack/context, exit cleanly
        env['__STACK__'] = []
        break

    except Yielded as e:
        # Script yielded: pause and handle returned data (if any)
        if e.carry:
            env["__STACK__"][-1].env.update(e.carry)
        break

    break  # Execution finished normally
```

* **Imported:** Handles library import and resumes script execution after injection.
* **Halted:** Handles intentional script stop, typically clearing any running state.
* **Yielded:** Handles script pauses and passing control/data back to the engine.

---

### Crucibles (Variable Environments)

Tinder’s state is maintained in a **Crucible**, which acts as the script’s memory map. Crucibles are nested, dictionary-like environments that provide variable scope, inheritance, and advanced access rules. When you run a script, you supply the Crucible it operates on. This enables you to support features like global state, local variables, or session stacks as your engine requires.

> For advanced engines, you may want to implement custom Crucible rules—like shadowing prevention, protected variables, or access permissions. See [Variables & Crucibles](#) for more.

## Dunder Variables

Tinder exposes a set of special “dunder” (double-underscore) variables that give scripts and engines fine-grained control over execution state and flow. These variables live in the Crucible and can be read or modified—allowing for advanced or even self-modifying behaviors.
Most scripts and users never need to touch these; dunder variables exist primarily to keep internal mechanics out of the way of normal user code.

?> **Note:**
By default, dunder variables are fully accessible for reading and writing. Engines may restrict or sandbox them for safety, security, or debugging.

---

### Dunder Variable Reference

* `__LINE__`
  The next line number or label to execute. Changing this immediately jumps the script to a new location. This is the core mechanism behind all explicit Tinder control flow.

* `__CONDITION__`
  The result of the last condition (`if ...`). This value is checked by `else` statements to determine if they should run.

* `__JUMPED__`
  The line or label most recently targeted by a `jump`. This is also where `return` will transfer execution.

* `__ITER__`, `__INDEX__`, `__LENGTH__`
  Internal loop variables used by `foreach` constructs:

  * `__ITER__`: The current item or key being iterated
  * `__INDEX__`: The current index or position
  * `__LENGTH__`: The total number of items in the collection

---

**Why does this matter?**
Dunder variables are the “levers and gears” of Tinder’s interpreter. While typical scripts won’t reference them directly, they enable powerful tricks, debugging, or experimental dynamic behaviors if you need them. Their names use double underscores to avoid conflicts with user-defined variables.

?> As always: with great power comes great potential for chaos—use dunder variables responsibly!

## Writing and Integrating Libraries in Tinder

Libraries in Tinder provide a modular, flexible way to add new features and expose engine capabilities to scripts—without modifying the core language. At their heart, Tinder libraries are Python dictionaries of functions and values, but the Tinder `Library` class and decorators add useful features for complex or open scripting environments.

---

### What Is a Tinder Library?

A Tinder library is implemented as a request from the engine to modify the local environment, so what it is depends on how your engine responds to an import request. Because of how the import exception is raised, a Python dictionary of functions and values is an obvious choice. However, to make things easier and less error-prone, Tinder provides a `library` module with helpers and patterns for export control, context management, and permissions. These tools are optional, but recommended.

**Key Modules and Concepts:**

* **Library Class:**
  Inherit from this to define context-aware, exportable collections of functions for use in scripts.
* **Context:**
  The context argument (passed to the library at creation) acts as a closure, giving every exported method access to engine resources, game data, or anything else not passed directly by the script.
* **Exportable Methods:**
  Methods decorated with `@exportable` (or `@exportableAs("name")`) are easily flagged for inclusion and custom naming.
* **Static Evaluation:**
  Methods decorated with `@static_eval_safe` are flagged as safe to resolve by the compiler at compile time.
* **Permissions:**
  Permissions are declared at the library level (using a mixin or attribute), but enforcement must be handled by the engine when scripts request imports.
* **Export Method:**
  `export()` returns a dictionary of script-visible names to their respective methods. When called with a list of names, it returns only those entries.

---

### How to Make a Library

#### 1. Create the Library

Inherit from `Library` and provide a unique name and a context object (typically your engine or environment):

```python
class MyLibrary(Library):
    def __init__(self, context):
        super().__init__("my_lib", context)
```

#### 2. Define Methods for Scripts

* Each method you want accessible to scripts must:

  * Be decorated with `@exportable` or `@exportableAs("name")`
  * Accept `env` (the current Crucible/environment) as its first parameter.
    This gives the method access to script-local, user, or engine state.

```python
    @exportable
    def foo(self, env, x):
        # env: Crucible for the script's variable scope/state
        return x + 1

    @static_eval_safe
    @exportableAs("bar")
    def do_bar(self, env, y):
        return y * 2
```

> **Why `env`?**
> Tinder always passes the current script environment as the first argument to all library methods called from scripts. This ensures methods have access to script-local or user data.

#### 3. (Optional) Use Context for Engine Access

The `context` argument given to the library is available as `self.context` in all methods.
This lets you call engine APIs, access data stores, or interact with external systems from any script-callable method.

```python
    @exportable
    def get_player_name(self, env):
        # self.context could be your game engine
        return self.context.get_current_player().name
```

#### 4. (Optional) Set Permissions

A library allows for setting permissions via a kwarg. If your engine supports permission controls, this can be used to test whether or not a library should be accessible. However, this property does nothing on its own.

```python
class MyLibrary(Library):
    def __init__(self, context, **kwargs):
        super().__init__("my_lib", permissions=["admin"])
```

---

### How Export Works

The `export()` method walks all methods of your library and returns those marked as exportable in a dictionary. If you pass a list of names, only those are included (used for `from library import foo, bar`).

---

### Example: Creating and Registering a Library

```python
class MyLibrary(Library):
    def __init__(self, context):
        super().__init__("my_lib", context)

    @exportable
    def add(self, env, a, b):
        return a + b

    @static_eval_safe
    @exportableAs("mul")
    def multiply(self, env, a, b):
        return a * b

# Register libraries for scripts
libs = import_libraries("my_game.libraries", context)
# {'my_lib': <MyLibrary instance>}
```

---

### Implementing Imports in Your Engine

When a Tinder script requests a library import, it raises an `Imported` exception with:

* `library`: Name to import
* `name`: Alternate name if using `import ... as ...`
* `request`: List of symbols if using `from ... import ...`

Handle the exception to load the correct library and update the script environment:

```python
try:
    script.run(env)
except Imported as e:
    lib = self.libraries.get(e.library)
    if not lib:
        raise Exception(f"Library {e.library} not found!")
    # If specific symbols were requested (from ... import ...)
    if e.request:
        env.update(lib.export(e.request))
    else:
        env[e.name or e.library] = lib
```

?> This example uses the `export()` method for convenience, but you may handle or expose library methods as you wish.

---

### Permissions in Tinder Libraries

Permissions in Tinder are *opt-in*: they exist to help you restrict access to certain libraries or functions, especially in environments where users write their own scripts or untrusted code runs in your engine.

A library’s permissions are just a list of strings, set via a constructor kwarg:

```python
class MyLibrary(Library):
    def __init__(self, context):
        super().__init__("my_lib", permissions=["admin"])
```

> **What do permissions do?**
> By themselves, permissions are only metadata. Tinder doesn’t enforce them—they’re a hint for your engine to check before exposing a library (or function) to a script.

---

#### Should You Use Permissions?

* **Multi-user or open scripting environments:**
  If players, modders, or untrusted code authors write scripts, permissions are a simple way to protect sensitive features (like account management, privileged data, or admin commands).
* **Single-user or closed systems:**
  For interactive fiction engines, personal tools, or tightly controlled projects, you can ignore permissions entirely—they’re inert unless your engine checks them.

---

#### How to Use Permissions

1. **Flag** libraries (or methods) with relevant permissions.
2. **Check** the permissions list at import time (in your engine’s import handler) before granting the request.
3. **Decide** what a “permission” means in your system (user roles, API tiers, etc).

```python
if "admin" in lib.permissions and not user.is_admin:
    raise PermissionError("You do not have access to this library.")
```

?> Tinder’s permission system is intentionally lightweight. It’s up to you to decide how permissions are defined, checked, and enforced.
