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


def run_file(path: str, mode: str):
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

        # Provide a namespace with 'sleep' bound to time.sleep so compiled code can call sleep(...)
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


def main():
    parser = argparse.ArgumentParser(description='CapLang runner (interpret or compile)')
    parser.add_argument('path', help='Path to .capla file')
    parser.add_argument('--mode', choices=['run', 'compile'], default='run', help='Run with the interpreter or compile-to-python and run')

    args = parser.parse_args()

    return_code = run_file(args.path, args.mode)
    sys.exit(return_code)


if __name__ == '__main__':
    main()
