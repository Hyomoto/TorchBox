## Libraries and Extending Tinder <!-- {docsify-ignore} -->

Tinder scripts are built to express gameplay, narrative, and application logic directly—using Tinder’s native features for state, flow, input, and branching. **Libraries** let your scripts reach beyond what’s possible in pure script, integrating with engine features, privileged operations, or custom logic. Libraries extend Tinder, but do not define what scripting is *for*.

---

### What is a Library in Tinder?

A **library** is a bundle of functions, constants, or utilities that can be imported into your script. Libraries are defined by the engine, standard library, or game code, and provide reusable tools for things like string manipulation, math, file access, or special engine features.

?> **Philosophy:**
Tinder is designed for in-script problem solving and gameplay flow. Libraries are there to *extend* the language—not replace it—by providing extra capabilities or bridging to the outside world.

---

### When and Why to Use Libraries

* **Accessing engine features:** If you need to interact with something outside your script (files, UI, combat logic), use a library.
* **Security & permissions:** The engine controls what libraries your script can see or use.
* **Convenience:** Only import the functions or constants you need, keeping your script tidy.

**Examples of library use:**

* Start a battle with `call battle.start()`
* Authenticate with `login.find_user(input)`
* Format text columns with `text.column()`

But for most core logic, state, and control—**Tinder’s built-in scripting remains the main tool.** Menus, branching, dialog, and more can all be built in pure Tinder.

---

### Importing Libraries

* Use `import library` to load a library with all its tools, optionally under a custom name.
* Use `from library import symbol1, symbol2` to import specific tools directly into your script.

```tinder
import math
from text import column
```

?> Once imported, library functions and values are available alongside all your regular script logic.

---

### Permissions and Security

Some libraries (or individual functions) may require permission to use—this is enforced by the engine, not Tinder itself. This mechanism allows for safe, sandboxed scripting, especially in games or systems where users can write their own scripts. See your engine’s documentation for available libraries and any permissions or restrictions.

?> [writing a library](language/advanced.md#writing-and-integrating-libraries-in-tinder) contains more information about the technical aspects of writing a library, as well as how permissions are defined.

---

**Summary:**

* **Tinder scripts are self-sufficient for most logic and flow.**
* **Libraries are used to reach out** to engine features, advanced utilities, or shared tools.
* **Import only what you need** for clarity and maintainability.
* **The engine or game controls** what libraries exist and what scripts can access.
