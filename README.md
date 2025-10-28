
# CapLang

CapLang is a small, Ruby-like expression language prototype with two execution modes:

- runtime (interpreter)
- compiler-to-Python (compiles expressions to Python and runs them)

This repository is an early prototype focused on expressions (arithmetic, strings, comparisons, grouping). Some lexer keywords for statements (like `def`, `if`) exist but the parser currently only supports expressions.

Where to start
- Examples: `examples/hello.capla`, `examples/math.capla`, `examples/compare.capla`
- Runner: `src/run.py` — interpret or compile-and-run a `.capla` file
- Docs: `docs/` contains quickstart, language spec, tutorial and examples
- Compiler CLI: `bin/capla-compile` — compile `.capla` to a Python file that can be executed directly. Example:

	```bash
	./bin/capla-compile examples/hello.capla --out examples/compiled_hello.py
	python3 examples/compiled_hello.py
	```

New & experimental features
---------------------------------
This repository contains recent experimental additions to the prototype. See `docs/added_features.md` for details and examples (function definitions, compile-to-file, import preservation, a Python->CapLang translator, the `pyspigot` shim, and a scheduler used in the `LagManager` example).

Quickstart

Run the interpreter (evaluate the expression in the `.capla` file):

```bash
python3 src/run.py examples/hello.capla --mode run
```

Compile the expression to a Python expression and run it in-process:

```bash
python3 src/run.py examples/hello.capla --mode compile
```

Project status & notes
- Language: prototype supporting statements (`print`, `var`, blocks, `if`/`else`, `while`, `for`), expressions (arithmetic, strings, comparisons) and variables.
- Lexer and parser: keywords and statement parsing implemented for the items above.
- Interpreter: evaluates statements and expressions with lexical scoping.
- Compiler: emits Python code for supported constructs for prototyping.

Want to contribute?
See `docs/contributing.md`.

