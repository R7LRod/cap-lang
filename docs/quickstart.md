# Quickstart

Minimal steps to run CapLang files locally.

1) Ensure you have Python 3 installed (3.8+ recommended).

2) Run the interpreter on an example:

```bash
python3 src/run.py examples/hello.capla --mode run
```

3) Compile-to-Python and run in-memory:

```bash
python3 src/run.py examples/hello.capla --mode compile
```

4) Create your own `.capla` file. A `.capla` file is currently expected to contain a single expression. Example:

```text
print "Hello " + "CapLang"
```

Limitations
Extensions: pyspigot integration
- You can use Java-style imports for pyspigot classes in CapLang. For example:

```text
import org.bukkit.Bukkit;
print Bukkit.getName();
```

This will compile to `from pyspigot import Bukkit` and make the `Bukkit` symbol available when running compiled code. The interpreter also attempts to bind the same name from a local `pyspigot` package.

Note: this prototype includes a small local `pyspigot` stub for demos. To integrate with a real Spigot/Bukkit bridge, install or provide a `pyspigot` package that exposes the expected classes.
