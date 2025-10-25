# Tutorial — short examples

This tutorial covers short runnable examples for the current CapLang prototype.

1) Hello / string concatenation

Create `examples/hello.capla` (already included):

```text
"Hello, " + "CapLang!"
```

Run with the interpreter:

```bash
python3 src/run.py examples/hello.capla --mode run
```

2) Arithmetic

Create `examples/math.capla`:

```text
print (1 + 2) * 3.5 - 4 / 2
```

Run with either mode (interpreter or compile):

```bash
python3 src/run.py examples/math.capla --mode run
python3 src/run.py examples/math.capla --mode compile
```


3) Comparisons and booleans

Create `examples/compare.capla`:

```text
print 1 + 2 == 3
```

This will print `True`.

4) Variables, if and for loops

Create `examples/for.capla`:

```text
var i = 0;
for ( ; i < 5 ; i = i + 1 ) {
	print i;
}
```

This demonstrates `var` declarations, the C-style `for` syntax (desugared to `while`), and `print` statements.

Next steps you can try
- Extend the parser to accept statements (assignment, `print`/`puts`), then wire them into the interpreter and compiler.
