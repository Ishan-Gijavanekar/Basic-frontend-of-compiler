import re

class Lexer:
    TOKEN_SPECIFICATION = [
        ('PREPROCESSOR', r'#.*'),     
        ('STRING',     r'".*?"'),
        ('FORMAT',     r'%[dfcs]'),
        ('KEYWORD',    r'\b(int|float|char|return|if|else|while|for|void|print)\b'),
        ('IDENTIFIER', r'\b[_a-zA-Z][_a-zA-Z0-9]*\b'),
        ('NUMBER',     r'\b\d+(\.\d+)?\b'),
        ('OPERATOR',   r'[+\-*/=<>!&|\%]+'),
        ('DELIMITER',  r'[(){},;]'),
        ('SKIP',       r'[ \t]+'),
        ('NEWLINE',    r'\n'),
        ('MISMATCH',   r'.'),
    ]

    def __init__(self):
        token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.TOKEN_SPECIFICATION)
        self.get_token = re.compile(token_regex).match

    def tokenize(self, line):
        pos = 0
        tokens = []
        while pos < len(line):
            match = self.get_token(line, pos)
            if not match:
                raise SyntaxError(f'Unexpected character: {line[pos]}')
            kind = match.lastgroup
            value = match.group()
            if kind in ('SKIP', 'NEWLINE'):
                pass
            elif kind == 'MISMATCH':
                raise SyntaxError(f'Illegal token: {value}')
            else:
                tokens.append((kind, value))
            pos = match.end()
        return tokens
