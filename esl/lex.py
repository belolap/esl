__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(C) 2010 Business group of development management'
__licence__ = 'GPL'

from ply.lex import lex

class ESLLex(object):

    reserved = (
        'TRUE',
        'FALSE',
        'NULL',
        'NOT',
        'AND',
        'OR',
        'IF',
        'ELIF',
        'ELSE',
        'UNLESS',
        'FOR',
        'IN',
        'WHILE',
        'CONTINUE',
        'BREAK',
        'FUNCTION',
        'RETURN',
        'IMPORT',
        )
    reserved_words = {}
    for k in reserved:
        reserved_words[k.lower()] = k

    tokens = reserved + (
                # Characters . , : ;
                'DOT',
                'COMMA',
                'COLON',
                'SEMICOLON',

                # Brackets: ( ) [ ] { }
                'LPAREN',
                'RPAREN',
                'LBRACKET',
                'RBRACKET',
                'LBRACE',
                'RBRACE',

                # Assigment: =
                'ASSIGN',

                # Comparsion: > < == != >= <=
                'GREATER',
                'LESS',
                'EQUAL',
                'NOT_EQUAL',
                'GREATER_EQUAL',
                'LESS_EQUAL',

                # Doubles: ++ --
                'DOUBLE_PLUS',
                'DOUBLE_MINUS',

                # Operators: + - * /
                'PLUS',
                'MINUS',
                'TIMES',

                'DIVIDE',

                # Assign with operators += -= *= /=
                'EQ_PLUS',
                'EQ_MINUS',

                # Others
                'ID',
                'INTEGER',
                'DECIMAL',
                'STRING',

            )

    # Characters . , : ;
    t_DOT           = r'\.'
    t_COMMA         = r','
    t_COLON         = r':'
    t_SEMICOLON     = r';'

    # Brackets: ( ) [ ] { }
    t_LPAREN        = r'\('
    t_RPAREN        = r'\)'
    t_LBRACKET      = r'\['
    t_RBRACKET      = r'\]'
    t_LBRACE        = r'\{'
    t_RBRACE        = r'\}'

        # Assigment: =
    t_ASSIGN        = r'='

        # Comparsion: > < == != >= <=
    t_GREATER       = r'>'
    t_LESS          = r'<'
    t_EQUAL         = r'=='
    t_NOT_EQUAL     = r'!='
    t_GREATER_EQUAL = r'>='
    t_LESS_EQUAL    = r'<='

    # Doubles: ++ --
    t_DOUBLE_PLUS   = r'\+\+'
    t_DOUBLE_MINUS  = r'--'

    # Operators: + - * /
    t_PLUS          = r'\+'
    t_MINUS         = r'-'
    t_TIMES         = r'\*'
    t_DIVIDE        = r'/'

    # Assign with operators += -= *= /=
    t_EQ_PLUS       = r'\+='
    t_EQ_MINUS      = r'-='

    # Others
    def t_ID(self, t):
        r'[A-Za-z_][\w_]*'
        if t.value in self.reserved_words:
            t.type = self.reserved_words[t.value]
        return t

    t_INTEGER       = r'\d+'
    t_DECIMAL       = r'\d*\.\d+'
    t_STRING        = r'".*?"'

    # Ignored symbols
    t_ignore  = ' \t'

    # Comments
    def t_COMMENT1(self, t):
        r'/\*[\w\W]*?\*/'
        t.lexer.lineno += t.value.count('\n')

    def t_COMMENT2(self, t):
        r'//[^\n]*'

    # New lines
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        t.lexer.startpos = t.lexer.lexpos

    # Errors handle
    def error_msg(self, msg, line, pos, value):
        return '%s at line %s, position %s, statement `%s\'.' % (msg, line, pos, value)

    def t_error(self, t):
        startpos = getattr(t.lexer, 'startpos', 1)
        column = t.lexpos - startpos + 1
        raise SyntaxError(self.error_msg('can\'t parse', t.lineno, column,
            t.value[0]))

    # Build lexer
    def build(self):
        self.lexer = lex(module=self)
