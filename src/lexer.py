from enum import Enum, auto

class TokenType(Enum):
    # Keywords
    DEF = auto()
    CLASS = auto()
    IF = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    RETURN = auto()
    # Statements / control
    PRINT = auto()
    VAR = auto()
    FOR = auto()
    WHILE = auto()
    BREAK = auto()
    CONTINUE = auto()
    IMPORT = auto()
    
    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    
    # Delimiters
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    SEMICOLON = auto()
    
    # End of file
    EOF = auto()

class Token:
    def __init__(self, type: TokenType, lexeme: str, literal: object, line: int):
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __str__(self):
        return f"{self.type} {self.lexeme} {self.literal}"

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        
        self.keywords = {
            "def": TokenType.DEF,
            "class": TokenType.CLASS,
            "if": TokenType.IF,
            "else": TokenType.ELSE,
            "true": TokenType.TRUE,
            "false": TokenType.FALSE,
            "nil": TokenType.NIL,
            "return": TokenType.RETURN
        }
        # Add control/statement keywords
        self.keywords.update({
            "print": TokenType.PRINT,
            "var": TokenType.VAR,
            "for": TokenType.FOR,
            "while": TokenType.WHILE,
            "break": TokenType.BREAK,
            "continue": TokenType.CONTINUE,
            "import": TokenType.IMPORT,
        })

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
            
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def scan_token(self):
        c = self.advance()
        
        if c.isspace():
            if c == '\n':
                self.line += 1
            return
            
        if c.isalpha() or c == '_':
            self.identifier()
            return
            
        if c.isdigit():
            self.number()
            return
            
        if c == '"':
            self.string()
            return
            
        # Handle operators and delimiters
        if c == '(':
            self.add_token(TokenType.LEFT_PAREN)
        elif c == ')':
            self.add_token(TokenType.RIGHT_PAREN)
        elif c == '{':
            self.add_token(TokenType.LEFT_BRACE)
        elif c == '}':
            self.add_token(TokenType.RIGHT_BRACE)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == '.':
            self.add_token(TokenType.DOT)
        elif c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == '+':
            self.add_token(TokenType.PLUS)
        elif c == '-':
            self.add_token(TokenType.MINUS)
        elif c == '*':
            self.add_token(TokenType.STAR)
        elif c == '/':
            self.add_token(TokenType.SLASH)
        elif c == '=':
            self.add_token(TokenType.EQUAL_EQUAL if self.match('=') else TokenType.EQUAL)
        elif c == '!':
            self.add_token(TokenType.BANG_EQUAL if self.match('=') else TokenType.BANG)
        elif c == '<':
            self.add_token(TokenType.LESS_EQUAL if self.match('=') else TokenType.LESS)
        elif c == '>':
            self.add_token(TokenType.GREATER_EQUAL if self.match('=') else TokenType.GREATER)
        else:
            raise Exception(f"Unexpected character at line {self.line}")

    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
            
        text = self.source[self.start:self.current]
        type = self.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(type)

    def number(self):
        while self.peek().isdigit():
            self.advance()
            
        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
                
        self.add_token(TokenType.NUMBER, float(self.source[self.start:self.current]))

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()
            
        if self.is_at_end():
            raise Exception(f"Unterminated string at line {self.line}")
            
        self.advance()  # Closing quote
        
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)

    def match(self, expected: str) -> bool:
        if self.is_at_end() or self.source[self.current] != expected:
            return False
            
        self.current += 1
        return True

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        return char

    def add_token(self, type: TokenType, literal: object = None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type, text, literal, self.line))