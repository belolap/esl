#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

import ply.lex
import collections


class LexError(Exception):
    pass


class Lexer(object):

    states = (
        ('ccode', 'exclusive'),
    )

    keywords = collections.OrderedDict([
        ('do', 'DO'),
        ('while', 'WHILE'),
        ('for', 'FOR'),
        ('until', 'UNTIL'),
        ('repeat', 'REPEAT'),
        ('end', 'END'),
        ('in', 'IN'),

        ('if', 'IF'),
        ('then', 'THEN'),
        ('elseif', 'ELSEIF'),
        ('else', 'ELSE'),

        ('local', 'LOCAL'),

        ('function', 'FUNCTION'),
        ('return', 'RETURN'),
        ('break', 'BREAK'),

        ('nil', 'NIL'),
        ('false', 'FALSE'),
        ('true', 'TRUE'),

        ('and', 'AND'),
        ('or', 'OR'),
        ('not', 'NOT'),
    ])

    tokens = tuple(keywords.values()) + (
        'NUMBER',
        'STRING',
        'TDOT',
        'NAME',

        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'POWER',
        'MODULO',

        'EQUALS',
        'LESS_THEN',
        'MORE_THEN',
        'LESS_EQUAL_THEN',
        'MORE_EQUAL_THEN',
        'TILDE_EQUAL',

        'SQUARE',

        'APPEND',

        'ASSIGN',
        'DOT',
        'COLON',
        'COMMA',
        'SEMICOLON',

        'BRACES_L',
        'BRACES_R',

        'BRACKET_L',
        'BRACKET_R',

        'PARANTHESES_L',
        'PARANTHESES_R',
    )

    t_NUMBER          = r'\d+'
    t_STRING          = r'"[^\\"]*"' # r'".*?"|\'.*?\''
    t_TDOT            = r'\.\.\.'

    def t_NAME(self, t):
        r'[A-Za-z][A-Za-z0-9_]*'
        if t.value in self.keywords:
            t.type = self.keywords[t.value]
        return t

    t_PLUS            = r'\+'
    t_MINUS           = r'-'
    t_TIMES           = r'\*'
    t_DIVIDE          = r'/'
    t_POWER           = r'\^'
    t_MODULO          = r'%'

    t_EQUALS          = r'=='
    t_LESS_THEN       = r'<'
    t_MORE_THEN       = r'>'
    t_LESS_EQUAL_THEN = r'<='
    t_MORE_EQUAL_THEN = r'>='
    t_TILDE_EQUAL     = r'~='

    t_SQUARE          = r'\#'

    t_APPEND          = r'\.\.'

    t_ASSIGN          = r'='
    t_DOT             = r'\.'
    t_COLON           = r':'
    t_COMMA           = r','
    t_SEMICOLON       = r';'

    t_BRACES_L        = r'\{'
    t_BRACES_R        = r'\}'

    t_BRACKET_L       = r'\['
    t_BRACKET_R       = r'\]'

    t_PARANTHESES_L   = r'\('
    t_PARANTHESES_R   = r'\)'

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        t.lexer.startpos = t.lexer.lexpos

    t_ignore = ' \t'

    def t_COMMENTS(self, t):
        r'--(?!\[=*\[).*'

    def t_ccode(self, t):
        r'(?:--)?\[=*\['
        t.lexer.start_pos = t.lexer.lexpos
        if t.value.startswith('--'):
            t.lexer.is_comment = True
        else:
            t.lexer.is_comment = False
        t.lexer.level = t.value.count('=')
        t.lexer.begin('ccode')

    def t_ccode_newlone(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_ccode_end(self, t):
        r'\]=*\]'
        if t.value.count('=') == t.lexer.level:
            t.lexer.begin('INITIAL')
            t.lexer.lineno += t.value.count('\n')
            if not t.lexer.is_comment:
                t.value = t.lexer.lexdata[t.lexer.start_pos-1:t.lexer.lexpos-1]
                t.type = 'STRING'
                return t

    t_ccode_ignore = ''

    def t_ccode_error(self, t):
        t.lexer.skip(1)

    def t_error(self, t):
        msg = ('Illegal character `{}\' '
               'at line {}'.format(t.value[0], t.lexer.lineno))
        raise LexError(msg)

    def build(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
