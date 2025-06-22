## Data Types and Access

Tinder supports several basic data types, each designed for clarity and ease of use in scripts. These are: **Numbers, Strings, Arrays, Tables, and Batches**. You interact with data using dot notation, membership operators, and function calls.

---

### Supported Data Types <!-- {docsify-ignore} -->

#### Numbers

Numbers are integers or floating-point values.

```tinder
set score to 42
set price to 10.99
```

#### Strings

Strings are enclosed in single `'` or double `"` quotes. They support escape sequences and interpolation.

```tinder
set name to "Devon"
set message to 'Hello, world!'
```

#### Arrays

Arrays are ordered lists, declared with square brackets `[]`.

```tinder
set items to [1, 2, 3]
set names to ["June", "William"]
```

#### Tables

Tables (dictionaries) are key-value pairs, declared with curly braces `{}`.

```tinder
set user to {name: "Devon", score: 100}
```

?> Tables and arrays both allow for trailing commas.

---

## Accessors and Data Retrieval

#### Dot Notation

* Use `.` to access table fields or array indices (if the next accessor is an integer).

  * `user.name` gets the value for key `"name"` in `user`
  * `list.0` gets the item at index `0` in `list`
* Dot access can be chained as long as each step resolves to a table, array, or a final value.

!> **Caveat:**
Dot chains *must* resolve stepwise to lists or dictionaries.

* `a.b.c` works if `a` is a dict, `a.b` is a dict, and so on.
* `a.b.foo()` works (function can be final value).
* `a.foo().b` **will not work**, since function calls terminate dot traversal.

#### Membership and Indexing

* Use `from` to explicitly retrieve a value by key or index:

  * `x from [10, 20, 30]` returns the item at index `x`
  * `k from {foo: 1, bar: 2}` returns the value for key `k`
* Use `in` to check for membership (`item in list`)

?> There is **no** `a[0]` syntax in Tinder. Use dot notation or `from` instead.

#### Function Calls

Functions are invoked with parentheses:

```tinder
call foo()
set result to math.add(1, 2)
```

Functions are **not** declared inside scripts; they are made available via the engine, standard library, or imports.
See [TODO](/#) for function reference.

---

## Operator Precedence

Operators in Tinder follow a defined precedence order, affecting how expressions are evaluated:

1. **Parentheses / Grouping**
2. **Unary:** `not`, `-`
3. **Multiplicative:** `*`, `/`, `//`, `mod`
4. **Additive:** `+`, `-`
5. **Comparisons:** `<`, `>`, `<=`, `>=`, `==`, `!=`
6. **Membership:** `in`, `from`, `at`
7. **Boolean:** `and`, `or`

!> Use parentheses to make evaluation order explicit, especially with mixed operators.

---

## Engine Functions and In-Script Logic

Functions in Tinder scripts are provided by the engine, standard library, or imports; scripts do not declare functions directly.

* You call them with `call foo()` or as part of an expression.

For advanced control flow, Tinder’s `jump` and `return` can be used with labels to create reusable logic segments within a script:

```tinder
set a to 0
#func else start
  inc a
  return
#start
  jump end if a == 5
  jump func
#end else start
```

?> While this pattern can mimic function calls, block constructs (`for`, `foreach`, `if`, etc.) are preferred for most logic.
See [Statements](language/basics.md#statements) and [Control Flow](language/keywords#control-flow) for more on block structures.
