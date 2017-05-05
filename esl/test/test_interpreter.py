#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

import decimal
import logging
import tornado.testing

import esl


logger = logging.getLogger('esl.test')


class TestInterpreter(tornado.testing.AsyncTestCase):

    def setUp(self):
        super().setUp()

    def dump_lex(self, code, debug=False):
        lexer = esl.lex.Lexer()
        lexer.build(debug=debug)
        lexer.lexer.input(code)
        for tok in lexer.lexer:
            logger.debug(tok)

    async def run_code(self, code, ns=None):
        interpreter = esl.Interpreter(code, namespace=ns)
        return await interpreter.run()

    async def assert_code(self, template, code, ns=None):
        result = await self.run_code(code, ns=ns)
        self.assertEqual(template, result)

    async def assert_raises(self, exc, code, ns=None):
        try:
            result = await self.run_code(code, ns=ns)
        except exc as e:
            pass
        else:
            self.fail('Exception {} does not raised'.format(exc.__name__))

    @tornado.testing.gen_test
    def test_constants(self):
        '''Return constants'''
        yield self.assert_code(1, 'return 1')
        yield self.assert_code(100, 'return 100')
        yield self.assert_code('abc', 'return "abc"')
        yield self.assert_code(True,  'return true;')
        yield self.assert_code(False, 'return false;')
        yield self.assert_code(None,  'return nil;')

    @tornado.testing.gen_test
    def test_binary_expressions(self):
        '''Binary expressions'''
        yield self.assert_code(9,  'return 5 + 4;')
        yield self.assert_code(17, 'return 5 + 4 * 3;')
        yield self.assert_code(27, 'return (5 + 4) * 3;')
        yield self.assert_code(7,  'return 4 / 2 + 5;')
        yield self.assert_code(12, 'return 5 + 4 / 2 + 5;')

    @tornado.testing.gen_test
    def test_tables(self):
        '''Tables'''
        t = esl.Table()
        t[1] = 1
        t[2] = 2
        t["zed"] = "alive"
        self.assertEqual([(1, 1), (2, 2), ('zed', 'alive')],
                         [(k, t[k]) for k in t])
        t[4] = 4
        self.assertEqual(2, len(t))

        t[3] = 3
        self.assertEqual(4, len(t))

        t = yield self.run_code('return {1, 2, 3}')
        self.assertEqual([(1, 1), (2, 2), (3, 3)],
                         [(k, t[k]) for k in t])

    @tornado.testing.gen_test
    def test_dot(self):
        '''Access to object attributes via dot'''
        class A(object):
            def __init__(self, value, child=None):
                self._x = 'denied'
                self.x = value
                self.s = child
        ns = esl.Namespace()
        ns.set_global('a', A('c', A('7')))

        a = ns.get_global('a')
        yield self.assert_code('c', 'return a.x;', ns)
        yield self.assert_code('7', 'return a.s.x;', ns)
        yield self.assert_raises(esl.ESLSyntaxError, 'return a._x;', ns)

    @tornado.testing.gen_test
    def test_variables(self):
        '''Variables assignment'''
        yield self.assert_code(5,  'a = 5; return a;')
        yield self.assert_code(5,  'a = 5; b = a; return b;')
        yield self.assert_code([6, 5],  'a, b = 5, 6; a, b = b, a; return a, b')
        yield self.assert_code(None, 'return a;')

    @tornado.testing.gen_test
    def test_attributes_assignment(self):
        '''Object's attributes assignment'''
        class A(object):
            def __init__(self, x):
                self.b = x
        ns = esl.Namespace()
        ns.set_global('a', A('zzz'))
        yield self.assert_code('d', 'a.b = "d"; return a.b', ns)
        yield self.assert_code(['z', 'b'], 'z, a.b = "z", "b"; return z, a.b', ns)


    @tornado.testing.gen_test
    def test_relational_expressions(self):
        '''Relational expressions'''
        yield self.assert_code(True,  'return 5 == 5;')
        yield self.assert_code(False, 'return 5 ~= 5;')
        yield self.assert_code(True,  'return 5 >= 5;')
        yield self.assert_code(False, 'return 5 >= 6;')
        yield self.assert_code(True,  'return 6 >= 5;')
        yield self.assert_code(False, 'return 6 <= 5;')
        yield self.assert_code(False, 'return 5  < 5;')

    @tornado.testing.gen_test
    def test_unary_expressions(self):
        '''Unary expressions'''
        yield self.assert_code(3, 'return #{1, 2, [3]=3, ["a"]=4, b=5}')
        yield self.assert_code(5,  'a = -5; return -a')
        yield self.assert_code(6,  'a = -(5 + 1); return -a')

    @tornado.testing.gen_test
    def test_logical_expressions(self):
        '''Logical expressions'''
        self.dump_lex('return 1 and 4')
        yield self.assert_code(4, 'return 1 and 4')
        yield self.assert_code(5, 'return 1 - 1 == 1 and 4 or 5')
        yield self.assert_code(False, 'return not 5')

    @tornado.testing.gen_test
    def test_if_statement(self):
        '''If-elseif-else statement'''
        code = '''\
            a = 1
            b = 0
            if a == 1 then
                b = 1
            end
            return b
        '''
        yield self.assert_code(1, code)

        code = '''\
            a = 3
            b = 0
            if a == 1 then
                b = 1
            elseif a == 2 then
                b = 2
            elseif a == 3 then
                b = 3
            end
            return b
        '''
        yield self.assert_code(3, code)

        code = '''\
            a = 4
            b = 0
            if a == 1 then
                b = 1
            elseif a == 2 then
                b = 2
            elseif a == 3 then
                b = 3
            else
                b = 4
            end
            return b
        '''
        yield self.assert_code(4, code)

    @tornado.testing.gen_test
    def test_while_loop(self):
        '''While loop'''
        code = '''
            result = 0
            count = 0
            while count < 5 do
                result = result + 1
                count = count + 1
            end
            return result;
        '''
        yield self.assert_code(5, code)

        code = '''
            result = 0
            count = 100
            while count < 1 do
                result = result + 1
                count = count + 1
            end
            return result;
        '''
        yield self.assert_code(0, code)

        code = '''
            result = 0
            count = 0
            repeat
                result = result + 1
                count = count + 1
            until count < 5
            return result
        '''
        yield self.assert_code(5, code)

        code = '''
            result = 0
            count = 100
            repeat
                result = result + 1
                count = count + 1
            until count < 1
            return result
        '''
        yield self.assert_code(1, code)

    @tornado.testing.gen_test
    def test_for_statement(self):
        '''Numeric for statement'''
        code = '''\
            a = 0
            for i=1, 5 do
                a = a + 1
            end
            return a
        '''
        yield self.assert_code(5, code)

        code = '''\
            a = 0
            for i=1, 12, 2 do
                a = a + 1
            end
            return a
        '''
        yield self.assert_code(6, code)

        code = '''\
            a = 0
            for i=1, 12, 2 do
                for j=1, 5 do
                    a = a + 1
                end
            end
            return a
        '''
        yield self.assert_code(30, code)

    @tornado.testing.gen_test
    def test_for_in(self):
        '''Generic for statement'''
        code = '''\
            a = {1, 2, 3, ["b"]=7, c=8, 4, 5}
            b = 0
            for k, v in pairs(a) do
                b = b + v
            end
            return b
        '''
        yield self.assert_code(30, code)

    @tornado.testing.gen_test
    def test_break_statement(self):
        '''Break statement'''
        code = '''
            a = 0
            for i=0, 10 do
                a = a + 1
                break
            end
            return a
        '''
        yield self.assert_code(1, code)

        code = '''
            a = 0
            for i=1, 10 do
                if a > 5 then
                    break
                end
                a = a + 1
            end
            return a
        '''
        yield self.assert_code(6, code)

        code = '''\
            a = 0
            for i=0, 10 do
                for j=0, 10 do
                    if j > 1 then
                        break
                    end
                    a = a + 1
                end
                a = a + 1
            end
            return a
        '''
        yield self.assert_code(33, code)

    @tornado.testing.gen_test
    def test_function(self):
        '''Function'''
        funcode = '''\
            function huge_sum(a, b, c, d)
                return a + b + c + d
            end
        '''
        yield self.assert_code(10, funcode + 'return huge_sum(1, 5, 3, 1)')

        def func(a, b, c=1, *p, **n):
            return a + b

        ns = esl.Namespace({'func': func})
        yield self.assert_code(4, 'return func(1, 3);', ns)

        funcode = '''\
            function dummy()
                return 1
            end
        '''
        yield self.assert_code(1, funcode + 'return dummy()')

    @tornado.testing.gen_test
    def test_function_namespace(self):
        '''Function namespaces'''
        code = '''\
            a = 2
            function sum(a, b)
                a = 5
            end
            sum(4, 6)
            return a
        '''
        yield self.assert_code(2, code)

    @tornado.testing.gen_test
    def test_return_statement(self):
        '''Return statement'''
        code = '''\
            function sumstr(b, c, d)
                return b + c + d
            end
            result = sumstr("a1", "b5", "d6")
            return result
        '''
        yield self.assert_code('a1b5d6', code)

        code = '''\
            a = 1
            if a == 1 then
                return 2
            end
            a = a + 1
            return 3
        '''
        yield self.assert_code(2, code)

        code = '''return 1'''
        yield self.assert_code(1, code)

    @tornado.testing.gen_test
    def test_block_parsing(self):
        '''Block parsing'''
        code = '''
            function a(x)
                return 1 + x
            end
            function b(x)
                return 2 + x
            end
            function c(meth)
                return meth
            end

            z = 1 + c(a or b)(5)
            return z
        '''
        yield self.assert_code(7, code)

        code = '''
            function a(x)
                return 1 + x
            end
            function b(x)
                return 2 + x
            end

            c = 5

            z = 1 + c; (a or b)(5)
            return z
        '''
        yield self.assert_code(6, code)

    @tornado.testing.gen_test
    def test_comments(self):
        '''Test comments'''
        code = '''\
        -- simple comment
        local a = 1
        return a
        '''
        yield self.assert_code(1, code)

        code = '''\
        -- single line
        --[[
            multiline comment
        ]]
        --[=[
            anoher. lets a[b["a"]] = 5
        ]=]
        local a = [[This is
                    multiline
                    string]]
        return a
        '''
        tmpl = '''This is
                    multiline
                    string'''
        yield self.assert_code(tmpl, code)

    @tornado.testing.gen_test
    def test_namespace(self):
        '''Namespace and scope'''
        code = '''\
        a = 1
        do
            a = 2
        end
        return a
        '''
        yield self.assert_code(2, code)

        code = '''\
        a = 1
        do
            local a = 2
        end
        return a
        '''
        yield self.assert_code(1, code)

        code = '''\
        a = 1
        do
            local a = nil
        end
        return a
        '''
        yield self.assert_code(1, code)

        code = '''\
        do
            local a = 1
            a = 2
        end
        return a
        '''
        yield self.assert_code(None, code)

    @tornado.testing.gen_test
    def test_objects_functions(self):
        '''Objects's functions'''
        code = '''\
            a = {b=1}
            function a:test()
                return self.b;
            end
            return a:test()
        '''
        yield self.assert_code(1, code)

        class A(object):
            def __init__(self):
                self.value = 1
            def test(self, increment):
                if isinstance(self, esl.Table):
                    return self['value'] + increment
                return self.value + increment
        ns = esl.Namespace({'a': A()})

        code = '''return a:test(10)'''
        yield self.assert_code(11, code, ns)

        code = '''
            b = {value=2}
            return a.test(b, 20)
        '''
        yield self.assert_code(22, code, ns)

    @tornado.testing.gen_test
    def test_iterators(self):
        '''Iterators'''
        code = '''
            result = 0
            for k, v in pairs(a) do
                result = result + v
            end
            return result
        '''

        yield self.assert_code(6, 'a = {1, 2, 3}' + code)

        ns = esl.Namespace({'a': {'a': 1, 'b': 2, 'c': 3, 'd': 4}})
        yield self.assert_code(10, code, ns)

        ns = esl.Namespace({'a': [1, 2, 3, 4, 5]})
        yield self.assert_code(15, code, ns)

        # Generators
        class A(object):
            def __init__(self):
                self.number = 0
            async def __aiter__(self):
                return self
            async def __anext__(self):
                self.number += 1
                if self.number > 10:
                    raise StopAsyncIteration('finished')
                return self.number

        code = '''
            result = 0
            for k, v in ipairs(a) do
                result = result + v
            end
            return result
        '''
        ns = esl.Namespace({'a': A()})
        yield self.assert_code(55, code, ns)

    @tornado.testing.gen_test
    def test_concat(self):
        '''Concat'''
        code = '''return "a" .. "b"'''
        yield self.assert_code('ab', code)

        code = '''return 1 .. "b"'''
        yield self.assert_code('1b', code)

        code = '''return "a" .. 1'''
        yield self.assert_code('a1', code)
