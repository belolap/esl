__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

import decimal
import tornado.testing

from .. import lex
from .. import parse
from .. import context
from .. import interpreter


class TestInterpreter(tornado.testing.AsyncTestCase):

    def setUp(self):
        super().setUp()
        self.parser = parse.Parser(debug=False)
        self.interpreter = interpreter.Interpreter()

    async def run_code(self, code, ctx=None):
        bytecode = self.parser.parse(code)
        result = await self.interpreter.run(bytecode, ctx)
        return result

    async def assert_code(self, template, code, ctx=None):
        result = await self.run_code(code, ctx)
        if isinstance(result, interpreter.AttrDict):
            result = dict([(k, v) for k, v in result.items()])
        self.assertEqual(template, result)

    async def assert_raises(self, exc, code, ctx=None):
        try:
            result = await self.run_code(code, ctx)
        except exc as e:
            pass
        else:
            self.fail('Exception {} does not raised'.format(exc.__name__))

    @tornado.testing.gen_test
    def test_constants(self):
        '''ESL: interpretate constants'''
        yield self.assert_code(1, '1;')
        yield self.assert_code(100, '100;')
        yield self.assert_code(decimal.Decimal('100.35'), '100.35;')
        yield self.assert_code('abc', '"abc";')
        yield self.assert_code('abc', '\'abc\';')
        yield self.assert_code('"abc"', '\'"abc"\';')
        yield self.assert_code(True,  'true;')
        yield self.assert_code(False, 'false;')
        yield self.assert_code(None,  'null;')

    @tornado.testing.gen_test
    def test_id(self):
        '''ESL: interpretate ids'''
        ctx = context.Context()
        ctx.set('a', 1)
        yield self.assert_code(1,  'a;', ctx)

    @tornado.testing.gen_test
    def test_dot(self):
        '''ESL: interpretate access to object attributes via dot'''
        class A(object):
            def __init__(self, value, child=None):
                self._x = 'denied'
                self.x = value
                self.s = child
        ctx = context.Context()
        ctx.set('a', A('c', A('7')))

        a = ctx.get('a')
        yield self.assert_raises(lex.SyntaxError, 'a._x;', ctx)
        yield self.assert_code('c', 'a.x;', ctx)
        yield self.assert_code('7', 'a.s.x;', ctx)

    @tornado.testing.gen_test
    def test_binary_expressions(self):
        '''ESL: interpretate binary expressions'''
        yield self.assert_code(9,   '5 + 4;')
        yield self.assert_code(17, '5 + 4 * 3;')
        yield self.assert_code(27, '(5 + 4) * 3;')
        yield self.assert_code(7,  '4 / 2 + 5;')
        yield self.assert_code(12, '5 + 4 / 2 + 5;')

    @tornado.testing.gen_test
    def test_variables(self):
        '''ESL: interpretate variables assignment'''
        yield self.assert_raises(interpreter.RuntimeError, 'a + 1;')
        yield self.assert_code(5,  'a = b = 5; a;')
        yield self.assert_code(5,  'a = b = 5; b;')
        yield self.assert_raises(lex.SyntaxError, 'a = b += 5;')
        yield self.assert_code(5,  'a = 5; a;')
        yield self.assert_code(11, 'a = 5 + 6; a;')

    @tornado.testing.gen_test
    def test_attributes_assignment(self):
        '''ESL: interpretate attributes assignment'''
        class A(object):
            def __init__(self, x):
                self.b = x
        bytecode = self.parser.parse('a.b = "d"; a.b;')
        ctx = context.Context()
        ctx.set('a', A('zzz'))
        yield self.assert_code('d', 'a.b = "d"; a.b;', ctx)

    @tornado.testing.gen_test
    def test_array(self):
        '''ESL: interpretate arrays and its elements'''
        yield self.assert_code([1, 2, '3'], 'a = [1, 2, "3"]; a;')
        yield self.assert_code({'a': 1, 'b': 2, 3: 3},
                'a = {"a": 1, "b": 2, 3: 3}; a;')
        yield self.assert_code('3', 'a = [1, 2, "3"]; a[2];')
        yield self.assert_code(2, 'a = {"a": 1, "b": 2, 3: 3}; a["b"];')
        yield self.assert_code(4, 'a = {"a": 1}; a["a"] = 4; a["a"];')
        yield self.assert_code(4, 'a = [9,8,7,6]; a[1+2] = 4; a[3];')

    @tornado.testing.gen_test
    def test_increment_assignment(self):
        '''ESL: increment assignment'''
        yield self.assert_raises(interpreter.RuntimeError,'a += 1;')
        yield self.assert_code(11, 'a = 5; a += 6; a;')
        yield self.assert_code(-1, 'a = 5; a -= 6; a;')
        yield self.assert_code(6,  'a = 5; a++; a;')
        yield self.assert_code(5,  'a = 6; a--; a;')

    @tornado.testing.gen_test
    def test_unary_expressions(self):
        '''ESL: interpretate unary expressions'''
        yield self.assert_code(-5, '-5;')
        yield self.assert_code(5,  'a = -5; -a;')
        yield self.assert_code(6,  'a = -(5 + 1); -a;')

    @tornado.testing.gen_test
    def test_logical_expressions(self):
        '''ESL: interpretate logical expressions'''
        yield self.assert_code(4,     '1 and 4;')
        yield self.assert_code(5,     '1 - 1 and 4 or 5;')
        yield self.assert_code(False, 'not 5;')

    @tornado.testing.gen_test
    def test_relative_expressions(self):
        '''ESL: interpretate equal and relative expressions'''
        yield self.assert_code(True,  '5 == 5;')
        yield self.assert_code(False, '5 != 5;')
        yield self.assert_code(True,  '5 >= 5;')
        yield self.assert_code(False, '5 >= 6;')
        yield self.assert_code(True,  '6 >= 5;')
        yield self.assert_code(False, '6 <= 5;')
        yield self.assert_code(False, '5 < 5;')

    @tornado.testing.gen_test
    def test_if_statement(self):
        '''ESL: interpretate if-elif-else statement'''
        code = '''\
            a = 1;
            b = 0;
            if (a == 1) {
                b = 1;
            }
            b;
        '''
        yield self.assert_code(1, code)

        code = '''\
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
        '''
        yield self.assert_code(3, code)

        code = '''\
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
        '''
        yield self.assert_code(4, code)

    @tornado.testing.gen_test
    def test_special_if_and_unless(self):
        '''ESL: interpretate special if and unless'''
        code = '''\
            b = 1;
            a = 5 if (b == 1);
            a;
        '''
        yield self.assert_code(5, code)

        code = '''\
            b = 1;
            a = 2;
            a = 5 if (b == 2);
            a;
        '''
        yield self.assert_code(2, code)

        code = '''\
            b = 1;
            a = 2;
            a = 5 unless (b == 2);
            a;
        '''
        yield self.assert_code(5, code)
        code = '''\
            b = 1;
            a = 2;
            a = 5 unless (b == 1);
            a;
        '''
        yield self.assert_code(2, code)

    @tornado.testing.gen_test
    def test_for_statement(self):
        '''ESL: interpretate for (expr; expr; expr) {...} statement'''
        code = '''\
            a = 0;
            for (i = 0; i < 5; i++) {
                a++;
            }
            a;
        '''
        yield self.assert_code(5, code)

        code = '''\
            a = 0;
            for (i = 0; i < 5; i++) {
                for (j = 0; j < 5; j++) {
                    a++;
                }
            }
            a;
        '''
        yield self.assert_code(25, code)

    @tornado.testing.gen_test
    def test_for_in(self):
        '''ESL: interpretate for..in statement'''
        code = '''\
            a = [1, 2, 3, 4, 5];
            b = 0;
            for (i in a) {
                b += i;
            }
            b;
        '''
        yield self.assert_code(15, code)

    @tornado.testing.gen_test
    def test_while_loop(self):
        '''ESL: interpretate while loop'''
        code = '''\
            count = 5;
            result = 0;
            while (count > 0) {
                result += count;
                count --;
            }
            result;
        '''
        yield self.assert_code(15, code)

    @tornado.testing.gen_test
    def test_break_statement(self):
        '''ESL: interpretate break statement'''
        code = '''\
            a = 0;
            for (i = 0; i < 10; i++) {
                break;
                a += 1000;
            }
            a;
        '''

        yield self.assert_code(0, code)
        code = '''\
            a = 0;
            for (i = 0; i < 10; i++) {
                if (a > 5) {
                    break;
                    a += 1000;
                }
                a++;
            }
            a;
        '''
        yield self.assert_code(6, code)

        code = '''\
            a = 0;
            for (i = 0; i < 10; i++) {
                for (j = 0; j < 2; j++) {
                    break;
                    a += 1000;
                }
                a++;
            }
            a;
        '''
        yield self.assert_code(10, code)

        # TODO: test for..in break statement
        # TODO: test while break statement

    @tornado.testing.gen_test
    def test_continue_statement(self):
        '''ESL: interpretate continue statement'''
        code = '''\
            a = 0;
            for (i = 0; i < 5; i++) {
                a++;
                continue;
                a += 1000;
            }
            a;
        '''
        yield self.assert_code(5, code)

        code = '''\
            a = 0;
            for (i = 0; i < 5; i++) {
                for (j = 0; j < 5; j++) {
                    a++;
                    continue;
                    a += 1000;
                }
            }
            a;
        '''
        yield self.assert_code(25, code)
        # TODO: test for..in continue statement
        # TODO: test while continue statement

    @tornado.testing.gen_test
    def test_function(self):
        '''ESL: interpretate function'''
        funcode = '''\
            function summishe(a, b, c, d) {
                return a + b + c + d;
            }
        '''
        yield self.assert_code(10,
                funcode + 'summishe(1, 5, 3, 1);')

        def func(a, b):
            return a + b

        ctx = context.Context({'func': func})
        bytecode = self.parser.parse('return func(1, 3);')
        yield self.assert_code(bytecode.touch(ctx), 4)

    @tornado.testing.gen_test
    def test_function_parameters(self):
        '''ESL: interpretate function parameters'''
        funcode = '''\
            function summishe(a, b, c, d) {
                return a + b + c + d;
            }
        '''
        code = funcode + '''summishe(1, b=5, 6);'''
        yield self.assert_raises(interpreter.RuntimeError, code)
        code = funcode + '''summishe(1, 2, 3);'''
        yield self.assert_raises(interpreter.RuntimeError, code)
        code = funcode + '''summishe(1, 2, 3, 4, 5);'''
        yield self.assert_raises(interpreter.RuntimeError, code)
        code = funcode + '''summishe(1, 2, 3, 4, d=5);'''
        yield self.assert_raises(interpreter.RuntimeError, code)
        code = funcode + '''summishe(1, 2, 3, 4, m=5);'''
        yield self.assert_raises(interpreter.RuntimeError, code)

    @tornado.testing.gen_test
    def test_function_without_parameters(self):
        '''ESL: interpretate function without parameters'''
        code = '''\
            function summishe() {
                return 2;
            }
            return summishe();
        '''
        yield self.assert_code(2, code)

    @tornado.testing.gen_test
    def test_function_namespace(self):
        '''ESL: interpretate function namespaces'''
        code = '''\
            a = 2;
            function sum(a, b) {
                a = 5;
            }
            sum(4, 6);
            return a;
        '''
        yield self.assert_code(2, code)

        code = '''\
            a = 2;
            function sum(b, c) {
                a = 5;
            }
            sum(4, 6);
            return a;
        '''
        yield self.assert_code(2, code)

        code = '''\
            a = {"a": 2};
            function sum(b, c) {
                a["a"] = 5;
            }
            sum(4, 6);
            return a["a"];
        '''
        yield self.assert_code(5, code)

    @tornado.testing.gen_test
    def test_return_statement(self):
        '''ESL: interpretate return statement'''
        code = '''\
            function sumstr(b, c, d) {
                return b + c + d;
                return b + c;
            }
            result = sumstr("a1", "b5", d="d6");
            return result;
            return 2;
        '''
        yield self.assert_code('a1b5d6', code)

        code = '''\
            a = 1;
            if (a == 1) {
                return 2;
            }
            return 3;
        '''
        yield self.assert_code(2, code)

        code = '''return 1;'''
        yield self.assert_code(1, code)

    @tornado.testing.gen_test
    def test_empty_braces(self):
        '''ESL: interpretate empty braces'''
        code = '''{}'''
        yield self.assert_raises(parse.SyntaxError,
                code)
        code = '''{a = 1;}'''
        yield self.assert_raises(parse.SyntaxError,
                code)

    @tornado.testing.gen_test
    def test_import(self):
        '''ESL: interpretate import module'''
        def return_imported(code):
            return '''\
                a = 5;
            '''

        code = '''\
            a = 1;
            import change;
            return a;
        '''
        ctx = context.Context()
        ctx.setImportHandler(return_imported)
        bytecode = self.parser.parse(code)
        yield self.assert_code(5, bytecode.touch(ctx))
