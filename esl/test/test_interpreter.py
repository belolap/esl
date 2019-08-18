__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger, DEBUG

from pytest import fixture, mark

from esl import Interpreter, Namespace, Table, ESLSyntaxError
from esl.lex import Lexer

logger = getLogger(__name__)


@fixture
def debug(caplog):
    caplog.set_level(DEBUG, logger='esl')
    caplog.set_level(DEBUG, logger='yacc')
    return logger.debug


def dump_lex(code, debug=False):
    lexer = Lexer()
    lexer.build(debug=debug)
    lexer.lexer.input(code)
    for tok in lexer.lexer:
        logger.debug(tok)


async def run_code(code, ns=None):
    interpreter = Interpreter(code, namespace=ns)
    return await interpreter.run()


async def assert_code(template, code, ns=None):
    result = await run_code(code, ns=ns)
    assert template == result


async def assert_raises(exc, code, ns=None):
    try:
        await run_code(code, ns=ns)
    except Exception:
        pass
    else:
        assert False, 'Exception {} does not raised'.format(exc.__name__)


class TestInterpreter:
    @mark.asyncio
    async def test_constants(self):
        '''Return constants'''
        await assert_code(1, 'return 1')
        await assert_code(100, 'return 100')
        await assert_code('abc', 'return "abc"')
        await assert_code(True, 'return true;')
        await assert_code(False, 'return false;')
        await assert_code(None, 'return nil;')

    @mark.asyncio
    async def test_binary_expressions(self):
        '''Binary expressions'''
        await assert_code(9, 'return 5 + 4;')
        await assert_code(17, 'return 5 + 4 * 3;')
        await assert_code(27, 'return (5 + 4) * 3;')
        await assert_code(7, 'return 4 / 2 + 5;')
        await assert_code(12, 'return 5 + 4 / 2 + 5;')

    @mark.asyncio
    async def test_tables(self):
        '''Tables'''
        t = Table()
        t[1] = 1
        t[2] = 2
        t["zed"] = "alive"
        assert ([(1, 1), (2, 2), ('zed', 'alive')] == [(k, t[k]) for k in t])

        t[4] = 4
        assert 2 == len(t)

        t[3] = 3
        assert 4, len(t)

        t = await run_code('return {1, 2, 3}')
        assert ([(1, 1), (2, 2), (3, 3)] == [(k, t[k]) for k in t])

    @mark.asyncio
    async def test_dot(self):
        '''Access to object attributes via dot'''
        class A(object):
            def __init__(self, value, child=None):
                self._x = 'denied'
                self.x = value
                self.s = child

        ns = Namespace()
        ns.set_var('a', A('c', A('7')))

        a = ns.get_var('a')
        assert isinstance(a, A)

        await assert_code('c', 'return a.x;', ns)
        await assert_code('7', 'return a.s.x;', ns)
        await assert_raises(ESLSyntaxError, 'return a._x;', ns)

    @mark.asyncio
    async def test_variables(self):
        '''Variables assignment'''
        await assert_code(5, 'a = 5; return a;')
        await assert_code(5, 'a = 5; b = a; return b;')
        await assert_code([6, 5], 'a, b = 5, 6; a, b = b, a; return a, b')
        await assert_code(None, 'return a;')

    @mark.asyncio
    async def test_attributes_assignment(self):
        '''Object's attributes assignment'''
        class A(object):
            def __init__(self, x):
                self.b = x

        ns = Namespace()
        ns.set_var('a', A('zzz'))
        await assert_code('d', 'a.b = "d"; return a.b', ns)
        await assert_code(['z', 'b'], 'z, a.b = "z", "b"; return z, a.b', ns)

    @mark.asyncio
    async def test_relational_expressions(self):
        '''Relational expressions'''
        await assert_code(True, 'return 5 == 5;')
        await assert_code(False, 'return 5 ~= 5;')
        await assert_code(True, 'return 5 >= 5;')
        await assert_code(False, 'return 5 >= 6;')
        await assert_code(True, 'return 6 >= 5;')
        await assert_code(False, 'return 6 <= 5;')
        await assert_code(False, 'return 5  < 5;')

    @mark.asyncio
    async def test_unary_expressions(self):
        '''Unary expressions'''
        await assert_code(3, 'return #{1, 2, [3]=3, ["a"]=4, b=5}')
        await assert_code(5, 'a = -5; return -a')
        await assert_code(6, 'a = -(5 + 1); return -a')

    @mark.asyncio
    async def test_logical_expressions(self):
        '''Logical expressions'''
        dump_lex('return 1 and 4')
        await assert_code(4, 'return 1 and 4')
        await assert_code(5, 'return 1 - 1 == 1 and 4 or 5')
        await assert_code(False, 'return not 5')

    @mark.asyncio
    async def test_if_statement(self):
        '''If-elseif-else statement'''
        code = '''\
            a = 1
            b = 0
            if a == 1 then
                b = 1
            end
            return b
        '''
        await assert_code(1, code)

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
        await assert_code(3, code)

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
        await assert_code(4, code)

    @mark.asyncio
    async def test_while_loop(self):
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
        await assert_code(5, code)

        code = '''
            result = 0
            count = 100
            while count < 1 do
                result = result + 1
                count = count + 1
            end
            return result;
        '''
        await assert_code(0, code)

        code = '''
            result = 0
            count = 0
            repeat
                result = result + 1
                count = count + 1
            until count < 5
            return result
        '''
        await assert_code(5, code)

        code = '''
            result = 0
            count = 100
            repeat
                result = result + 1
                count = count + 1
            until count < 1
            return result
        '''
        await assert_code(1, code)

    @mark.asyncio
    async def test_for_statement(self):
        '''Numeric for statement'''
        code = '''\
            a = 0
            for i=1, 5 do
                a = a + 1
            end
            return a
        '''
        await assert_code(5, code)

        code = '''\
            a = 0
            for i=1, 12, 2 do
                a = a + 1
            end
            return a
        '''
        await assert_code(6, code)

        code = '''\
            a = 0
            for i=1, 12, 2 do
                for j=1, 5 do
                    a = a + 1
                end
            end
            return a
        '''
        await assert_code(30, code)

    @mark.asyncio
    async def test_for_in(self):
        '''Generic for statement'''
        code = '''\
            a = {1, 2, 3, ["b"]=7, c=8, 4, 5}
            b = 0
            for k, v in pairs(a) do
                b = b + v
            end
            return b
        '''
        await assert_code(30, code)

    @mark.asyncio
    async def test_break_statement(self):
        '''Break statement'''
        code = '''
            a = 0
            for i=0, 10 do
                a = a + 1
                break
            end
            return a
        '''
        await assert_code(1, code)

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
        await assert_code(6, code)

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
        await assert_code(33, code)

    @mark.asyncio
    async def test_function(self):
        '''Function'''
        funcode = '''\
            function huge_sum(a, b, c, d)
                return a + b + c + d
            end
        '''
        await assert_code(10, funcode + 'return huge_sum(1, 5, 3, 1)')

        def func(a, b, c=1, *p, **n):
            return a + b

        ns = Namespace({'func': func})
        await assert_code(4, 'return func(1, 3);', ns)

        funcode = '''\
            function dummy()
                return 1
            end
        '''
        await assert_code(1, funcode + 'return dummy()')

    @mark.asyncio
    async def test_function_namespace(self):
        '''Function namespaces'''
        code = '''\
            a = 2
            function sum(a, b)
                a = 5
            end
            sum(4, 6)
            return a
        '''
        await assert_code(2, code)

    @mark.asyncio
    async def test_return_statement(self):
        '''Return statement'''
        code = '''\
            function sumstr(b, c, d)
                return b + c + d
            end
            result = sumstr("a1", "b5", "d6")
            return result
        '''
        await assert_code('a1b5d6', code)

        code = '''\
            a = 1
            if a == 1 then
                return 2
            end
            a = a + 1
            return 3
        '''
        await assert_code(2, code)

        code = '''return 1'''
        await assert_code(1, code)

    @mark.asyncio
    async def test_block_parsing(self):
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
        await assert_code(7, code)

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
        await assert_code(6, code)

    @mark.asyncio
    async def test_comments(self):
        '''Test comments'''
        code = '''\
        -- simple comment
        local a = 1
        return a
        '''
        await assert_code(1, code)

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
        await assert_code(tmpl, code)

    @mark.asyncio
    async def test_scope(self):
        '''Namespace and scope'''
        code = '''\
        a = 1
        do
            a = 2
        end
        return a
        '''
        await assert_code(2, code)

        code = '''\
        a = 1
        do
            local a = 2
        end
        return a
        '''
        await assert_code(1, code)

        code = '''\
        a = 1
        do
            local a = nil
        end
        return a
        '''
        await assert_code(1, code)

        code = '''\
        do
            local a = 1
            a = 2
        end
        return a
        '''
        await assert_code(None, code)

        code = '''\
            local a = 1
            if true then
                a = 2
            end
            return a
        '''
        await assert_code(2, code)

    @mark.asyncio
    async def test_objects_functions(self):
        '''Objects's functions'''
        code = '''\
            a = {b=1}
            function a:test()
                return self.b;
            end
            return a:test()
        '''
        await assert_code(1, code)

        class A(object):
            def __init__(self):
                self.value = 1

            def test(self, increment):
                if isinstance(self, Table):
                    return self['value'] + increment
                return self.value + increment

        ns = Namespace({'a': A()})

        code = '''return a:test(10)'''
        await assert_code(11, code, ns)

        code = '''
            b = {value=2}
            return a.test(b, 20)
        '''
        await assert_code(22, code, ns)

    @mark.asyncio
    async def test_iterators(self):
        '''Iterators'''
        code = '''
            result = 0
            for k, v in pairs(a) do
                result = result + v
            end
            return result
        '''

        await assert_code(6, 'a = {1, 2, 3}' + code)

        ns = Namespace({'a': {'a': 1, 'b': 2, 'c': 3, 'd': 4}})
        await assert_code(10, code, ns)

        ns = Namespace({'a': [1, 2, 3, 4, 5]})
        await assert_code(15, code, ns)

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
        ns = Namespace({'a': A()})
        await assert_code(55, code, ns)

    @mark.asyncio
    async def test_concat(self):
        '''Concat'''
        code = '''return "a" .. "b"'''
        await assert_code('ab', code)

        code = '''return 1 .. "b"'''
        await assert_code('1b', code)

        code = '''return "a" .. 1'''
        await assert_code('a1', code)
