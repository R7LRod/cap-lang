# Language specification (prototype)

This file documents the small expression language that CapLang currently implements.

Lexical elements
- Numbers: integers and floats (lexer converts to Python float tokens)
- Strings: double-quoted, e.g. "hello"
- Identifiers: letters, digits and underscores, starting with letter or underscore
- Keywords recognized by the lexer: `def`, `class`, `if`, `else`, `true`, `false`, `nil`, `return`

Tokens (selected)
- Operators: `+ - * / = == != < <= > >= !`
- Parentheses: `(`, `)`
- Delimiters: `{ } , . ;`

Statements (supported)
- `print <expression>` — print the expression value.
- `var <name> = <expression>;` — declare a variable (initializer optional).
- Blocks: `{ ... }` create a new lexical scope.
- `if (<condition>) <then> [else <else>]` — conditional execution.
- `while (<condition>) <body>` — while loop.
- `for (<init>; <condition>; <increment>) <body>` — C-style for loop (desugared to `while` by the parser).

Grammar (high-level)

program        -> declaration* EOF ;
declaration    -> "var" IDENTIFIER ("=" expression)? ";" | statement ;
statement      -> "print" expression ";" | "for" '(' ... ')' statement | "if" '(' expression ')' statement ("else" statement)? | "while" '(' expression ')' statement | block | expression_statement ;
expression_statement -> expression (";")? ;

expression     -> assignment ;
assignment     -> IDENTIFIER "=" assignment | equality ;
equality       -> comparison ( ("!=" | "==") comparison )* ;
comparison     -> term ( (">" | ">=" | "<" | "<=") term )* ;
term           -> factor ( ("-" | "+") factor )* ;
factor         -> unary ( ("/" | "*") unary )* ;
unary          -> ("!" | "-") unary | primary ;
primary        -> NUMBER | STRING | "true" | "false" | "nil" | IDENTIFIER | "(" expression ")" ;

Semantics
- Numbers are treated as floats at runtime.
- `+` is overloaded for number addition and string concatenation (both operands must be same type).
- Variable declarations create names in the current environment; assignment updates an existing variable in the nearest enclosing environment.
- `for` loops are desugared to `while` loops by the parser and behave accordingly.

Compiler mapping
- The compiler emits Python code for supported constructs (assignments, print, if/while/blocks). This is a convenience for prototyping and interop; emitted code is executed with Python's semantics where they align.

Limitations and future work
- Functions (`def`) and classes are recognized by the lexer but not implemented in the parser/interpreter yet.
- No standard library beyond `print`.
- Error messages are basic; adding better diagnostics is a planned improvement.
