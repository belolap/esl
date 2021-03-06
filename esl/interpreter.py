__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

import sys
import inspect
import logging
import traceback

import esl.parse
import esl.namespace
import esl.table
import esl.function
import esl.extensions

logger = logging.getLogger(__name__)


class ESLSyntaxError(Exception):
    pass


class ESLRuntimeError(Exception):
    pass


class Node(object):
    def __init__(self, lineno):
        self.lineno = lineno

    def is_false(self, val):
        return val in (None, False)

    async def touch(self, interpreter, ns):
        raise NotImplementedError('method must be overrided')


class ListNode(Node):
    def __init__(self, lineno):
        super().__init__(lineno)
        self.children = []

    def __iter__(self):
        return iter(self.children)

    def append(self, item):
        self.children.append(item)


class Chunk(Node):
    def __init__(self, lineno, block):
        super().__init__(lineno)
        self.block = block

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        result = await self.block.touch(interpreter, ns)
        interpreter.line_stack.pop()
        return result


class Block(ListNode):
    def __init__(self, lineno):
        super().__init__(lineno)

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        ns = ns.clone()

        result = None
        for statement in self.children:
            if interpreter.returning or interpreter.breaking:
                break
            if statement is not None:
                result = await statement.touch(interpreter, ns)
        interpreter.line_stack.pop()
        return result


class Statement(Node):
    pass


class Assignment(Statement):
    def __init__(self, lineno, left, value, local=False):
        super().__init__(lineno)
        self.left = left
        self.value = value
        self.local = local

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        count = len(self.left.children)
        if self.value is not None and len(self.value.children) != count:
            raise ValueError('incorrect count of values')

        values = []
        for i in range(0, count):
            if self.value is None:
                values.append(None)
            else:
                values.append(
                    (await self.value.children[i].touch(interpreter,
                                                        ns)))  # yapf: ignore

        for i in range(0, count):
            item = self.left.children[i]
            value = values[i]
            if isinstance(item, Variable):
                name = await item.name.touch(interpreter, ns)
            else:
                name = await item.touch(interpreter, ns)

            if isinstance(item, Variable) and item.left is not None:
                obj = await item.left.touch(interpreter, ns)
                try:
                    if value is None:
                        if name in obj:
                            ns.del_item(obj, name)
                    else:
                        ns.set_item(obj, name, value)
                except TypeError:
                    if value is None:
                        if ns.has_attribute(obj, name):
                            ns.del_attribute(obj, name)
                    else:
                        ns.set_attribute(obj, name, value)
            else:
                ns.set_var(name, value, self.local)

        interpreter.line_stack.pop()


class While(Statement):
    def __init__(self, lineno, expression, block, check_before=True):
        super().__init__(lineno)
        self.expression = expression
        self.block = block
        self.check_before = check_before

    async def _check_expression(self, interpreter, ns):
        result = await self.expression.touch(interpreter, ns)
        if result is None or result is False:
            return False
        return True

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        interpreter.loop_stack.append(self)

        result = None

        i = 0
        while i < 100:
            i += 1
            if self.check_before:
                if not await self._check_expression(interpreter, ns):
                    interpreter.breaking = True

            if interpreter.breaking:
                break

            result = await self.block.touch(interpreter, ns)

            if not self.check_before:
                if not await self._check_expression(interpreter, ns):
                    interpreter.breaking = True

        interpreter.breaking = False

        interpreter.loop_stack.pop()
        interpreter.line_stack.pop()

        return result


class If(Statement):
    def __init__(self, lineno, expression, block, elseiflist, else_):
        super().__init__(lineno)
        self.expression = expression
        self.block = block
        self.elseiflist = elseiflist
        self.else_ = else_

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        passed = False
        result = None

        check = await self.expression.touch(interpreter, ns)
        if not self.is_false(check):
            result = await self.block.touch(interpreter, ns)
            passed = True

        if not passed:
            for elseif in self.elseiflist:
                check = await elseif.expression.touch(interpreter, ns)
                if not self.is_false(check):
                    result = await elseif.touch(interpreter, ns)
                    passed = True
                    break

        if not passed and self.else_ is not None:
            result = await self.else_.block.touch(interpreter, ns)

        interpreter.line_stack.pop()
        return result


class NumericFor(Statement):
    def __init__(self, lineno, name, start, limit, step, block):
        super().__init__(lineno)
        self.name = name
        self.start = start
        self.limit = limit
        self.step = step
        self.block = block

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        interpreter.loop_stack.append(self)

        ns = ns.clone()

        result = None

        name = self.name.name
        start = await self.start.touch(interpreter, ns)
        assert isinstance(start, int)

        limit = await self.limit.touch(interpreter, ns)
        assert isinstance(limit, int)

        if self.step is None:
            step = 1
        else:
            step = await self.step.touch(interpreter, ns)
        assert isinstance(step, int)

        i = start

        while (step > 0 and i <= limit) or (step <= 0 and i >= limit):
            if interpreter.breaking:
                break
            ns.set_var(name, i, True)
            result = await self.block.touch(interpreter, ns)
            i += step

        interpreter.breaking = False

        interpreter.loop_stack.pop()
        interpreter.line_stack.pop()

        return result


class GenericFor(Statement):
    def __init__(self, lineno, namelist, explist, block):
        super().__init__(lineno)
        self.namelist = namelist
        self.explist = explist
        self.block = block

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        interpreter.loop_stack.append(self)

        result = None

        ns = ns.clone()

        params = []
        for expression in self.explist.children:
            evaluated = await expression.touch(interpreter, ns)
            if isinstance(evaluated, (list, tuple)):
                params += evaluated
            else:
                params.append(evaluated)
        if len(params) < 3:
            params += [None] * (3 - len(params))

        names = []
        for name in self.namelist.children:
            names.append(await name.touch(interpreter, ns))

        fun, obj, key = params[0:3]

        while True:
            if hasattr(fun, '__anext__'):
                try:
                    values = (None, await fun.__anext__())
                except StopAsyncIteration:
                    values = None
            elif hasattr(fun, '__next__'):
                try:
                    values = (None, await fun.__next__())
                except StopAsyncIteration:
                    values = None
            else:
                values = fun(obj, key)

            if values is None:
                break

            if not isinstance(values, (list, tuple)):
                values = [values]

            for k, v in zip(names, values):
                ns.set_var(k, v, True)

            result = await self.block.touch(interpreter, ns)

            key = values[0]

        interpreter.breaking = False

        interpreter.loop_stack.pop()
        interpreter.line_stack.pop()

        return result


class Function(Statement):
    def __init__(self, lineno, name, body, local):
        super().__init__(lineno)
        self.name = name
        self.body = body
        self.local = local

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        func = esl.function.Function(self.body.parlist, self.body.body)

        name = await self.name.children.pop().touch(interpreter, ns)

        parent = None
        for item in self.name.children:
            if parent is None:
                n = await item.touch(interpreter, ns)
                parent = ns.get_var(n)
            else:
                parent = parent[n]
            if parent is None:
                raise NameError('function not found')

        if parent is None:
            ns.set_var(name, func)
        else:
            if self.name.colon:
                func.self = parent
            parent[name] = func

        interpreter.line_stack.pop()


class Break(Statement):
    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        interpreter.breaking = True
        interpreter.line_stack.pop()


class Return(Statement):
    def __init__(self, lineno, explist):
        super().__init__(lineno)
        self.explist = explist

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        if self.explist is None:
            expressions = []
        else:
            expressions = self.explist

        result = []
        for expression in expressions:
            result.append(await expression.touch(interpreter, ns))

        interpreter.returning = True
        interpreter.line_stack.pop()

        if len(result) == 0:
            return
        elif len(result) == 1:
            return result[0]
        else:
            return result


class ElseIfList(ListNode):
    pass


class ElseIf(Node):
    def __init__(self, lineno, expression, block):
        super().__init__(lineno)
        self.expression = expression
        self.block = block

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        result = await self.block.touch(interpreter, ns)
        interpreter.line_stack.pop()
        return result


class Else(Node):
    def __init__(self, lineno, block):
        super().__init__(lineno)
        self.block = block

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        result = await self.block.touch(interpreter, )
        interpreter.line_stack.pop()
        return result


class FunctionName(ListNode):
    def __init__(self, lineno, colon=False):
        super().__init__(lineno)
        self.colon = colon


class VariableList(ListNode):
    pass


class Variable(Node):
    def __init__(self, lineno, left, name, proto='dict'):
        super().__init__(lineno)
        self.left = left
        self.name = name
        self.proto = proto

    async def touch(self, interpreter, ns):
        if isinstance(self.name, Name):
            name = self.name.name
        else:
            name = await self.name.touch(interpreter, ns)

        if self.left is None:
            result = ns.get_var(name)
        else:
            left = await self.left.touch(interpreter, ns)
            try:
                result = ns.get_item(left, name)
            except TypeError:
                result = ns.get_attribute(left, name)
        return result


class NameList(ListNode):
    pass


class ExpressionList(ListNode):
    pass


class Constant(Node):
    def __init__(self, lineno, value):
        super().__init__(lineno)
        self.value = value

    async def touch(self, interpreter, ns):
        return self.value


class FunctionCall(Node):
    def __init__(self, lineno, prefixexp, name, args, colon=False):
        super().__init__(lineno)
        self.prefixexp = prefixexp
        self.name = name
        self.args = args
        self.colon = colon

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        obj = await self.prefixexp.touch(interpreter, ns)
        if self.name is None:
            func = obj
        else:
            name = await self.name.touch(interpreter, ns)
            if isinstance(obj, esl.table.Table):
                func = obj[name]
            else:
                func = getattr(obj, name)

        ns = ns.clone()

        if isinstance(func, esl.function.Function):
            if self.colon:
                ns.set_var('self', func.self, True)

            if func.parlist is not None:
                count = len(func.parlist.namelist.children)
                for i in range(0, count):
                    parameter = await func.parlist.namelist.children[i].touch(
                        interpreter, ns)
                    arg = await self.args.children[i].touch(interpreter, ns)
                    ns.set_var(parameter, arg, True)
            result = await func.body.touch(interpreter, ns)

        else:
            if not callable(func):
                if isinstance(func, type(None)):
                    func = 'nil'
                raise TypeError('{} is not callable'.format(str(func)))

            args = []
            for arg in self.args.children:
                args.append(await arg.touch(interpreter, ns))

            if inspect.ismethod(func):
                if self.colon:
                    args.insert(0, func.__self__)
                func = func.__func__

            if inspect.iscoroutinefunction(func):
                result = await func(*args)
            else:
                result = func(*args)

        interpreter.returning = False
        interpreter.line_stack.pop()

        return result


class Args(ListNode):
    pass


class FunctionBody(Node):
    def __init__(self, lineno, parlist, body):
        super().__init__(lineno)
        self.parlist = parlist
        self.body = body


class ParametersList(Node):
    def __init__(self, lineno, namelist, dots=False):
        super().__init__(lineno)
        self.namelist = namelist
        self.dots = dots


class Table(Node):
    def __init__(self, lineno, fieldlist):
        super().__init__(lineno)

        self.fieldlist = fieldlist

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        fieldlist = []
        if self.fieldlist is not None:
            for field in self.fieldlist.children:
                if field.name is None:
                    name = None
                else:
                    name = await field.name.touch(interpreter, ns)
                value = await field.expression.touch(interpreter, ns)
                fieldlist.append((name, value))

        table = esl.table.Table()
        i = 1
        for k, v in fieldlist:
            if k is None:
                k = i
                i += 1
            table[k] = v
        interpreter.line_stack.pop()
        return table


class FieldList(ListNode):
    pass


class Field(Node):
    def __init__(self, lineno, name, expression):
        super().__init__(lineno)
        self.name = name
        self.expression = expression


class Logical(Node):
    def __init__(self, lineno, left, operation, right):
        super().__init__(lineno)
        self.left = left
        self.operation = operation
        self.right = right

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        left = await self.left.touch(interpreter, ns)
        right = await self.right.touch(interpreter, ns)

        if self.operation == 'and':
            return left and right
        elif self.operation == 'or':
            return left or right
        else:
            raise NotImplementedError('operator {} is not '
                                      'implemented'.format(self.operator))


class Relational(Node):
    def __init__(self, lineno, left, operation, right):
        super().__init__(lineno)
        self.left = left
        self.operation = operation
        self.right = right

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        left = await self.left.touch(interpreter, ns)
        right = await self.right.touch(interpreter, ns)

        if self.operation == '==':
            result = (left == right)
        elif self.operation == '<':
            result = (left < right)
        elif self.operation == '>':
            result = (left > right)
        elif self.operation == '<=':
            result = (left <= right)
        elif self.operation == '>=':
            result = (left >= right)
        elif self.operation == '~=':
            result = (left != right)
        else:
            raise NotImplementedError('operation {} not '
                                      'supported'.format(self.operation))

        interpreter.line_stack.pop()

        return result


class Append(Node):
    def __init__(self, lineno, left, right):
        super().__init__(lineno)
        self.left = left
        self.right = right

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        left = await self.left.touch(interpreter, ns)
        right = await self.right.touch(interpreter, ns)

        if (not isinstance(left, (str, int, float))
                or not isinstance(right, (str, int, float))):
            raise TypeError('can concate only strings or numbers, '
                            'got `{} .. {}\''.format(
                                type(left).__name__,
                                type(right).__name__))

        result = str(left) + str(right)

        interpreter.line_stack.pop()
        return result


class Arithmetic(Node):
    def __init__(self, lineno, left, operation, right):
        super().__init__(lineno)
        self.left = left
        self.operation = operation
        self.right = right

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)

        left = await self.left.touch(interpreter, ns)
        right = await self.right.touch(interpreter, ns)

        if self.operation == '+':
            result = left + right
        elif self.operation == '-':
            result = left - right
        elif self.operation == '*':
            result = left * right
        elif self.operation == '/':
            result = left / right
        else:
            raise NotImplementedError('operation {} not '
                                      'supported'.format(self.operation))

        interpreter.line_stack.pop()

        return result


class Unary(Node):
    def __init__(self, lineno, operation, expression):
        super().__init__(lineno)
        self.operation = operation
        self.expression = expression

    async def touch(self, interpreter, ns):
        interpreter.line_stack.append(self.lineno)
        result = await self.expression.touch(interpreter, ns)
        interpreter.line_stack.pop()

        if self.operation == '-':
            return -result
        elif self.operation == 'not':
            return not bool(result)
        elif self.operation == '#':
            return len(result)


class Name(Node):
    def __init__(self, lineno, name):
        super().__init__(lineno)
        self.name = name

    async def touch(self, interpreter, ns):
        return self.name


class Interpreter(object):
    def __init__(self,
                 code,
                 bytecode=None,
                 namespace=None,
                 extensions=None,
                 debug=False):
        self.__code = code

        if bytecode is None:
            parser = esl.parse.Parser(debug=debug)
            try:
                bytecode = parser.parse(code)
            except (esl.lex.LexError, esl.parse.ParseError) as e:
                raise ESLSyntaxError(str(e))
        self.__bytecode = bytecode

        if namespace is None:
            namespace = esl.namespace.Namespace()
        self.__namespace = namespace

        self.add_extensions(extensions)

        self.debug = debug

        self.line_stack = []
        self.call_stack = []
        self.loop_stack = []

        self.breaking = False
        self.returning = False

    def add_extensions(self, extensions=None, **kwargs):
        if extensions is None:
            extensions = esl.extensions.__extension__

        ns = self.__namespace

        for k, v in extensions.items():
            ns.set_var(k, v)

        for k, v in kwargs.items():
            ns.set_var(k, v)

    async def run(self):
        if self.__bytecode is None:
            return
        try:
            result = await self.__bytecode.touch(self, self.__namespace)

        except Exception as e:
            # Error message
            msg = str(e)
            if not msg:
                msg = '(no message)'
            msg = msg[0].lower() + msg[1:]
            logger.error('Error: {}'.format(msg))

            lines = self.__code.split('\n')

            # ESL call stack
            parent_fun = '<main>'
            for fun, lineno in self.call_stack:
                logger.error('... {} line {}: {}()'.format(
                    parent_fun, lineno, fun))
                parent_fun = fun

            lastline = self.line_stack[-1]
            if lastline <= len(lines):
                line = lines[lastline - 1].strip()[:50]
                logger.error('... {} line {}: {} ...'.format(
                    parent_fun, lastline, line))
            else:
                logger.error('... {} line {}: can\' find source '
                             'line '.format(parent_fun, lastline))

            # Python traceback
            if self.debug:
                t, val, tb = sys.exc_info()
                message = str(val)
                if message:
                    message = '{}: {}'.format(t.__name__, message)
                else:
                    message = t.__name__

                logger.debug('Python traceback:')
                for file, line, fun, inst in traceback.extract_tb(tb):
                    logger.debug('... {} line {} in {}()'.format(
                        file[-40:], line, fun))
                logger.debug('...   {}'.format(inst))

            raise ESLRuntimeError(msg) from None

        return result
