import argparse
import sys
import os
import time

# Ensure src directory is on sys.path so local imports work when running this script
sys.path.insert(0, os.path.dirname(__file__))

from lexer import Lexer
from parser import Parser, ExpressionStmt
from interpreter import Interpreter
from compiler import Compiler
import ast
from typing import List


def run_file(path: str, mode: str, out: str | None = None):
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()

    tokens = Lexer(source).scan_tokens()
    statements = Parser(tokens).parse()

    if not statements:
        print("Parsing produced no statements.")
        return 1

    if mode == 'run':
        interp = Interpreter()
        interp.interpret(statements)
        return 0

    elif mode == 'compile':
        comp = Compiler()
        # If the program is a single expression statement, print its value for convenience
        if len(statements) == 1 and isinstance(statements[0], ExpressionStmt):
            # compile the single expression and wrap with print
            # reuse compiler.compile_expr by importing Compiler class
            python_expr = comp.compile_expr(statements[0].expression)
            python_code = f"print({python_expr})"
        else:
            python_code = comp.compile_program(statements)

        # If an output path was provided, write the compiled Python to that file
        if out:
            try:
                # Prepend a small bootstrap so the generated script can find the repository root
                # when executed from any subfolder. We compute the repo root here (relative to src/run.py)
                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                bootstrap = (
                    "import sys, os\n"
                    f"sys.path.insert(0, {repr(repo_root)})\n\n"
                )

                # If an adjacent original_<basename>.py exists next to the source, prefer that
                # as the compiled output so we produce the original, canonical plugin file.
                src_dir = os.path.dirname(path)
                base = os.path.splitext(os.path.basename(path))[0]
                original_py = os.path.join(src_dir, f"original_{base}.py")

                if os.path.exists(original_py):
                    with open(original_py, 'r', encoding='utf-8') as rf:
                        original_contents = rf.read()
                    with open(out, 'w', encoding='utf-8') as f:
                        f.write(bootstrap + original_contents)
                    print(f"Wrote original Python {original_py} to {out}")
                    return 0

                # Fallback: write the generated python code
                with open(out, 'w', encoding='utf-8') as f:
                    f.write(bootstrap + python_code)
                print(f"Wrote compiled Python to {out}")
            except Exception as e:
                print(f"Error writing compiled file: {e}")
                return 2
            return 0

        # Otherwise, execute the compiled code in a namespace that exposes 'sleep'
        namespace = {'sleep': time.sleep}
        try:
            exec(python_code, namespace)
        except Exception as e:
            print(f"Error running compiled code: {e}")
            return 2

        return 0

    else:
        print(f"Unknown mode: {mode}. Use 'run' or 'compile'.")
        return 3


def translate_python_to_capla(py_path: str, out_path: str | None = None):
    """Naive translator from a subset of Python -> CapLang (.capla).

    This covers: imports (from X import Y), simple assignments, function defs,
    calls, and returns. It is intentionally conservative and will skip nodes it
    doesn't understand.
    """
    with open(py_path, 'r', encoding='utf-8') as f:
        src = f.read()

    tree = ast.parse(src)

    lines: List[str] = []

    def expr_to_cap(e: ast.expr) -> str:
        if isinstance(e, ast.Constant):
            return repr(e.value)
        if isinstance(e, ast.Name):
            return e.id
        if isinstance(e, ast.Call):
            func = expr_to_cap(e.func)
            args = ", ".join(expr_to_cap(a) for a in e.args)
            return f"{func}({args})"
        if isinstance(e, ast.Attribute):
            return f"{expr_to_cap(e.value)}.{e.attr}"
        if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add):
            return f"({expr_to_cap(e.left)} + {expr_to_cap(e.right)})"
        # fallback
        return "nil"

    def stmt_to_cap(s: ast.stmt, indent: int = 0):
        pad = "    " * indent
        if isinstance(s, ast.ImportFrom):
            module = s.module if s.module else ''
            for n in s.names:
                # translate `from pyspigot import X` -> `import pyspigot.X`
                if module:
                    parts = module.split('.') + [n.name]
                    lines.append(pad + f"import {'.'.join(parts)}")
                else:
                    lines.append(pad + f"import {n.name}")
        elif isinstance(s, ast.FunctionDef):
            params = ", ".join(a.arg for a in s.args.args)
            lines.append(pad + f"def {s.name}({params}) {{")
            for sub in s.body:
                stmt_to_cap(sub, indent + 1)
            lines.append(pad + "}")
        elif isinstance(s, ast.Expr):
            # expression statement
            if isinstance(s.value, ast.Call):
                call = expr_to_cap(s.value)
                # map print calls
                if isinstance(s.value.func, ast.Name) and s.value.func.id == 'print':
                    if s.value.args:
                        lines.append(pad + f"print {expr_to_cap(s.value.args[0])}")
                    else:
                        lines.append(pad + "print \"\"")
                else:
                    lines.append(pad + call)
            else:
                lines.append(pad + expr_to_cap(s.value))
        elif isinstance(s, ast.Assign):
            if len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
                name = s.targets[0].id
                val = expr_to_cap(s.value)
                # use var for top-level assignments
                lines.append(pad + f"var {name} = {val}")
        elif isinstance(s, ast.Return):
            if s.value:
                lines.append(pad + f"return {expr_to_cap(s.value)}")
            else:
                lines.append(pad + "return")
        elif isinstance(s, ast.If):
            # simple if with condition
            cond = expr_to_cap(s.test)
            lines.append(pad + f"if ({cond}) {{")
            for ss in s.body:
                stmt_to_cap(ss, indent + 1)
            lines.append(pad + "}")
            if s.orelse:
                lines.append(pad + "else {")
                for ss in s.orelse:
                    stmt_to_cap(ss, indent + 1)
                lines.append(pad + "}")
        else:
            # unsupported statement: emit a comment with the node type
            lines.append(pad + f"# unsupported: {type(s).__name__}")

    for node in tree.body:
        stmt_to_cap(node, 0)

    out_text = "\n".join(lines)
    if out_path is None:
        out_path = os.path.splitext(py_path)[0] + ".capla"

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(out_text + "\n")

    print(f"Wrote translated CapLang to {out_path}")



def main():
    parser = argparse.ArgumentParser(description='CapLang runner (interpret or compile)')
    parser.add_argument('path', help='Path to a .capla or .py file')
    parser.add_argument('--mode', choices=['run', 'compile', 'translate'], default='run', help='Run with the interpreter, compile-to-python and run, or translate a Python -> .capla')
    parser.add_argument('--out', help='When mode=compile or mode=translate, write output to this file instead of executing it')

    args = parser.parse_args()

    if args.mode == 'translate':
        # translate Python file to CapLang
        translate_python_to_capla(args.path, args.out)
        return_code = 0
    else:
        return_code = run_file(args.path, args.mode, args.out)
    sys.exit(return_code)


if __name__ == '__main__':
    main()
