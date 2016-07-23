__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(C) 2010 Business group of development management'
__licence__ = 'GPL'

from unittest import TestCase

from edera.esl.lex import ESLLex


class SyntaxTest(TestCase):
    def setUp(self):
        esllexer = ESLLex()
        esllexer.build()
        self.lexer = esllexer.lexer

    def testComments(self):
        '''ESL: syntax of comments'''
        code = """\
        /* This is test
         * of some
         * comment
         */
        """
        self.lexer.input(code)
        code = """\
        // One string comment
        """
        self.lexer.input(code)

    def testSimpleNumbers(self):
        '''ESL: syntax of simple numbers'''
        self.lexer.input('1045')

    def testBoolConstantsAndNone(self):
        '''ESL: syntax bool constants and none'''
        self.lexer.input('true')
        self.lexer.input('false')
        self.lexer.input('none')

    def testBinaryExpression(self):
        '''ESL: syntax of binary expressions'''
        self.lexer.input('4 + 5 * 3 / 4 - 7')

    def testVariableAssignement(self):
        '''ESL: syntax of variable assign'''
        self.lexer.input('a = 5')
        self.lexer.input('a = 5 + 1')
        self.lexer.input('a++')
        self.lexer.input('a--')

    def testRoundBrakets(self):
        '''ESL: syntax of round brakets'''
        self.lexer.input('(4 + 5)')
        self.lexer.input('4 + (5 + 2)')
        self.lexer.input('(4 + 5) * 2')
        self.lexer.input('b = 5 / (4 + 5) * 2')

    def testIfStatement(self):
        '''ESL: syntax of if statement'''
        self.lexer.input('if (a == 1) { b = 5; }')
        self.lexer.input('if (a == 1) { b = 5; } elif (c == 7) { z = 1;} else { r = 5 };')
        multiline = """\
            if (a == 1) {
                b = 5;
            }
            elif (a == 2) {
                b = 6;
            }
            else {
                b = 7;
            }
        """
        self.lexer.input(multiline)
