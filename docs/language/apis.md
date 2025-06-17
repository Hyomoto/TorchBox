## APIs and Extending Tinder <!-- {docsify-ignore} -->

Tinder scripts are built to express game, narrative, and application logic directly—using the language’s own features for state, flow, input, and branching. **APIs** are used to reach beyond what scripts can directly touch, enabling integration with engine features, privileged operations, or custom libraries. APIs extend Tinder, but they do not define what scripting is *for*.

---

### What is an API in Tinder?

An **API** in Tinder is a collection of functions, variables, or services bundled together and made available for import into your script. APIs are defined by the engine or standard library, and are used for things that can’t (or shouldn’t) be done directly in script—such as interacting with files, running complex math, or accessing protected engine systems.

?> **Philosophy:**
The primary goal of Tinder scripting is to let you solve problems and express gameplay in-script, using Tinder’s flow and data features. APIs exist to *extend* the language, not to replace it.

---

### When and Why to Use APIs

* **Engine boundaries:** Need to interact with systems outside script state? Use an API.
* **Security:** The engine controls what APIs (and thus powers) each script can access.
* **Convenience:** Import only the tools or functions you actually need, reducing clutter.

For example, you might use APIs to:

* Start a battle with `call battle.start()`
* Authenticate a user with `login.find_user(input)`
* Format text columns with `text.column()`

But for most logic, state, and gameplay control—**Tinder script itself is the main tool.**
Complex systems (menus, dialogue, branching, simple battles, etc.) can all be built natively.

---

### Importing APIs

* Use `import api` to load an API with all its tools, optionally under a custom name.
* Use `from api import symbol1, symbol2` to pull specific functions or values into your script.

```tinder
import math
from text import column
```

?> Once imported, API functions are available alongside all your regular script logic.

---

### How APIs Are Made (Technical Note)

APIs are defined by engine developers, usually in Python, as subclasses of the `API` base class.
Functions are exposed using the `@exportable` decorator. When you import an API, Tinder collects these and makes them available to your script.

Advanced users: Engine implementers may inject functions or variables directly into the Crucible as well. For most users, using APIs through import is the standard method.

---

### Permissions and Security

Some APIs (or individual functions) require permission to use—this is enforced by the engine, not Tinder itself. This mechanism allows for safe, sandboxed scripting even in complex or user-driven environments.

?> See your engine’s documentation for available APIs and permission details.

---

**Summary:**

* **Tinder scripts can do most things natively**—state, logic, flow, menus, dialogue, and more.
* **APIs are used to reach out** to engine features, protected actions, or shared tools.
* **Imports bring in only what you need,** keeping scripts clear and focused.
* **The engine controls** what APIs and functions exist, and what scripts can access.
