#!/usr/bin/env python3
"""
py2capla - simple, single-file Python -> .capla transpiler

This implements a conservative subset of Python -> CapLang (.capla) translation.

Supported features (small, useful subset):
- top-level and function `def` definitions
- `print(...)` mapped to `print <expr>` in CapLang
- numeric and string literals, booleans, None -> nil
- binary ops: +, -, *, / and comparisons: ==, !=, <, <=, >, >=
- unary - and not (translated to `!`)
- assignments (emitted as `var name = expr` for safety)
- return, if/else, while
- for-loops over range(...) translated to equivalent `var` + `while` loop

Limitations:
- complex comprehensions, generators, class defs, imports, list/dict literals
  and logical `and`/`or` are not fully supported. This is a pragmatic tool
  for small scripts and examples.

Usage:
  python py2capla/py2capla.py -i input.py -o out.capla
  python py2capla/py2capla.py -e 'print("hi")' -o out.capla

Author: added by assistant
"""
import ast
import argparse
import sys
from typing import List


def quote_str(s: str) -> str:
    # CapLang examples use double-quoted strings
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


class Py2Capla(ast.NodeVisitor):
    def __init__(self):
        self.lines: List[str] = []

    def compile(self, node: ast.AST) -> str:
        self.visit(node)
        return "\n".join(self.lines) + "\n"

    # --- Module / statements ---
    def visit_Module(self, node: ast.Module):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Expr(self, node: ast.Expr):
        # expression statement
        if isinstance(node.value, ast.Call) and getattr(node.value.func, 'id', None) == 'print':
            # special-case print: print arg1, arg2 -> multiple prints separated by space
            args = node.value.args
            if not args:
                self.lines.append('print ""')
            else:
                # join multiple args with ' + " " + ' to emulate Python print spacing
                compiled_args = [self.compile_expr(a) for a in args]
                if len(compiled_args) == 1:
                    self.lines.append(f'print {compiled_args[0]}')
                else:
                    joined = ' + " " + '.join(compiled_args)
                    self.lines.append(f'print ({joined})')
            return

        expr = self.compile_expr(node.value)
        self.lines.append(expr)

    def visit_Assign(self, node: ast.Assign):
        # Support simple single-target assignments to a Name
        if len(node.targets) != 1:
            raise RuntimeError('Only single-target assignments are supported')
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise RuntimeError('Only simple name targets supported in assignments')

        name = target.id
        value = self.compile_expr(node.value)
        # Emit as var declaration for safer first-time binding
        self.lines.append(f'var {name} = {value}')

    def visit_AugAssign(self, node: ast.AugAssign):
        if not isinstance(node.target, ast.Name):
            raise RuntimeError('Only simple name augassign supported')
        target = node.target.id
        op = self.binop_symbol(node.op)
        val = self.compile_expr(node.value)
        self.lines.append(f'{target} = ({target} {op} {val})')

    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name
        params = [arg.arg for arg in node.args.args]
        param_list = ', '.join(params)
        self.lines.append(f'def {name}({param_list}) {{')
        # body: compile into inner lines with indentation
        inner = Py2Capla()
        for stmt in node.body:
            inner.visit(stmt)
        # ensure non-empty body
        if not inner.lines:
            self.lines.append('    pass')
        else:
            for l in inner.lines:
                self.lines.append('    ' + l)
        self.lines.append('}')

    def visit_Return(self, node: ast.Return):
        if node.value is None:
            self.lines.append('return')
        else:
            self.lines.append(f'return {self.compile_expr(node.value)}')

    def visit_If(self, node: ast.If):
        cond = self.compile_expr(node.test)
        self.lines.append(f'if ({cond}) {{')
        inner = Py2Capla()
        for s in node.body:
            inner.visit(s)
        for l in inner.lines:
            self.lines.append('    ' + l)
        self.lines.append('}')
        if node.orelse:
            self.lines.append('else {')
            inner2 = Py2Capla()
            for s in node.orelse:
                inner2.visit(s)
            for l in inner2.lines:
                self.lines.append('    ' + l)
            self.lines.append('}')

    def visit_While(self, node: ast.While):
        cond = self.compile_expr(node.test)
        self.lines.append(f'while ({cond}) {{')
        inner = Py2Capla()
        for s in node.body:
            inner.visit(s)
        for l in inner.lines:
            self.lines.append('    ' + l)
        self.lines.append('}')

    def visit_For(self, node: ast.For):
        # Only support 'for <name> in range(...)' patterns and translate to var+while
        if not isinstance(node.target, ast.Name):
            raise RuntimeError('Only simple for-loop targets supported')
        if not isinstance(node.iter, ast.Call) or getattr(node.iter.func, 'id', None) != 'range':
            raise RuntimeError('Only for-loops over range(...) are supported')

        args = node.iter.args
        if len(args) == 1:
            start = '0'
            stop = self.compile_expr(args[0])
            step = '1'
        elif len(args) == 2:
            start = self.compile_expr(args[0])
            stop = self.compile_expr(args[1])
            step = '1'
        elif len(args) == 3:
            start = self.compile_expr(args[0])
            stop = self.compile_expr(args[1])
            step = self.compile_expr(args[2])
        else:
            raise RuntimeError('range() with too many args')

        varname = node.target.id
        self.lines.append(f'var {varname} = {start}')
        # condition depends on sign of step; assume positive step for simplicity
        self.lines.append(f'while ({varname} < {stop}) {{')
        inner = Py2Capla()
        for s in node.body:
            inner.visit(s)
        # increment
        inner.lines.append(f'{varname} = ({varname} + {step})')
        for l in inner.lines:
            self.lines.append('    ' + l)
        self.lines.append('}')

    # --- Expressions ---
    def compile_expr(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            v = node.value
            if v is None:
                return 'nil'
            if isinstance(v, bool):
                return 'true' if v else 'false'
            if isinstance(v, (int, float)):
                return repr(v)
            if isinstance(v, str):
                return quote_str(v)
            raise RuntimeError(f'Unsupported constant: {v!r}')

        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.BinOp):
            left = self.compile_expr(node.left)
            right = self.compile_expr(node.right)
            op = self.binop_symbol(node.op)
            return f'({left} {op} {right})'

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return f'!{self.compile_expr(node.operand)}'
            if isinstance(node.op, ast.USub):
                return f'-{self.compile_expr(node.operand)}'
            raise RuntimeError('Unsupported unary operator')

        if isinstance(node, ast.Compare):
            # Only single comparator supported (common case)
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise RuntimeError('Only simple comparisons supported')
            left = self.compile_expr(node.left)
            op = self.cmpop_symbol(node.ops[0])
            right = self.compile_expr(node.comparators[0])
            return f'({left} {op} {right})'

        if isinstance(node, ast.Call):
            # simple function call
            func = node.func
            if isinstance(func, ast.Name):
                fname = func.id
            else:
                # support attribute calls like obj.method
                fname = self.compile_expr(func)

            args = [self.compile_expr(a) for a in node.args]
            return f"{fname}({', '.join(args)})"

        if isinstance(node, ast.BoolOp):
            # conservative translation: join with '||'/'&&' (note: CapLang lexer/parser may not support these tokens fully)
            op = ' || ' if isinstance(node.op, ast.Or) else ' && '
            parts = [self.compile_expr(v) for v in node.values]
            return '(' + op.join(parts) + ')'

        if isinstance(node, ast.Attribute):
            return f"{self.compile_expr(node.value)}.{node.attr}"

        if isinstance(node, ast.Subscript):
            # simple subscription a[b]
            return f"{self.compile_expr(node.value)}[{self.compile_expr(node.slice.value if isinstance(node.slice, ast.Index) else node.slice)}]"

        raise RuntimeError(f'Unsupported expression node: {type(node)}')

    def binop_symbol(self, op: ast.AST) -> str:
        if isinstance(op, ast.Add):
            return '+'
        if isinstance(op, ast.Sub):
            return '-'
        if isinstance(op, ast.Mult):
            return '*'
        if isinstance(op, ast.Div):
            return '/'
        if isinstance(op, ast.Mod):
            return '%'
        raise RuntimeError(f'Unsupported binary op: {op}')

    def cmpop_symbol(self, op: ast.AST) -> str:
        if isinstance(op, ast.Eq):
            return '=='
        if isinstance(op, ast.NotEq):
            return '!='
        if isinstance(op, ast.Lt):
            return '<'
        if isinstance(op, ast.LtE):
            return '<='
        if isinstance(op, ast.Gt):
            return '>'
        if isinstance(op, ast.GtE):
            return '>='
        raise RuntimeError(f'Unsupported comparison op: {op}')


def transpile_source(source: str) -> str:
    tree = ast.parse(source)
    compiler = Py2Capla()
    return compiler.compile(tree)


def main(argv=None):
    p = argparse.ArgumentParser(description='Simple Python -> .capla transpiler (single-file)')
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', '--input', help='Input Python file')
    group.add_argument('-e', '--expr', help='Inline Python expression/script')
    p.add_argument('-o', '--output', help='Output .capla file (defaults to stdout)')
    args = p.parse_args(argv)

    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            src = f.read()
    else:
        src = args.expr

    cap_src = transpile_source(src)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(cap_src)
        print(f'Wrote {args.output}')
    else:
        print(cap_src)


if __name__ == '__main__':
    main()
