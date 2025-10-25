from typing import List, Any, Optional
from lexer import Token, TokenType

# Expression nodes
class Expr:
    pass

class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression = expression

class Literal(Expr):
    def __init__(self, value: Any):
        self.value = value

class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right

class Variable(Expr):
    def __init__(self, name: Token):
        self.name = name

class Assign(Expr):
    def __init__(self, name: Token, value: Expr):
        self.name = name
        self.value = value

class Function(Expr):
    def __init__(self, name: Token, params: List[Token], body: List['Stmt']):
        self.name = name
        self.params = params
        self.body = body

class ReturnStmt(Expr):
    def __init__(self, value: Optional[Expr]):
        self.value = value

class Get(Expr):
    def __init__(self, object: Expr, name: Token):
        self.object = object
        self.name = name

class Call(Expr):
    def __init__(self, callee: Expr, arguments: List[Expr]):
        self.callee = callee
        self.arguments = arguments

# Statement nodes
class Stmt:
    pass

class ExpressionStmt(Stmt):
    def __init__(self, expression: Expr):
        self.expression = expression

class PrintStmt(Stmt):
    def __init__(self, expression: Expr):
        self.expression = expression

class FunctionStmt(Stmt):
    def __init__(self, name: Token, params: List[Token], body: List[Stmt]):
        self.name = name
        self.params = params
        self.body = body

class Return(Stmt):
    def __init__(self, value: Optional[Expr]):
        self.value = value

class VarStmt(Stmt):
    def __init__(self, name: Token, initializer: Optional[Expr], vtype: Optional[Token] = None):
        self.name = name
        self.initializer = initializer
        self.vtype = vtype

class ImportStmt(Stmt):
    def __init__(self, path: List[Token]):
        self.path = path

class BlockStmt(Stmt):
    def __init__(self, statements: List[Stmt]):
        self.statements = statements

class IfStmt(Stmt):
    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Optional[Stmt]):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class WhileStmt(Stmt):
    def __init__(self, condition: Expr, body: Stmt):
        self.condition = condition
        self.body = body


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> List[Stmt]:
        statements: List[Stmt] = []
        while not self.is_at_end():
            statements.append(self.declaration())
        return statements

    # --- Declarations / statements ---
    def declaration(self) -> Stmt:
        if self.match(TokenType.VAR):
            return self.var_declaration()
        if self.match(TokenType.DEF):
            return self.function_declaration()
        if self.match(TokenType.IMPORT):
            return self.import_declaration()
        return self.statement()

    def import_declaration(self) -> Stmt:
        # parse dotted path: IDENT ('.' IDENT)*
        parts: List[Token] = []
        parts.append(self.consume(TokenType.IDENTIFIER, "Expect module name in import."))
        while self.match(TokenType.DOT):
            parts.append(self.consume(TokenType.IDENTIFIER, "Expect name after '.' in import."))

        # optional semicolon
        if self.match(TokenType.SEMICOLON):
            pass

        return ImportStmt(parts)

    def var_declaration(self) -> Stmt:
        # support optional type annotation: var <type> <name> = <expr>
        vtype = None
        name = None
        if self.match(TokenType.IDENTIFIER):
            first = self.previous()
            # if the next token is also an identifier, treat first as the type
            if self.check(TokenType.IDENTIFIER):
                vtype = first
                name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
            else:
                name = first
        else:
            name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        # optional semicolon
        if self.match(TokenType.SEMICOLON):
            pass

        return VarStmt(name, initializer, vtype)

    def statement(self) -> Stmt:
        if self.match(TokenType.PRINT):
            return self.print_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return BlockStmt(self.block())

        return self.expression_statement()

    def print_statement(self) -> PrintStmt:
        expr = self.expression()
        if self.match(TokenType.SEMICOLON):
            pass
        return PrintStmt(expr)

    def expression_statement(self) -> ExpressionStmt:
        expr = self.expression()
        # optional semicolon
        if self.match(TokenType.SEMICOLON):
            pass
        return ExpressionStmt(expr)

    def block(self) -> List[Stmt]:
        statements: List[Stmt] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def if_statement(self) -> IfStmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()

        return IfStmt(condition, then_branch, else_branch)

    def while_statement(self) -> WhileStmt:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        body = self.statement()
        return WhileStmt(condition, body)

    def for_statement(self) -> Stmt:
        # for ( initializer ; condition ; increment ) body
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        # initializer
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        # condition
        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        # increment
        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self.statement()

        # desugar for-loop to while-loop
        if increment is not None:
            body = BlockStmt([body, ExpressionStmt(increment)])

        if condition is None:
            condition = Literal(True)

        body = WhileStmt(condition, body)

        if initializer is not None:
            body = BlockStmt([initializer, body])

        return body

    def function_declaration(self) -> Stmt:
        name = self.consume(TokenType.IDENTIFIER, "Expect function name.")
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after function name.")
        params: List[Token] = []
        if not self.check(TokenType.RIGHT_PAREN):
            params.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))
            while self.match(TokenType.COMMA):
                params.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before function body.")
        body: List[Stmt] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            body.append(self.declaration())
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after function body.")
        return FunctionStmt(name, params, body)

    def return_statement(self) -> Stmt:
        value = None
        if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RIGHT_BRACE):
            value = self.expression()
        if self.match(TokenType.SEMICOLON):
            pass
        return Return(value)

    # --- Expressions ---
    def expression(self) -> Expr:
        return self.assignment()

    def assignment(self) -> Expr:
        expr = self.equality()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, Variable):
                name = expr.name
                return Assign(name, value)

            raise Exception(f"Invalid assignment target at line {equals.line}")

        return expr

    def equality(self) -> Expr:
        expr = self.comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)

        return expr

    def comparison(self) -> Expr:
        expr = self.term()

        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                        TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)

        return expr

    def term(self) -> Expr:
        expr = self.factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)

        return expr

    def factor(self) -> Expr:
        expr = self.unary()

        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)

        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.call()

    def call(self) -> Expr:
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                # parse arguments
                args: List[Expr] = []
                if not self.check(TokenType.RIGHT_PAREN):
                    args.append(self.expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.expression())

                self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
                expr = Call(expr, args)
                continue

            if self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = Get(expr, name)
                continue

            break

        return expr

    def primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            return Literal(False)
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.NIL):
            return Literal(None)

        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)

        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise Exception(f"Expected expression at line {self.peek().line}")

    # --- Utility parsing helpers ---
    def match(self, *types: TokenType) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def check(self, type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def consume(self, type: TokenType, message: str) -> Token:
        if self.check(type):
            return self.advance()

        raise Exception(f"{message} at line {self.peek().line}")