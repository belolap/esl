#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

import ply.lex
import collections


class LexError(Exception):
    pass


class Lexer(object):

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

    def t_error(self, t):
        #XXX: rewrite
        msg = ('Illegal character `{}\' '
               'at line {}'.format(t.value[0], t.lexer.lineno))
        raise LexError(msg)

    def build(self, **kwargs):
        self.lexer = ply.lex.lex(module=self, **kwargs)
