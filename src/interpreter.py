from typing import Any, List
from lexer import Token, TokenType
from parser import (
    Binary, Grouping, Literal, Unary, Variable, Expr, Assign,
    Stmt, ExpressionStmt, PrintStmt, VarStmt, BlockStmt, IfStmt, WhileStmt, ImportStmt, Call, Get,
    FunctionStmt, Return
)
import time
from typing import List


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class FunctionCallable:
    def __init__(self, declaration: FunctionStmt, closure: 'Environment'):
        self.declaration = declaration
        self.closure = closure

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: 'Interpreter', args: List):
        env = Environment(self.closure)
        # bind parameters
        for i, param in enumerate(self.declaration.params):
            name = param.lexeme
            value = args[i] if i < len(args) else None
            env.define(name, value)

        try:
            interpreter.execute_block(self.declaration.body, env)
        except ReturnException as r:
            return r.value
        return None


class Environment:
    def __init__(self, enclosing: 'Environment' = None):
        self.values = {}
        # optional declared types for variables in this environment
        self.types = {}
        self.enclosing = enclosing

    def define(self, name: str, value: Any):
        self.values[name] = value

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def get_type(self, name: str):
        if name in self.types:
            return self.types[name]
        if self.enclosing is not None:
            return self.enclosing.get_type(name)
        return None

    def assign(self, name: str, value: Any):
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise RuntimeError(f"Undefined variable '{name}'")


class Interpreter:
    def __init__(self):
        self.environment = Environment()
        # Bind simple built-ins
        # input(prompt) -> Python input
        self.environment.define('input', lambda prompt=None: input(prompt if prompt is not None else ''))
        # sleep(seconds) -> time.sleep
        self.environment.define('sleep', time.sleep)
        # expose simple scheduler and other helpers via pyspigot import mapping

    def interpret(self, statements: List[Stmt]):
        try:
            for stmt in statements:
                self.execute(stmt)
        except Exception as error:
            raise RuntimeError(error)

    # --- Statement execution ---
    def execute(self, stmt: Stmt):
        if isinstance(stmt, ExpressionStmt):
            self.evaluate(stmt.expression)
        elif isinstance(stmt, PrintStmt):
            value = self.evaluate(stmt.expression)
            print(value)
        elif isinstance(stmt, VarStmt):
            value = None
            if stmt.initializer is not None:
                value = self.evaluate(stmt.initializer)
            # if a declared type is present, attempt to coerce the value
            if getattr(stmt, 'vtype', None) is not None:
                vtype = stmt.vtype.lexeme
                value = self.coerce_value(value, vtype)
                # record type in environment
                self.environment.types[stmt.name.lexeme] = vtype
            self.environment.define(stmt.name.lexeme, value)
        elif isinstance(stmt, ImportStmt):
            # Map Java-style import paths to the pyspigot module
            # Example: import org.bukkit.Bukkit -> will bind 'Bukkit' name from pyspigot
            last = stmt.path[-1].lexeme
            try:
                module = __import__("pyspigot")
                # try to get attribute from pyspigot
                value = getattr(module, last, module)
            except Exception:
                # If import fails, leave as None; runtime will indicate error when used
                value = None
            self.environment.define(last, value)
        elif isinstance(stmt, BlockStmt):
            self.execute_block(stmt.statements, Environment(self.environment))
        elif isinstance(stmt, IfStmt):
            cond = self.evaluate(stmt.condition)
            if self.is_truthy(cond):
                self.execute(stmt.then_branch)
            elif stmt.else_branch is not None:
                self.execute(stmt.else_branch)
        elif isinstance(stmt, WhileStmt):
            while self.is_truthy(self.evaluate(stmt.condition)):
                self.execute(stmt.body)
        elif isinstance(stmt, FunctionStmt):
            func = FunctionCallable(stmt, self.environment)
            self.environment.define(stmt.name.lexeme, func)
        elif isinstance(stmt, Return):
            value = None
            if stmt.value is not None:
                value = self.evaluate(stmt.value)
            # unwind via exception
            raise ReturnException(value)
        else:
            raise RuntimeError(f"Unknown statement type: {type(stmt)}")

    def execute_block(self, statements: List[Stmt], env: Environment):
        previous = self.environment
        try:
            self.environment = env
            for s in statements:
                self.execute(s)
        finally:
            self.environment = previous

    # --- Expression evaluation ---
    def evaluate(self, expr: Expr) -> Any:
        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, Grouping):
            return self.evaluate(expr.expression)

        if isinstance(expr, Unary):
            right = self.evaluate(expr.right)
            if expr.operator.type == TokenType.MINUS:
                return -float(right)
            elif expr.operator.type == TokenType.BANG:
                return not self.is_truthy(right)

        if isinstance(expr, Binary):
            left = self.evaluate(expr.left)
            right = self.evaluate(expr.right)

            if expr.operator.type == TokenType.MINUS:
                return float(left) - float(right)
            elif expr.operator.type == TokenType.SLASH:
                return float(left) / float(right)
            elif expr.operator.type == TokenType.STAR:
                return float(left) * float(right)
            elif expr.operator.type == TokenType.PLUS:
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                raise RuntimeError("Operands must be two numbers or two strings")
            elif expr.operator.type == TokenType.GREATER:
                return float(left) > float(right)
            elif expr.operator.type == TokenType.GREATER_EQUAL:
                return float(left) >= float(right)
            elif expr.operator.type == TokenType.LESS:
                return float(left) < float(right)
            elif expr.operator.type == TokenType.LESS_EQUAL:
                return float(left) <= float(right)
            elif expr.operator.type == TokenType.BANG_EQUAL:
                return not self.is_equal(left, right)
            elif expr.operator.type == TokenType.EQUAL_EQUAL:
                return self.is_equal(left, right)

        if isinstance(expr, Variable):
            return self.environment.get(expr.name.lexeme)

        if isinstance(expr, Call):
            callee = self.evaluate(expr.callee)
            args = [self.evaluate(a) for a in expr.arguments]
            # support interpreter-declared functions
            if hasattr(callee, 'call'):
                return callee.call(self, args)

            if callable(callee):
                return callee(*args)
            raise RuntimeError(f"Can only call functions and callable objects")

        if isinstance(expr, Get):
            obj = self.evaluate(expr.object)
            try:
                return getattr(obj, expr.name.lexeme)
            except Exception:
                raise RuntimeError(f"Attribute '{expr.name.lexeme}' not found on object")

        if isinstance(expr, Assign):
            value = self.evaluate(expr.value)
            # if the variable has a declared type, attempt coercion before assigning
            vtype = self.environment.get_type(expr.name.lexeme)
            if vtype is not None:
                value = self.coerce_value(value, vtype)
            self.environment.assign(expr.name.lexeme, value)
            return value

    def coerce_value(self, value: Any, vtype: str) -> Any:
        """Attempt to coerce a runtime value to the declared type name (vtype).

        Supported types: int, float, string, bool
        """
        if vtype is None:
            return value
        vt = vtype.lower()
        try:
            if vt == 'int':
                # prefer int when possible, fall back to converting to float
                try:
                    return int(value)
                except Exception:
                    try:
                        return int(float(value))
                    except Exception:
                        return float(value)
            if vt == 'float':
                return float(value)
            if vt in ('string', 'str'):
                return str(value)
            if vt == 'bool':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    v = value.strip().lower()
                    if v in ('true', '1', 'yes'):
                        return True
                    if v in ('false', '0', 'no'):
                        return False
                return bool(value)
        except Exception as e:
            raise RuntimeError(f"Cannot coerce value {value!r} to type '{vtype}': {e}")
        return value

        raise RuntimeError(f"Unknown expression type: {type(expr)}")

    def is_truthy(self, object: Any) -> bool:
        if object is None:
            return False
        if isinstance(object, bool):
            return object
        return True

    def is_equal(self, a: Any, b: Any) -> bool:
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b