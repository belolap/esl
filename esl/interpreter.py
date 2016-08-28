__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

__all__ = ['Interpreter',
           'Id', 'Attribute', 'BasicType', 'StringType',
           'Array', 'ArrayElement',
           'VariableAssignment', 'ExpressionStatement', 'TranslationUnit',
           'Hash', 'HashElement', 'ArrayAccess', 'BinaryExpression',
           'RelationalExpression', 'IncrementExpression',
           'LoopCommandStatement', 'CompoundStatement', 'ForStatement',
           'IfStatement', 'ForInStatement', 'Declaration', 'Return',
           'FunctionStatement', 'CallElement', 'Call', 'ElIfStatement',
           'ElseStatement', 'ImportStatement', 'LogicalExpression',
           'UnaryExpression', 'UnaryExpression', 'SpecialIfStatement',
           'UnlessStatement', 'WhileStatement']

import sys
import logging
import traceback
import collections

from . import context


logger = logging.getLogger('edera.esl.interpreter')


# Exception
class RuntimeError(Exception):
    pass


# Nodes
class Node(object):

    def __init__(self, lineno):
        self.lineno = lineno

    def eval(self):
        raise NotImplementedError('method {}.eval() does not implemented '
                                  'yet'.format(type(self).__name__))

    async def touch(self, ctx):
        raise NotImplementedError('method {}.touch() does not implemented '
                                  'yet'.format(type(self).__name__))


class NodeList(Node):

    def __init__(self, lineno):
        self.children = []
        super().__init__(lineno)

    def __getitem__(self, k):
        return self.children[k]

    def __setitem__(self, k, v):
        self.children[k] = v

    def add(self, node):
        self.children.append(node)


class AttrDict(collections.MutableMapping):

    def __getitem__(self, key):
        return self.__dict__.__getitem__(key)

    def __setitem__(self, key, value):
        return self.__dict__.__setitem__(key, value)

    def __delitem__(self, key):
        return self.__dict__.__delitem__(key, value)

    def __iter__(self):
        for k in self.__dict__.keys():
            yield k

    def __len__(self):
        return self.__dict__.__len__()


class TranslationUnit(NodeList):

    def __init__(self, lineno, node):
        super().__init__(lineno)
        self.add(node)

    def pretty(self):
        return ' '.join([x.pretty() for x in self.children])

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        for statement in self.children:
            if len(ctx.loops) > 0:
                loop = ctx.loops[-1]
                if loop.must_break or loop.must_continue:
                    continue
            result = await statement.touch(ctx)
            if ctx.must_return:
                ctx.line_stack.pop()
                return result
        ctx.line_stack.pop()
        return result


class ImportStatement(Node):

    def __init__(self, parser, lineno, id):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.parser = parser
        self.id = id

    def __str__(self):
        return 'import %s;' % self.id

    async def touch(self, ctx):
        if ctx.import_handler is None:
            raise RuntimeError('please setup import handler')
        code = ctx.import_handler(self.id.name)
        bytecode = self.parser.parse(code)
        return bytecode.touch(ctx)


class FunctionObject(object):

    def __init__(self, name, parameters, compound_statement):
        raise NotImplementedError('for revision')
        self.name = name
        self.parameters = parameters
        self.compound_statement = compound_statement

    def __call__(self, ctx, *params, **named):
        # create new globals
        new_globals = ctx.getGlobals().copy()
        new_globals.update(ctx.getLocals())

        # create new locals
        new_locals = {}
        parameters = list(self.parameters)
        for i in range(0, len(params)):
            try:
                key = parameters.pop(0)
            except IndexError:
                raise TypeError(
                        'function take a {} parameters, but {} given'.format(
                            len(self.parameters), len(params) + len(named)))
            new_locals[key] = params[i]

        for key in named:
            if self.parameters.count(key):
                if key in new_locals:
                    raise TypeError('parameter {} passed twiste'.format(key))
                new_locals[key] = named[key]
                parameters.pop(parameters.index(key))
            else:
                raise TypeError('parameter {} not defined '
                                'in function'.format(key))

        if len(parameters):
            raise TypeError(
                    'function take a {} parameters, but {} given'.format(
                        len(self.parameters), len(params) + len(named)))

        # create new context
        new_ctx = context.Context(new_globals, new_locals)

        return self.compound_statement.touch(new_ctx)

    def __repr__(self):
        return '<{} {} at {}>'.format(self.__class__.__name__,
                                      self.name,
                                      hex(id(self)))


class FunctionStatement(Node):

    def __init__(self, lineno, id, declaration, compound_statement):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.id = id
        self.declaration = declaration
        self.compound_statement = compound_statement

    def __str__(self):
        if self.declaration is None:
            declaration = ''
        else:
            declaration = str(self.declaration)
        return 'function %s (%s) %s' % (str(self.id), declaration, str(self.compound_statement))

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        name = self.id.name
        if self.declaration is not None:
            declarations = self.declaration.children
        else:
            declarations = []
        parameters = list(map(lambda x: x.name, declarations))
        fun = FunctionObject(name, parameters, self.compound_statement)
        if ctx.has_key(name):
            ctx.set(name, fun)
        else:
            ctx.addLocal(name, fun)
        ctx.line_stack.pop()


class Declaration(NodeList):

    def __init__(self, lineno):
        raise NotImplementedError('for revision')
        super().__init__(lineno)

    def __str__(self):
        return ', '.join([str(x) for x in self.children])


class Return(Node):

    def __init__(self, lineno, expression):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.expression = expression

    def __str__(self):
        return 'return %s' % str(self.expression)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        ctx.must_return = True
        result = self.expression.touch(ctx)
        ctx.line_stack.pop()
        return result


class IfStatement(NodeList):

    def __init__(self, lineno, if_expression, compound_statement, elif_statement, else_statement):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.if_expression = if_expression
        self.compound_statement = compound_statement
        self.elif_statement = elif_statement
        self.else_statement = else_statement

    def __str__(self):
        return 'if (%s) %s%s%s' % (
                str(self.if_expression),
                str(self.compound_statement),
                self.elif_statement != None and ' ' + str(self.elif_statement) or '',
                self.else_statement != None and ' ' + str(self.else_statement) or '',
                )

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        if bool(self.if_expression.touch(ctx)):
            result = self.compound_statement.touch(ctx)
            ctx.line_stack.pop()
            return result
        else:
            if self.elif_statement is not None:
                for expression, statement in self.elif_statement.children:
                    if bool(expression.touch(ctx)):
                        result = statement.touch(ctx)
                        ctx.line_stack.pop()
                        return result

            if self.else_statement is not None:
                result = self.else_statement.compound_statement.touch(ctx)
                ctx.line_stack.pop()
                return result


class ElIfStatement(NodeList):

    def __init__(self, lineno):
        raise NotImplementedError('for revision')
        super().__init__(lineno)

    def __str__(self):
        return ' '.join ([ 'elif (%s) %s' % (str(x[0]), str(x[1])) for x in self.children ])


class ElseStatement(Node):

    def __init__(self, lineno, compound_statement):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.compound_statement = compound_statement

    def __str__(self):
        return 'else %s' % str(self.compound_statement)


class SpecialIfStatement(Node):

    def __init__(self, lineno, expression, if_expression):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.expression = expression
        self.if_expression = if_expression

    def __str__(self):
        return '%s if (%s);' % (str(self.expression), str(self.if_expression))

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = None
        if bool(self.if_expression.touch(ctx)):
            result = self.expression.touch(ctx)
        ctx.line_stack.pop()
        return result


class UnlessStatement(Node):

    def __init__(self, lineno, expression, if_expression):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.expression = expression
        self.if_expression = if_expression

    def __str__(self):
        return '%s unless (%s);' % (str(self.expression), str(self.if_expression))

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = None
        if not bool(self.if_expression.touch(ctx)):
            result = self.expression.touch(ctx)
        ctx.line_stack.pop()
        return result


class ForStatement(Node):

    def __init__(self, lineno, init_expression, relative_expression, increment_expression, compound_statement):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.init_expression = init_expression
        self.relative_expression = relative_expression
        self.increment_expression = increment_expression
        self.compound_statement = compound_statement
        self.must_break = False
        self.must_continue = False

    def __str__(self):
        return 'for (%s; %s; %s) %s' % (self.init_expression, self.relative_expression, self.increment_expression, self.compound_statement)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        init = self.init_expression
        relative = self.relative_expression
        increment = self.increment_expression

        ctx.loops.append(self)

        init.touch(ctx)

        while bool(relative.touch(ctx)):
            self.must_continue = False
            for statement in self.compound_statement.translation_unit.children:
                statement.touch(ctx)
                if self.must_break or self.must_continue:
                    break
            if self.must_break:
                break
            increment.touch(ctx)

        del ctx.loops[-1]
        ctx.line_stack.pop()


class ForInStatement(Node):

    def __init__(self, lineno, id, expression, compound_statement):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.id = id
        self.expression = expression
        self.compound_statement = compound_statement
        self.must_break = False
        self.must_continue = False

    def __str__(self):
        return 'for (%s in %s) %s' % (self.id, self.expression, self.compound_statement)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        ctx.loops.append(self)
        for element in self.expression.touch(ctx):
            self.must_continue = False
            if not ctx.has_key(self.id.name):
                ctx.addLocal(self.id.name, element)
            else:
                ctx.set(self.id.name, element)
            for statement in self.compound_statement.translation_unit.children:
                statement.touch(ctx)
                if self.must_break or self.must_continue:
                    break
            if self.must_break:
                break
        del ctx.loops[-1]
        ctx.line_stack.pop()


class WhileStatement(Node):

    def __init__(self, lineno, expression, compound_statement):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.expression = expression
        self.compound_statement = compound_statement
        self.must_break = False
        self.must_continue = False

    def __str__(self):
        return 'while (%s) %s' % (self.expression, self.compound_statement)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        ctx.loops.append(self)

        while bool(self.expression.touch(ctx)):
            self.must_continue = False
            for statement in self.compound_statement.translation_unit.children:
                statement.touch(ctx)
                if self.must_break or self.must_continue:
                    break
            if self.must_break:
                break
        del ctx.loops[-1]
        ctx.line_stack.pop()


class LoopCommandStatement(Node):

    def __init__(self, lineno, command):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.command = command

    def __str__(self):
        return '%s' % self.command

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        if len(ctx.loops) < 1:
            raise RuntimeError('`%s\' statement without loop.' % self.command)
        if self.command == 'break':
            ctx.loops[-1].must_break = True
        elif self.command == 'continue':
            ctx.loops[-1].must_continue = True
        else:
            raise RuntimeError('unknown loop command `%s\'.' % type(self.command))
        ctx.line_stack.pop()


class CompoundStatement(Node):

    def __init__(self, lineno, translation_unit):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.translation_unit = translation_unit

    def __str__(self):
        return '{%s}' % str(self.translation_unit)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = self.translation_unit.touch(ctx)
        ctx.line_stack.pop()
        return result


class ExpressionStatement(Node):

    def __init__(self, lineno, expression):
        super().__init__(lineno)
        self.expression = expression

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = await self.expression.touch(ctx)
        ctx.line_stack.pop()
        return result


class VariableAssignment(Node):

    def __init__(self, lineno, variable, expression):
        super().__init__(lineno)
        self.variable = variable
        self.expression = expression

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)

        var = self.variable
        value = await self.expression.touch(ctx)

        # Assign to variable
        if isinstance(var, Id):
            ctx.set(var.name, value)

        # Assign to object's attribute
        elif isinstance(var, Attribute):
            if var.attr is None:
                ctx.set(var.id.name, value)
            else:
                obj = await var.attr.touch(ctx)
                setattr(obj, var.id.name, value)

        # Array element asignment
        elif isinstance(var, ArrayAccess):
            array = await var.attr.touch(ctx)
            array_key = await var.expression.touch(ctx)
            array.__setitem__(array_key, value)

        else:
            raise TypeError('unknown variable type: {}'.format(type(var).__name__))

        ctx.line_stack.pop()
        return value


class IncrementAssignment(VariableAssignment):

    def __init__(self, lineno, variable, operator, expression):
        operator = {'+=': '+', '-=': '-'}.get(operator)
        expression = BinaryExpression(lineno, variable, operator, expression)
        super().__init__(lineno, variable, expression)


class LogicalExpression(Node):

    def __init__(self, lineno, left, operator, right):
        super().__init__(lineno)
        self.left = left
        self.operator = operator
        self.right = right

    def eval(self):
        if self.left is None:
            left = ''
        else:
            left = self.left.eval()
        return '{} {} {}'.format(left, self.operator, self.right.eval())

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        parts = []
        if self.left is not None:
            parts.append(self.left.eval())
        parts.append(self.operator)
        parts.append(self.right.eval())
        code = ' '.join(parts)
        result = eval(code, ctx.globals, ctx.locals)
        ctx.line_stack.pop()
        return result


class RelationalExpression(Node):

    def __init__(self, lineno, left, operator, right):
        super().__init__(lineno)
        self.left = left
        self.operator = operator
        self.right = right

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        code = '{} {} {}'.format(
                self.left.eval(), self.operator, self.right.eval())
        result = eval(code, ctx.globals, ctx.locals)
        ctx.line_stack.pop()
        return result


class BinaryExpression(Node):

    def __init__(self, lineno, left, operation, right):
        super().__init__(lineno)
        self.left = left
        self.operation = operation
        self.right = right

    def eval(self):
        return '({} {} {})'.format(self.left.eval(),
                                   self.operation,
                                   self.right.eval())

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        code = '{} {} {}'.format(self.left.eval(),
                                 self.operation,
                                 self.right.eval())
        result = eval(code, ctx.globals, ctx.locals)
        ctx.line_stack.pop()
        return result


class Call(Node):

    def __init__(self, lineno, attribute, parameters):
        raise NotImplementedError('for revision')
        super().__init__(lineno)
        self.attribute = attribute
        self.parameters = parameters

    def __str__(self):
        if self.parameters is None:
            parameters = ''
        else:
            parameters = str(self.parameters)
        return '%s(%s)' % (str(self.attribute), parameters)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)

        if self.parameters is None:
            parameters = []
        else:
            parameters = self.parameters

        # compile parameters
        params = ()
        named = {}

        first_named_param = None
        try:
            first_named_param = list(map(lambda x: type(x), parameters)).index(VariableAssignment)
        except ValueError:
            pass

        if first_named_param is None:
            params = tuple(parameters)
        else:
            params = tuple(parameters[0:first_named_param])
            for param in parameters[first_named_param:]:
                if isinstance(param, VariableAssignment):
                    named[param.key.id.name] = param.expression
                else:
                    raise TypeError('can\'t use unnamed parameter after named.')

        # find function and create namespaces
        fun = self.attribute.touch(ctx)

        # call function
        if isinstance(fun, FunctionObject):
            # append element to stack
            ctx.call_stack.append((str(self.attribute), self.lineno))

            # call
            result = fun.__call__(ctx, *params, **named)

            # del last element from stack
            del ctx.call_stack[-1]

        else:
            # touch all params for python
            e_params = tuple(map(lambda x: x.touch(ctx), params))
            e_named = {}
            for key in named:
                e_named[str(key)] = named[key].touch(ctx)

            # call
            result = fun.__call__(*e_params, **e_named)

        # reset return flag
        ctx.must_return = False


        ctx.line_stack.pop()
        return result


class CallElement(NodeList):

    def __init__(self, lineno):
        raise NotImplementedError('for revision')
        super().__init__(lineno)

    def __str__(self):
        return ', '.join([str(x) for x in self.children])


class Hash(Node):

    def __init__(self, lineno, element):
        super().__init__(lineno)
        self.element = element

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        if self.element is None:
            result = AttrDict()
        else:
            result = await self.element.touch(ctx)
        ctx.line_stack.pop()
        return result


class HashElement(NodeList):

    def __init__(self, lineno):
        super().__init__(lineno)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = AttrDict()
        for k, v in self.children:
            result[await k.touch(ctx)] = await v.touch(ctx)
        ctx.line_stack.pop()
        return result


class Array(Node):

    def __init__(self, lineno, element):
        super().__init__(lineno)
        self.element = element

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        if self.element is None:
            result = list()
        else:
            element = await self.element.touch(ctx)
            result = list(element)
        ctx.line_stack.pop()
        return result


class ArrayElement(NodeList):

    def __init__(self, lineno):
        super().__init__(lineno)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = []
        for x in self.children:
            result.append(await x.touch(ctx))
        ctx.line_stack.pop()
        return result


class ArrayAccess(Node):

    def __init__(self, lineno, attr, expression):
        super().__init__(lineno)
        self.attr = attr
        self.expression = expression

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        array = await self.attr.touch(ctx)
        result = array.__getitem__(await self.expression.touch(ctx))
        ctx.line_stack.pop()
        return result


class Attribute(Node):

    def __init__(self, lineno, attr, id):
        super().__init__(lineno)
        self.attr = attr
        self.id = id

    def eval(self):
        parts = []
        if self.attr is not None:
            parts.append(self.attr.eval())
        parts.append(self.id.eval())
        return '.'.join(parts)

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        if self.attr is not None:
            obj = await self.attr.touch(ctx)
            result = getattr(obj, self.id.name)
        else:
            result = await self.id.touch(ctx)
        ctx.line_stack.pop()
        return result


class Id(Node):

    def __init__(self, lineno, name):
        super().__init__(lineno)
        assert '.' not in name, 'variable mustn\'t include dot'
        assert not name.startswith('_'), 'variable mustn\'t starts with _'
        self.name = name

    def eval(self):
        return self.name

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = eval(self.name, ctx.globals, ctx.locals)
        ctx.line_stack.pop()
        return result


class BasicType(Node):

    def __init__(self, lineno, value):
        super().__init__(lineno)
        self.value = value

    def eval(self):
        value = self.value
        if value is True:
            return 'True'
        if value is False:
            return 'False'
        if value is None:
            return 'None'
        if isinstance(value, int):
            return str(value)
        raise TypeError('unknown type: {}'.format(type(value)))

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = self.value
        ctx.line_stack.pop()
        return result


class StringType(Node):

    def __init__(self, lineno, value):
        super().__init__(lineno)
        self.value = value

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = self.value
        ctx.line_stack.pop()
        return result


class UnaryExpression(Node):

    def __init__(self, lineno, operation, expression):
        super().__init__(lineno)
        self.operation = operation
        self.expression = expression

    async def touch(self, ctx):
        ctx.line_stack.append(self.lineno)
        result = eval('{} {}'.format(self.operation, self.expression.eval()),
                      ctx.globals, ctx.locals)
        ctx.line_stack.pop()
        return result


# Interpretier
class Interpreter(object):

    async def run(self, bytecode, ctx=None):
        if ctx is None:
            ctx = context.Context()

        try:
            result = await bytecode.touch(ctx)

        except Exception as e:
            #logger.error('Error while executing esl script:')
            logger.error('{}: {}'.format(type(e).__name__, e))

            if hasattr(bytecode, 'code'):
                lines = bytecode.code.split('\n')
                parent_fun = '<main>'
                for fun, lineno in ctx.call_stack:
                    logger.error('... {} line {}: {}()'.format(parent_fun,
                                                              lineno, fun))
                    parent_fun = fun

                lastline = ctx.line_stack[-1]
                if lastline <= len(lines):
                    line = lines[lastline - 1].strip()[:50]
                    logger.error('... {} line {}: `{}\' ...'.format(parent_fun,
                                                                   lastline,
                                                                   line))
                else:
                    logger.error('... {} line {}: can\' find source '
                                 'line '.format(parent_fun, lastline))

                t, val, tb = sys.exc_info()
                message = str(val)
                if message:
                    message = '{}: {}'.format(t.__name__, message)
                else:
                    message = t.__name__

                logger.debug('Python traceback:')
                for file, line, fun, inst in traceback.extract_tb(tb):
                    logger.debug('... {} line {} in {}()'.format(file[-40:],
                                                                line, fun))
                logger.debug('...   {}'.format(inst))

            raise RuntimeError(str(e))

        return result
