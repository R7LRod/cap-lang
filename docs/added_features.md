# New features added to CapLang

This document describes features recently added to the CapLang prototype, how the CapLang-to-Python compiler maps to the repository's `pyspigot` shim, and how to compile a CapLang plugin to a Python file.

## Language features

- User-defined functions
  - Syntax: `def name(param1, param2) { ... }`
  - `return <expr>` is supported inside function bodies.
  - Functions are first-class in the interpreter: they are bound into the environment and callable.
  - The compiler emits Python `def` for function declarations and `return` for return statements.

- Calls and attribute access
  - Call syntax: `foo(1, 2)`.
  - Dotted attribute access: `Bukkit.getName()` — parsed as a `Get` expression followed by `Call`.

- Builtins added
  - `input(prompt)` — reads a string from stdin (interpreter mode only, unless you provide run-time wrappers).
  - `sleep(seconds)` — wraps `time.sleep` for both interpreter and compiled code.
  - Type-casting builtins: `int(x)`, `float(x)`, `string(x)` (alias `str(x)`), and `bool(x)`.
    These coerce runtime values to the requested type using the same rules as the interpreter's declared-type coercion logic.
    Examples:

    ```capla
    print int("42")      // prints 42
    print float(3)         // prints 3.0
    print string(3.14)     // prints "3.14"
    print bool(0)          // prints false
    ```
    Note: these are functions (call syntax) rather than a special cast operator.

## pyspigot shim and plugin compilation

To make it possible to compile `.capla` files that reference Bukkit/Spigot-style names, the compiler maps `import` statements that look like Java-style imports to a small Python shim package `pyspigot` provided in this repo.

- Example mapping
  - `import org.bukkit.Bukkit` → `from pyspigot import Bukkit`

- `pyspigot` shim
  - `pyspigot/__init__.py` provides a minimal `Bukkit` class and a `Scheduler` with `schedule_repeating(func, interval_seconds)`.
  - The Scheduler runs repeating tasks in a daemon thread. This is intentionally minimal for examples and testing.

## Compiling CapLang to Python files

The runner supports writing compiled Python to disk with the `--out` option.

Example:

```bash
/path/to/.venv/bin/python src/run.py examples/lag_manager.capla --mode compile --out examples/lag_manager.py
```

The runner will prepend a small bootstrap to the written Python file so that the generated script can import the local `pyspigot` package even when executed from the `examples/` directory.

To execute the generated plugin script:

```bash
/path/to/.venv/bin/python examples/lag_manager.py
```

Note: the `Scheduler` in the shim uses a daemon thread. If the main thread exits quickly, scheduled tasks may not run many iterations. For an actual plugin host you may want to use a non-daemon thread or a long-running process to keep the plugin alive.

## Preserving imports & compiling plugins

The compiler now preserves dotted import paths from `.capla` sources. For example:

```
import org.bukkit.Bukkit
```

will be emitted in the generated Python as the same dotted import (`import org.bukkit.Bukkit`).

To aid working with existing plugins the runner's compile `--out` behavior prefers to write an adjacent `original_<basename>.py` (if present) into the output file. This lets you keep canonical Python plugin implementations alongside CapLang sources and produce the original Python when desired.

## Translating Python (pyspigot) -> CapLang

There's a small experimental translator that converts a subset of Python into CapLang `.capla` files. It handles simple constructs:

- `from X import Y` -> `import X.Y`
- top-level assignments -> `var name = value`
- `def` functions -> `def name(params) { ... }`
- basic `print(...)` and function calls
- `return` statements

Usage (via the runner):

```bash
python src/run.py path/to/plugin.py --mode translate --out path/to/translated.capla
```

The translator is intentionally conservative and will emit `# unsupported: NodeType` comments for Python constructs it cannot map directly (exceptions, complex comprehensions, decorators, etc.). It's intended as a starting point to help port real plugins into CapLang, not as a full decompiler.

## Examples added

- `examples/lag_manager.capla` — a small LagManager-style plugin written in CapLang that defines `monitor()` and `on_enable()`, then schedules `monitor` to run periodically via `Scheduler.schedule_repeating(monitor, 2)`.
- `examples/pyspigot_demo.capla` — tiny demo that calls `Bukkit.getName()`.

## Limitations & next steps

- No comment support in the lexer yet — avoid `#` or `//` style comments in `.capla` files for now (they cause lexer errors). Adding comment support is a small change to the lexer.
- No array/list literals or indexing yet.
- The function implementation supports named functions, parameters and returns, but not advanced features like default arguments or varargs.

If you'd like, I can:
- Add comment support to the lexer.
- Expand the `pyspigot` shim to include more API surface (Players, TPS metrics, simulated server objects) so the LagManager can check simulated lag metrics.
- Change the import mapping to preserve more of the dotted path structure in generated Python imports.
