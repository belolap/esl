__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(C) 2010 Business group of development management'
__licence__ = 'GPL'

from unittest import TestCase

from ..interpreter import Interpreter, ESLRuntimeError
from ..parse import ESLParser
from ..context import Context


class InterpreterTest(TestCase):

    def setUp(self):
        self.parser = ESLParser()
        self.interpreter = Interpreter()

    def runCode(self, code):
        bytecode = self.parser.parse(code)
        return self.interpreter.run(bytecode)

    def testBoolConstants(self):
        '''ESL: interpretate bool constants'''
        self.assertEqual(self.runCode('true;'), True)
        self.assertEqual(self.runCode('false;'), False)
        self.assertEqual(self.runCode('null;'), None)

    def testBinaryExpressions(self):
        '''ESL: interpretate binary expressions'''
        self.assertEqual(self.runCode('5 + 4;'), 9)
        self.assertEqual(self.runCode('5 + 4 * 3;'), 17)
        self.assertEqual(self.runCode('(5 + 4) * 3;'), 27)
        self.assertEqual(self.runCode('4 / 2 + 5;'), 7)

    def testDot(self):
        '''ESL: interpretate access to object attributes via dot'''
        # setup object
        class A(object):
            pass
        a = A()
        a.b = "c"
        bytecode = self.parser.parse("a.b;")
        ctx = Context()
        ctx.addGlobal("a", a)
        self.assertEqual(bytecode.touch(ctx), 'c');

    def testValiables(self):
        '''ESL: interpretate variables assignment'''
        self.assertRaises(ESLRuntimeError, self.runCode, 'a + 1;')
        self.assertEqual(self.runCode('a = 5; a;'), 5)
        self.assertEqual(self.runCode('a = 5 + 6; a;'), 11)
        self.assertRaises(ESLRuntimeError, self.runCode, 'a += 1;')
        self.assertEqual(self.runCode('a = 5; a += 6; a;'), 11)
        self.assertEqual(self.runCode('a = 5; a -= 6; a;'), -1)
        self.assertEqual(self.runCode('a = 5; a++; a;'), 6)
        self.assertEqual(self.runCode('a = 6; a--; a;'), 5)

    def testAttributesAssignment(self):
        '''ESL: interpretate attributes assignment'''
        class A(object):
            pass
        a = A()
        a.b = "c"
        bytecode = self.parser.parse('a.b = "d"; a.b;')
        ctx = Context()
        ctx.addGlobal("a", a)
        self.assertEqual(bytecode.touch(ctx), "d")

    def testArray(self):
        '''ESL: interpretate arrays and its elements'''
        self.assertEqual(self.runCode('a = [1, 2, "3"]; a;'), [1, 2, "3"])
        self.assertEqual(self.runCode('a = {"a": 1, "b": 2, 3: 3}; a;'), {"a": 1, "b": 2, 3: 3})
        self.assertEqual(self.runCode('a = [1, 2, "3"]; a[2];'), "3")
        self.assertEqual(self.runCode('a = {"a": 1, "b": 2, 3: 3}; a["b"];'), 2)
        self.assertEqual(self.runCode('a = {"a": 1}; a["a"] = 4; a["a"];'), 4)
        self.assertEqual(self.runCode('a = [9,8,7,6]; a[1+2] = 4; a[3];'), 4)

    def testUnaryExpressions(self):
        '''ESL: interpretate unary expressions'''
        self.assertEqual(self.runCode('-5;'), -5)
        self.assertEqual(self.runCode('a = -5; -a;'), 5)
        self.assertEqual(self.runCode('a = -(5 + 1); -a;'), 6)

    def testLogicalExpressions(self):
        '''ESL: interpretate logical expressions'''
        self.assertEqual(self.runCode('1 and 4;'), 4)
        self.assertEqual(self.runCode('1 - 1 and 4 or 5;'), 5)
        self.assertEqual(self.runCode('not 5;'), False)

    def testRelativeExpressions(self):
        '''ESL: interpretate equal and relative expressions'''
        self.assertEqual(self.runCode('5 == 5;'), True)
        self.assertEqual(self.runCode('5 != 5;'), False)
        self.assertEqual(self.runCode('5 >= 5;'), True)
        self.assertEqual(self.runCode('5 >= 6;'), False)
        self.assertEqual(self.runCode('6 >= 5;'), True)
        self.assertEqual(self.runCode('6 <= 5;'), False)
        self.assertEqual(self.runCode('5 < 5;'), False)

    def testIfStatement(self):
        '''ESL: interpretate if-elif-else statement'''
        code = """\
            a = 1;
            b = 0;
            if (a == 1) {
                b = 1;
            }
            b;
        """
        self.assertEqual(self.runCode(code), 1)

        code = """\
            a = 3;
            b = 0;
            if (a == 1) {
                b = 1;
            }
            elif (a == 2) {
                b = 2;
            }
            elif (a == 3) {
                b = 3;
            }
            b;
        """
        self.assertEqual(self.runCode(code), 3)

        code = """\
            a = 4;
            b = 0;
            if (a == 1) {
                b = 1;
            }
            elif (a == 2) {
                b = 2;
            }
            elif (a == 3) {
                b = 3;
            }
            else {
                b = 4;
            }
            b;
        """
        self.assertEqual(self.runCode(code), 4)

        code = """\
            if (a = 1) {b = 1;}
        """
        self.assertRaises(SyntaxError, self.runCode, code)

    def testSpecialIfAndUnless(self):
        '''ESL: interpretate special if and unless'''
        code = """\
            b = 1;
            a = 5 if (b == 1);
            a;
        """
        self.assertEqual(self.runCode(code), 5)

        code = """\
            b = 1;
            a = 2;
            a = 5 if (b == 2);
            a;
        """
        self.assertEqual(self.runCode(code), 2)

        code = """\
            b = 1;
            a = 2;
            a = 5 unless (b == 2);
            a;
        """
        self.assertEqual(self.runCode(code), 5)
        code = """\
            b = 1;
            a = 2;
            a = 5 unless (b == 1);
            a;
        """
        self.assertEqual(self.runCode(code), 2)

    def testForStatement(self):
        '''ESL: interpretate for (expr; expr; expr) {...} statement'''
        code = """\
            a = 0;
            for (i = 0; i < 5; i++) {
                a++;
            }
            a;
        """
        self.assertEqual(self.runCode(code), 5)

        code = """\
            a = 0;
            for (i = 0; i < 5; i++) {
                for (j = 0; j < 5; j++) {
                    a++;
                }
            }
            a;
        """
        self.assertEqual(self.runCode(code), 25)

    def testForIn(self):
        '''ESL: interpretate for..in statement'''
        code = """\
            a = [1, 2, 3, 4, 5];
            b = 0;
            for (i in a) {
                b += i;
            }
            b;
        """
        self.assertEqual(self.runCode(code), 15)

    def testWhileLoop(self):
        '''ESL: interpretate while loop'''
        code = """\
            count = 5;
            result = 0;
            while (count > 0) {
                result += count;
                count --;
            }
            result;
        """
        self.assertEqual(self.runCode(code), 15)

    def testBreakStatement(self):
        '''ESL: interpretate break statement'''
        code = """\
            a = 0;
            for (i = 0; i < 10; i++) {
                break;
                a += 1000;
            }
            a;
        """

        self.assertEqual(self.runCode(code), 0)
        code = """\
            a = 0;
            for (i = 0; i < 10; i++) {
                if (a > 5) {
                    break;
                    a += 1000;
                }
                a++;
            }
            a;
        """
        self.assertEqual(self.runCode(code), 6)

        code = """\
            a = 0;
            for (i = 0; i < 10; i++) {
                for (j = 0; j < 2; j++) {
                    break;
                    a += 1000;
                }
                a++;
            }
            a;
        """
        self.assertEqual(self.runCode(code), 10)

        # TODO: test for..in break statement
        # TODO: test while break statement

    def testContinueStatement(self):
        '''ESL: interpretate continue statement'''
        code = """\
            a = 0;
            for (i = 0; i < 5; i++) {
                a++;
                continue;
                a += 1000;
            }
            a;
        """
        self.assertEqual(self.runCode(code), 5)

        code = """\
            a = 0;
            for (i = 0; i < 5; i++) {
                for (j = 0; j < 5; j++) {
                    a++;
                    continue;
                    a += 1000;
                }
            }
            a;
        """
        self.assertEqual(self.runCode(code), 25)
        # TODO: test for..in continue statement
        # TODO: test while continue statement

    def testFunction(self):
        '''ESL: interpretate function'''
        funcode = """\
            function summishe(a, b, c, d) {
                return a + b + c + d;
            }
        """
        self.assertEqual(self.runCode(funcode + "summishe(1, 5, 3, 1);"), 10)

        def func(a, b):
            return a + b
        ctx = Context({'func': func})
        bytecode = self.parser.parse("return func(1, 3);")
        self.assertEqual(bytecode.touch(ctx), 4);

    def testFunctionParameters(self):
        '''ESL: interpretate function parameters'''
        funcode = """\
            function summishe(a, b, c, d) {
                return a + b + c + d;
            }
        """
        code = funcode + """summishe(1, b=5, 6);"""
        self.assertRaises(ESLRuntimeError, self.runCode, code)
        code = funcode + """summishe(1, 2, 3);"""
        self.assertRaises(ESLRuntimeError, self.runCode, code)
        code = funcode + """summishe(1, 2, 3, 4, 5);"""
        self.assertRaises(ESLRuntimeError, self.runCode, code)
        code = funcode + """summishe(1, 2, 3, 4, d=5);"""
        self.assertRaises(ESLRuntimeError, self.runCode, code)
        code = funcode + """summishe(1, 2, 3, 4, m=5);"""
        self.assertRaises(ESLRuntimeError, self.runCode, code)

    def testFunctionWithoutParameters(self):
        '''ESL: interpretate function without parameters'''
        code = """\
            function summishe() {
                return 2;
            }
            return summishe();
        """
        self.assertEqual(2, self.runCode(code));

    def testFunctionNamespace(self):
        '''ESL: interpretate function namespaces'''
        code = """\
            a = 2;
            function sum(a, b) {
                a = 5;
            }
            sum(4, 6);
            return a;
        """
        self.assertEqual(self.runCode(code), 2)

        code = """\
            a = 2;
            function sum(b, c) {
                a = 5;
            }
            sum(4, 6);
            return a;
        """
        self.assertEqual(self.runCode(code), 2)

        code = """\
            a = {"a": 2};
            function sum(b, c) {
                a["a"] = 5;
            }
            sum(4, 6);
            return a["a"];
        """
        self.assertEqual(self.runCode(code), 5)

    def testReturnStatement(self):
        '''ESL: interpretate return statement'''
        code = """\
            function sumstr(b, c, d) {
                return b + c + d;
                return b + c;
            }
            result = sumstr("a1", "b5", d="d6");
            return result;
            return 2;
        """
        self.assertEqual(self.runCode(code), "a1b5d6")

        code = """\
            a = 1;
            if (a == 1) {
                return 2;
            }
            return 3;
        """
        self.assertEqual(self.runCode(code), 2)

        code = """return 1;"""
        self.assertEqual(self.runCode(code), 1)

    def testEmptyBraces(self):
        """ESL: interpretate empty braces"""
        code = """{}"""
        self.assertRaises(SyntaxError, self.runCode, code)
        code = """{a = 1;}"""
        self.assertRaises(SyntaxError, self.runCode, code)

    def testImport(self):
        '''ESL: interpretate import module'''
        def return_imported(code):
            return """\
                a = 5;
            """

        code = """\
            a = 1;
            import change;
            return a;
        """
        ctx = Context()
        ctx.setImportHandler(return_imported)
        bytecode = self.parser.parse(code)
        self.assertEqual(bytecode.touch(ctx), 5);
