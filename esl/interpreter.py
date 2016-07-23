__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(C) 2010 Business group of development management'
__licence__ = 'GPL'

__all__ = ['Interpreter',
           'Id', 'Attribute', 'BasicType', 'Array', 'ArrayElement',
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

from . import context


logger = logging.getLogger('edera.esl.interpreter')


# nodes
class Node(object):
    def __init__(self, lineno):
        self.lineno = lineno

    def touch(self, ctx):
        raise NotImplementedError('method %s.touch() not implemented yet.' % self.__class__.__name__)

    def quote(self, value):
        if isinstance(value, str):
            value = value.replace('"', '\\"')
            return '"{}"'.format(value)
        else:
            return (value)


class NodeList(Node):
    def __init__(self, lineno):
        self.children = []
        super(NodeList, self).__init__(lineno)

    def __getitem__(self, k):
        return self.children[k]

    def __setitem__(self, k, v):
        self.children[k] = v

    def add(self, node):
        self.children.append(node)


class TranslationUnit(NodeList):
    def __init__(self, lineno, node):
        super(TranslationUnit, self).__init__(lineno)
        self.add(node)

    def __str__(self):
        return ' '.join([ str(x) for x in self.children])

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        for statement in self.children:
            if len(ctx.loops) > 0:
                loop = ctx.loops[-1]
                if loop.must_break or loop.must_continue:
                    continue
            result = statement.touch(ctx)
            if ctx.must_return:
                ctx.pop_line()
                return result
        ctx.pop_line()
        return result


class ImportStatement(Node):
    def __init__(self, parser, lineno, id):
        super(ImportStatement, self).__init__(lineno)
        self.parser = parser
        self.id = id

    def __str__(self):
        return 'import %s;' % self.id

    def touch(self, ctx):
        if ctx.import_handler is None:
            raise RuntimeError('please setup import handler')
        code = ctx.import_handler(self.id.name)
        bytecode = self.parser.parse(code)
        return bytecode.touch(ctx)


class FunctionObject(object):
    def __init__(self, name, parameters, compound_statement):
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
        super(FunctionStatement, self).__init__(lineno)
        self.id = id
        self.declaration = declaration
        self.compound_statement = compound_statement

    def __str__(self):
        if self.declaration is None:
            declaration = ''
        else:
            declaration = str(self.declaration)
        return 'function %s (%s) %s' % (str(self.id), declaration, str(self.compound_statement))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
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
        ctx.pop_line()


class Declaration(NodeList):
    def __init__(self, lineno):
        super(Declaration, self).__init__(lineno)

    def __str__(self):
        return ', '.join([str(x) for x in self.children])


class Return(Node):
    def __init__(self, lineno, expression):
        super(Return, self).__init__(lineno)
        self.expression = expression

    def __str__(self):
        return 'return %s' % str(self.expression)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        ctx.must_return = True
        result = self.expression.touch(ctx)
        ctx.pop_line()
        return result


class IfStatement(NodeList):
    def __init__(self, lineno, if_expression, compound_statement, elif_statement, else_statement):
        super(IfStatement, self).__init__(lineno)
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

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        if bool(self.if_expression.touch(ctx)):
            result = self.compound_statement.touch(ctx)
            ctx.pop_line()
            return result
        else:
            if self.elif_statement is not None:
                for expression, statement in self.elif_statement.children:
                    if bool(expression.touch(ctx)):
                        result = statement.touch(ctx)
                        ctx.pop_line()
                        return result

            if self.else_statement is not None:
                result = self.else_statement.compound_statement.touch(ctx)
                ctx.pop_line()
                return result


class ElIfStatement(NodeList):
    def __init__(self, lineno):
        super(ElIfStatement, self).__init__(lineno)

    def __str__(self):
        return ' '.join ([ 'elif (%s) %s' % (str(x[0]), str(x[1])) for x in self.children ])


class ElseStatement(Node):
    def __init__(self, lineno, compound_statement):
        super(ElseStatement, self).__init__(lineno)
        self.compound_statement = compound_statement

    def __str__(self):
        return 'else %s' % str(self.compound_statement)


class SpecialIfStatement(Node):
    def __init__(self, lineno, expression, if_expression):
        super(SpecialIfStatement, self).__init__(lineno)
        self.expression = expression
        self.if_expression = if_expression

    def __str__(self):
        return '%s if (%s);' % (str(self.expression), str(self.if_expression))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = None
        if bool(self.if_expression.touch(ctx)):
            result = self.expression.touch(ctx)
        ctx.pop_line()
        return result


class UnlessStatement(Node):
    def __init__(self, lineno, expression, if_expression):
        super(UnlessStatement, self).__init__(lineno)
        self.expression = expression
        self.if_expression = if_expression

    def __str__(self):
        return '%s unless (%s);' % (str(self.expression), str(self.if_expression))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = None
        if not bool(self.if_expression.touch(ctx)):
            result = self.expression.touch(ctx)
        ctx.pop_line()
        return result


class ForStatement(Node):
    def __init__(self, lineno, init_expression, relative_expression, increment_expression, compound_statement):
        super(ForStatement, self).__init__(lineno)
        self.init_expression = init_expression
        self.relative_expression = relative_expression
        self.increment_expression = increment_expression
        self.compound_statement = compound_statement
        self.must_break = False
        self.must_continue = False

    def __str__(self):
        return 'for (%s; %s; %s) %s' % (self.init_expression, self.relative_expression, self.increment_expression, self.compound_statement)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
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
        ctx.pop_line()


class ForInStatement(Node):
    def __init__(self, lineno, id, expression, compound_statement):
        super(ForInStatement, self).__init__(lineno)
        self.id = id
        self.expression = expression
        self.compound_statement = compound_statement
        self.must_break = False
        self.must_continue = False

    def __str__(self):
        return 'for (%s in %s) %s' % (self.id, self.expression, self.compound_statement)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
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
        ctx.pop_line()


class WhileStatement(Node):
    def __init__(self, lineno, expression, compound_statement):
        super(WhileStatement, self).__init__(lineno)
        self.expression = expression
        self.compound_statement = compound_statement
        self.must_break = False
        self.must_continue = False

    def __str__(self):
        return 'while (%s) %s' % (self.expression, self.compound_statement)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
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
        ctx.pop_line()


class LoopCommandStatement(Node):
    def __init__(self, lineno, command):
        super(LoopCommandStatement, self).__init__(lineno)
        self.command = command

    def __str__(self):
        return '%s' % self.command

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        if len(ctx.loops) < 1:
            raise RuntimeError('`%s\' statement without loop.' % self.command)
        if self.command == 'break':
            ctx.loops[-1].must_break = True
        elif self.command == 'continue':
            ctx.loops[-1].must_continue = True
        else:
            raise RuntimeError('unknown loop command `%s\'.' % type(self.command))
        ctx.pop_line()


class CompoundStatement(Node):
    def __init__(self, lineno, translation_unit):
        super(CompoundStatement, self).__init__(lineno)
        self.translation_unit = translation_unit

    def __str__(self):
        return '{%s}' % str(self.translation_unit)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = self.translation_unit.touch(ctx)
        ctx.pop_line()
        return result


class ExpressionStatement(Node):
    def __init__(self, lineno, expression):
        super(ExpressionStatement, self).__init__(lineno)
        self.expression = expression

    def __str__(self):
        return '%s;' % str(self.expression)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = self.expression.touch(ctx)
        ctx.pop_line()
        return result


class VariableAssignment(Node):
    def __init__(self, lineno, key, operation, expression):
        super(VariableAssignment, self).__init__(lineno)
        self.key = key
        self.operation = operation
        self.expression = expression

    def __str__(self):
        return '(%s %s %s)' % (self.key, self.operation, str(self.expression))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        value = self.expression.touch(ctx)

        if self.operation == '+=':
            value = self.key.touch(ctx) + value
        elif self.operation == '-=':
            value = self.key.touch(ctx) - value

        # attribute assignment
        var = self.key

        if isinstance(var, Attribute):
            if var.id.name.count('.') == 0:
                var = var.id
            else:
                parent_id, id = var.id.name.rsplit('.', 1)
                parent = Attribute(self.lineno, Id(self.lineno, parent_id)).touch(ctx)
                setattr(parent, id, value)

        # id assignment
        if isinstance(var, Id):
            if not ctx.has_key(var.name):
                ctx.addLocal(var.name, value)
            else:
                ctx.set(var.name, value)

        # array element asignment
        if isinstance(var, ArrayAccess):
            array = ctx.get(var.id.name)
            array_key = var.expression.touch(ctx)
            array.__setitem__(array_key, value)

        ctx.pop_line()


class IncrementExpression(VariableAssignment):
    def __init__(self, lineno, id, operation):
        self.id = id
        expression = BinaryExpression(lineno, id, '+', BasicType(lineno, operation == '++' and 1 or - 1))
        super(IncrementExpression, self).__init__(lineno, id, operation, expression)

    def __str__(self):
        return '(%s%s)' % (self.id, self.operation)


class LogicalExpression(Node):
    def __init__(self, lineno, left, operation, right):
        super(LogicalExpression, self).__init__(lineno)
        self.left = left
        self.operation = operation
        self.right = right

    def __str__(self):
        return '(%s %s %s)' % (str(self.left), self.operation, str(self.right))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        left = self.quote(self.left.touch(ctx))
        right = self.quote(self.right.touch(ctx))
        result = eval('%s %s %s' % (left, self.operation, right), ctx.getGlobals(), ctx.getLocals())
        ctx.pop_line()
        return result


class RelationalExpression(Node):
    def __init__(self, lineno, left, operation, right):
        super(RelationalExpression, self).__init__(lineno)
        self.left = left
        self.operation = operation
        self.right = right

    def __str__(self):
        return '(%s %s %s)' % (str(self.left), self.operation, str(self.right))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        left = self.quote(self.left.touch(ctx))
        right = self.quote(self.right.touch(ctx))
        result = eval('%s %s %s' % (left, self.operation, right), ctx.getGlobals(), ctx.getLocals())
        ctx.pop_line()
        return result


class BinaryExpression(Node):
    def __init__(self, lineno, left, operation, right):
        super(BinaryExpression, self).__init__(lineno)
        self.left = left
        self.operation = operation
        self.right = right

    def __str__(self):
        return '(%s %s %s)' % (str(self.left), self.operation, str(self.right))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        left = self.quote(self.left.touch(ctx))
        right = self.quote(self.right.touch(ctx))
        result = eval("%s %s %s" % (left, self.operation, right), ctx.getGlobals(), ctx.getLocals())
        ctx.pop_line()
        return result


class Call(Node):
    def __init__(self, lineno, attribute, parameters):
        super(Call, self).__init__(lineno)
        self.attribute = attribute
        self.parameters = parameters

    def __str__(self):
        if self.parameters is None:
            parameters = ''
        else:
            parameters = str(self.parameters)
        return '%s(%s)' % (str(self.attribute), parameters)

    def touch(self, ctx):
        ctx.push_line(self.lineno)

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


        ctx.pop_line()
        return result


class CallElement(NodeList):
    def __init__(self, lineno):
        super(CallElement, self).__init__(lineno)

    def __str__(self):
        return ', '.join([str(x) for x in self.children])


class Hash(Node):
    def __init__(self, lineno, element):
        super(Hash, self).__init__(lineno)
        self.element = element

    def __str__(self):
        return '{%s}' % str(self.element)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = dict(self.element.touch(ctx))
        ctx.pop_line()
        return result


class HashElement(NodeList):
    def __init__(self, lineno):
        super(HashElement, self).__init__(lineno)

    def __str__(self):
        return ', '.join([str(k) + ': ' + str(v) for k, v in self.children])

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = map(lambda x: (x[0].touch(ctx), x[1].touch(ctx)), self.children)
        ctx.pop_line()
        return result


class Array(Node):
    def __init__(self, lineno, element):
        super(Array, self).__init__(lineno)
        self.element = element

    def __str__(self):
        return '[%s]' % (self.element is not None and str(self.element) or '')

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        if self.element is None:
            result = list()
        else:
            result = list(self.element.touch(ctx))
        ctx.pop_line()
        return result


class ArrayElement(NodeList):
    def __init__(self, lineno):
        super(ArrayElement, self).__init__(lineno)

    def __str__(self):
        return ', '.join([str(x) for x in self.children])

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = [ x.touch(ctx) for x in self.children ]
        ctx.pop_line()
        return result


class ArrayAccess(Node):
    def __init__(self, lineno, id, expression):
        super(ArrayAccess, self).__init__(lineno)
        self.id = id
        self.expression = expression

    def __str__(self):
        return '%s[%s]' % (str(self.id), str(self.expression))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        array = self.id.touch(ctx)
        result = array.__getitem__(self.expression.touch(ctx))
        ctx.pop_line()
        return result


class Attribute(Node):
    def __init__(self, lineno, id):
        super(Attribute, self).__init__(lineno)
        self.id = id

    def __str__(self):
        return '%s' % str(self.id.name)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = eval(self.id.name, ctx.getGlobals(), ctx.getLocals())
        ctx.pop_line()
        return result


class Id(Node):
    def __init__(self, lineno, name):
        super(Id, self).__init__(lineno)
        self.name = name

    def __str__(self):
        return str(self.name)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = ctx.get(self.name)
        ctx.pop_line()
        return result


class BasicType(Node):
    def __init__(self, lineno, value):
        super(BasicType, self).__init__(lineno)
        self.value = value

    def __str__(self):
        if isinstance(self.value, str):
            return '"%s"' % self.value
        if self.value is True:
            return 'true'
        if self.value is False:
            return 'false'
        if self.value is None:
            return 'null'
        return str(self.value)

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        result = self.value
        ctx.pop_line()
        return result


class UnaryExpression(Node):
    def __init__(self, lineno, operation, expression):
        super(UnaryExpression, self).__init__(lineno)
        self.operation = operation
        self.expression = expression

    def __str__(self):
        return '(%s %s)' % (self.operation, str(self.expression))

    def touch(self, ctx):
        ctx.push_line(self.lineno)
        value = self.quote(self.expression.touch(ctx))
        result = eval('%s %s' % (self.operation, value), ctx.getGlobals(), ctx.getLocals())
        ctx.pop_line()
        return result


class ESLRuntimeError(Exception):
    pass


# interpretier
class Interpreter(object):

    def run(self, bytecode, ctx=None):
        if ctx is None:
            ctx = context.Context()

        try:
            result = bytecode.touch(ctx)
        except Exception as e:
            logger.error('Ошибка при выполнении скрипта: {}'.format(e))

            if hasattr(bytecode, 'code'):
                lines = bytecode.code.split('\n')
                parent_fun = '<main>'
                for fun, lineno in ctx.call_stack:
                    logger.error('... {} стр {}: {}()'.format(parent_fun,
                                                              lineno, fun))
                    parent_fun = fun

                lastline = ctx.line_stack[-1]
                if lastline <= len(lines):
                    line = lines[lastline - 1].strip()[:50]
                    logger.error('... {} стр {}: `{}\' ...'.format(parent_fun,
                                                                   lastline,
                                                                   line))
                else:
                    logger.error('... {} стр {}: не смог насти строку '
                                 'с кодом'.format(parent_fun, lastline))

                t, val, tb = sys.exc_info()
                message = str(val)
                if message:
                    message = '{}: {}'.format(t.__name__, message)
                else:
                    message = t.__name__

                logger.error('Python traceback:')
                for file, line, fun, inst in traceback.extract_tb(tb):
                    logger.error('... {} стр {} in {}()'.format(file[-40:],
                                                                line, fun))
                logger.error('...   {}'.format(inst))

            raise ESLRuntimeError(str(e))

        return result
