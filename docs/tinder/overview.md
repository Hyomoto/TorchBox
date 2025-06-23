## Introduction <!-- {docsify-ignore} -->

**Tinder** is a minimalist scripting language for building clear, deterministic logic in any project. It’s designed to be easy to read, simple to parse, and quick to adapt—making it a great fit for interactive fiction, text-driven games, or any application that needs flexible scripting.

Tinder doesn’t enforce how your engine works. Instead, it works alongside your application, storing and updating state in a central “Crucible.” Most interaction is handled by reading or writing values in the Crucible, and when you need to trigger events or signal the engine, you can do so with simple exceptions.

**Why Tinder?**

* **No clutter:** One instruction per line, no block scoping, no hidden rules.
* **Easy to extend:** The grammar is defined with PEG, so you can tweak or expand it as needed.
* **Transparent state:** All state lives in the Crucible, keeping things predictable.
* **Ideal for scripting:** Especially strong for branching story logic, user input handling, and quick prototyping.

### Highlights <!-- {docsify-ignore} -->

* **Compact, extensible syntax:** Write clear assignments, control flow, I/O, and macros with a handful of keywords.
* **Seamless state integration:** The Crucible tracks everything—local, global, and protected variables.
* **Syntactic sugar:** Use operator aliases, easy conditionals, and flexible data structures for fast iteration.
* **Engine-agnostic:** Tinder works the same in any application—plug it into your own engine or tooling with minimal friction.
