from typing import List
from parser import (
    Binary, Grouping, Literal, Unary, Variable, Expr,
    Stmt, ExpressionStmt, PrintStmt, VarStmt, BlockStmt, IfStmt, WhileStmt, Assign, ImportStmt, Call, Get,
    FunctionStmt, Return
)
from lexer import TokenType


def indent_lines(lines: List[str], level: int = 1) -> List[str]:
    prefix = '    ' * level
    return [prefix + l for l in lines]


class Compiler:
    def __init__(self):
        # track whether generated code needs the `time` module
        self.needs_time = False

    def compile_expr(self, expr: Expr) -> str:
        if isinstance(expr, Binary):
            return self.compile_binary(expr)
        elif isinstance(expr, Grouping):
            return self.compile_grouping(expr)
        elif isinstance(expr, Literal):
            return self.compile_literal(expr)
        elif isinstance(expr, Unary):
            return self.compile_unary(expr)
        elif isinstance(expr, Variable):
            return self.compile_variable(expr)
        elif isinstance(expr, Get):
            return self.compile_get(expr)
        elif isinstance(expr, Call):
            return self.compile_call(expr)
        elif isinstance(expr, Assign):
            # assignment expression compiles to a simple Python assignment and returns the variable name
            name = expr.name.lexeme
            value = self.compile_expr(expr.value)
            return f"({name} := {value})" if False else f"{value}; {name} = {value}; {name}"

        raise Exception(f"Unknown expression type: {type(expr)}")

    def compile_binary(self, expr: Binary) -> str:
        left = self.compile_expr(expr.left)
        right = self.compile_expr(expr.right)
        operator = expr.operator.type

        if operator == TokenType.PLUS:
            return f"({left} + {right})"
        elif operator == TokenType.MINUS:
            return f"({left} - {right})"
        elif operator == TokenType.STAR:
            return f"({left} * {right})"
        elif operator == TokenType.SLASH:
            return f"({left} / {right})"
        elif operator == TokenType.EQUAL_EQUAL:
            return f"({left} == {right})"
        elif operator == TokenType.BANG_EQUAL:
            return f"({left} != {right})"
        elif operator == TokenType.LESS:
            return f"({left} < {right})"
        elif operator == TokenType.LESS_EQUAL:
            return f"({left} <= {right})"
        elif operator == TokenType.GREATER:
            return f"({left} > {right})"
        elif operator == TokenType.GREATER_EQUAL:
            return f"({left} >= {right})"

        raise Exception(f"Unknown binary operator: {operator}")

    def compile_grouping(self, expr: Grouping) -> str:
        return f"({self.compile_expr(expr.expression)})"

    def compile_literal(self, expr: Literal) -> str:
        if expr.value is None:
            return "None"
        # Strings need to be quoted for valid Python syntax
        if isinstance(expr.value, str):
            return repr(expr.value)
        return str(expr.value)

    def compile_unary(self, expr: Unary) -> str:
        right = self.compile_expr(expr.right)
        if expr.operator.type == TokenType.MINUS:
            return f"(-{right})"
        elif expr.operator.type == TokenType.BANG:
            return f"(not {right})"

        raise Exception(f"Unknown unary operator: {expr.operator.type}")

    def compile_variable(self, expr: Variable) -> str:
        return expr.name.lexeme

    def compile_get(self, expr: Get) -> str:
        obj = self.compile_expr(expr.object)
        name = expr.name.lexeme
        return f"{obj}.{name}"

    def compile_call(self, expr: Call) -> str:
        callee = self.compile_expr(expr.callee)
        args = ", ".join(self.compile_expr(a) for a in expr.arguments)
        # Map runtime `sleep(...)` calls to Python's `time.sleep(...)` in compiled output.
        # If the callee is the bare name 'sleep', emit time.sleep(...) and mark
        # that we need to import the time module at the top of the generated file.
        if callee == 'sleep':
            self.needs_time = True
            return f"time.sleep({args})"

        return f"{callee}({args})"

    # --- Statement compilation ---
    def compile_stmt(self, stmt: Stmt) -> List[str]:
        if isinstance(stmt, ImportStmt):
            # Preserve dotted import paths from CapLang so generated Python mirrors
            # the original Java-style imports (e.g. `import org.bukkit.Bukkit`).
            parts = [p.lexeme for p in stmt.path]
            dotted = ".".join(parts)
            return [f"import {dotted}"]
        
        if isinstance(stmt, PrintStmt):
            return [f"print({self.compile_expr(stmt.expression)})"]
        if isinstance(stmt, VarStmt):
            name = stmt.name.lexeme
            if stmt.initializer is not None:
                return [f"{name} = {self.compile_expr(stmt.initializer)}"]
            return [f"{name} = None"]
        if isinstance(stmt, ExpressionStmt):
            # evaluate expression for side-effects
            return [f"{self.compile_expr(stmt.expression)}"]
        if isinstance(stmt, BlockStmt):
            lines: List[str] = []
            for s in stmt.statements:
                lines.extend(self.compile_stmt(s))
            return lines
        if isinstance(stmt, IfStmt):
            cond = self.compile_expr(stmt.condition)
            then_lines = self.compile_stmt_block(stmt.then_branch)
            lines = [f"if {cond}:"]
            lines.extend(indent_lines(then_lines))
            if stmt.else_branch is not None:
                else_lines = self.compile_stmt_block(stmt.else_branch)
                lines.append("else:")
                lines.extend(indent_lines(else_lines))
            return lines
        if isinstance(stmt, WhileStmt):
            cond = self.compile_expr(stmt.condition)
            body_lines = self.compile_stmt_block(stmt.body)
            lines = [f"while {cond}:"]
            lines.extend(indent_lines(body_lines))
            return lines

        if isinstance(stmt, FunctionStmt):
            name = stmt.name.lexeme
            params = ", ".join(p.lexeme for p in stmt.params)
            lines = [f"def {name}({params}):"]
            body_lines: List[str] = []
            for s in stmt.body:
                body_lines.extend(self.compile_stmt(s))
            if not body_lines:
                body_lines = ["pass"]
            lines.extend(indent_lines(body_lines))
            return lines
        if isinstance(stmt, Return):
            if stmt.value is None:
                return ["return"]
            return [f"return {self.compile_expr(stmt.value)}"]

        raise Exception(f"Can't compile statement type: {type(stmt)}")

    def compile_stmt_block(self, stmt: Stmt) -> List[str]:
        # helper to produce a list of lines for a statement or block
        if isinstance(stmt, BlockStmt):
            lines: List[str] = []
            for s in stmt.statements:
                lines.extend(self.compile_stmt(s))
            return lines
        return self.compile_stmt(stmt)

    def compile_program(self, statements: List[Stmt]) -> str:
        lines: List[str] = []
        for s in statements:
            lines.extend(self.compile_stmt(s))
        # If compiled code used time.sleep, emit a top-level import
        if getattr(self, 'needs_time', False):
            lines.insert(0, 'import time')

        # join lines into Python source
        return "\n".join(lines)