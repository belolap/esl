__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(C) 2010 Business group of development management'
__licence__ = 'GPL'

from decimal import Decimal
from unittest import TestCase

from edera.esl.parse import ESLParser


class TestParse(TestCase):
    def setUp(self):
        self.parser = ESLParser()

    def assertPairs(self, pairs):
        for pair in pairs:
            result = str(self.parser.parse(pair[0]))
            self.assertEqual(result, pair[1])

    def testComments(self):
        '''ESL: parse of comments style /* ... */'''
        code = """\
        /* This is test
         * of some
         * comment
         */
        """
        self.assertEqual(self.parser.parse(code), '')


    def testSimpleType(self):
        '''ESL: parse simple type'''
        pairs = (
                ('5;', '5;'),
                ('5.0;', '5.0;'),
                ('"5";', '"5";'),
                )
        self.assertPairs(pairs)
        self.assertEqual(type(self.parser.parse('5.0;')[0].expression.value), Decimal)

    def testBoolConstantsAndNone(self):
        '''ESL: parse bool constants and none'''
        pairs = (
                ('true;', 'true;'),
                ('false;', 'false;'),
                ('null;', 'null;'),
                )
        self.assertPairs(pairs)

    def testIds(self):
        '''ESL: parse id and attributes'''
        pairs = (
                ('s;', 's;'),
                ('a.b.c.d;', 'a.b.c.d;'),
                )
        self.assertPairs(pairs)

    def testDot(self):
        '''ESL: parse access to object attributes via dot'''
        pairs = (
                ('s.b;', 's.b;'),
                ('s.b.c;', 's.b.c;'),
                )
        self.assertPairs(pairs)

    def testVariableAssignment(self):
        '''ESL: parse variable assignment'''
        pairs = (
                ('a = 1;', '(a = 1);'),
                ('a += 1;', '(a += 1);'),
                ('a -= 1;', '(a -= 1);'),
                ('a++;', '(a++);'),
                ('a--;', '(a--);'),
                )
        self.assertPairs(pairs)

    def testArray(self):
        '''ESL: parse arrays, hashes and its elements'''
        pairs = (
                ('a = [];', '(a = []);'),
                ('a = [1, 2, 3];', '(a = [1, 2, 3]);'),
                ('a = {"a": 1, "b": 2, 4: 3};', '(a = {"a": 1, "b": 2, 4: 3});'),
                ('b = a[0];', '(b = a[0]);'),
                ('b = a["0"];', '(b = a["0"]);'),
                ('b = a[1 + 1];', '(b = a[(1 + 1)]);'),
                )
        self.assertPairs(pairs)

    def testBinaryExpressions(self):
        '''ESL: parse binary expressions'''
        pairs = (
                ('a = 5 + 1;', '(a = (5 + 1));'),
                ('4 + 1;', '(4 + 1);'),
                ('5 + 4 + 5;', '((5 + 4) + 5);'),
                ('5 + 4 * 5;', '(5 + (4 * 5));'),
                ('5 * 4 + 5;', '((5 * 4) + 5);'),
                ('b = 15 - 4 * 5 + 7 - 4 / 7;', '(b = (((15 - (4 * 5)) + 7) - (4 / 7)));'),
                )
        self.assertPairs(pairs)

    def testBrakets(self):
        '''ESL: parse brakets'''
        pairs = (
                ('a = (5 + 1);', '(a = (5 + 1));'),
                ('5 + (4 + 5);', '(5 + (4 + 5));'),
                ('(5 + 4) * 5;', '((5 + 4) * 5);'),
                ('b = (15 - 4) * (5 + 7) - 4 / 7;', '(b = (((15 - 4) * (5 + 7)) - (4 / 7)));'),
                )
        self.assertPairs(pairs)

    def testLogicalExpressions(self):
        '''ESL: parse logical expressions'''
        pairs = (
                ('a and b;', '(a and b);'),
                ('a and (5 + 4);', '(a and (5 + 4));'),
                ('a and 5 + 4;', '(a and (5 + 4));'),
                ('not 7;', '(not 7);'),
                ('not 5 == 5 and 6 != 7;', '(((not 5) == 5) and (6 != 7));'),
                ('not (5 < 6 or 7 >= 9 and 6);', '(not ((5 < 6) or ((7 >= 9) and 6)));'),
                )
        self.assertPairs(pairs)

    def testUnaryOPerators(self):
        '''ESL: parse unary expressions'''
        pairs = (
                ('not a;', '(not a);'),
                ('-a;', '(- a);'),
                )
        self.assertPairs(pairs)

    def testIfElifElseStatement(self):
        '''ESL: parse if-elif-else statement'''
        pairs = (
                ('if (a == 1) {b = 5;}',
                            'if ((a == 1)) {(b = 5);}'),
                ('if (a == 1) {b = 5;} else {c = 6;}',
                            'if ((a == 1)) {(b = 5);} else {(c = 6);}'),
                ('if (a == 1) {b = 5;} elif (a == 2) {c = 6;}',
                            'if ((a == 1)) {(b = 5);} elif ((a == 2)) {(c = 6);}'),
                ('if (a == 1) {b = 5;} elif (a == 2) {c = 6;} elif (a == 3) {c = 7;}',
                            'if ((a == 1)) {(b = 5);} elif ((a == 2)) {(c = 6);} elif ((a == 3)) {(c = 7);}'),
                ('if (a == 1) {b = 5;} elif (a == 2) {b = 6;} elif (a == 3) {b = 7;} else {b = 8;}',
                            'if ((a == 1)) {(b = 5);} elif ((a == 2)) {(b = 6);} elif ((a == 3)) {(b = 7);} else {(b = 8);}'),
                ('if (a == 1) {b = 5; b = 8;}',
                            'if ((a == 1)) {(b = 5); (b = 8);}'),
                )
        self.assertPairs(pairs)

    def testSpecialIfAndUnless(self):
        '''ESL: parse special if and unless'''
        pairs = (
                ('a = 1 if (true);',
                            '(a = 1) if (true);'),
                ('b = 4 + 5 * 4 unless (b == 5 + 4);',
                            '(b = (4 + (5 * 4))) unless ((b == (5 + 4)));'),
                )
        self.assertPairs(pairs)

    def testForStatement(self):
        '''ESL: parse for (expr; expr; expr) {...} statement'''
        pairs = (
                ('for (a = 1; a < 5; a++) {b = 1;}',
                            'for ((a = 1); (a < 5); (a++)) {(b = 1);}'),
                ('for (a = 1; a < 5; a++) {break;}',
                            'for ((a = 1); (a < 5); (a++)) {break;}'),
                ('for (a = 1; a < 5; a++) {continue;}',
                            'for ((a = 1); (a < 5); (a++)) {continue;}'),
                ('for (a = 1; a < 5; a++) {a = 1; continue;}',
                            'for ((a = 1); (a < 5); (a++)) {(a = 1); continue;}'),
                ('for (a = 1; a < 5; a++) {a = 1; break; b = 2;}',
                            'for ((a = 1); (a < 5); (a++)) {(a = 1); break; (b = 2);}'),
                ('for (a = 1; a < 5; a++) {break; b = 2;}',
                            'for ((a = 1); (a < 5); (a++)) {break; (b = 2);}'),
                )
        self.assertPairs(pairs)

    def testForIn(self):
        '''ESL: parse for..in statement'''
        pairs = (
                ('for (a in b) { c = a; }',
                            'for (a in b) {(c = a);}'),
                )
        self.assertPairs(pairs)

    def testWhileLoop(self):
        '''ESL: parse while loop'''
        pairs = (
                ('while (b == a + 1) {c = 1;}',
                            'while ((b == (a + 1))) {(c = 1);}'),
                )
        self.assertPairs(pairs)

    def testFunction(self):
        '''ESL: parse function'''
        pairs = (
                ('function a() {d=1;}',
                            'function a () {(d = 1);}'),
                ('function a(b, c) {d=1;}',
                            'function a (b, c) {(d = 1);}'),
                ('function a(b, c) {d=1; return d;}',
                            'function a (b, c) {(d = 1); return d;}'),
                ('test_function(a);',
                            'test_function(a);'),
                ('test_function(a, b+1);',
                            'test_function(a, (b + 1));'),
                ('call();',
                            'call();'),
                ('call(a, b);',
                            'call(a, b);'),
                ('a.call(a, b);',
                            'a.call(a, b);'),
                )
        self.assertPairs(pairs)

    def testImport(self):
        '''ESL: parse import module'''
        pairs = (
                ('import modulename;',
                            'import modulename;'),
                )
        self.assertPairs(pairs)
