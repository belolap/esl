__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

import decimal
import ply.yacc

from . import lex
from . import interpreter


# Parser as is
class Parser(lex.Lexer):

    def __init__(self, debug=False):
        self.build()

        # Create yacc
        self.yacc = ply.yacc.yacc(module=self, write_tables=True, debug=debug)

    # Rules
    def p_translation_unit1(self, p):
        '''
        translation_unit : statement
        '''
        p[0] = interpreter.TranslationUnit(p.lineno(0), p[1])

    def p_translation_unit2(self, p):
        '''
        translation_unit : translation_unit statement
        '''
        p[1].add(p[2])
        p[0] = p[1]

    def p_translation_unit3(self, p):
        '''
        translation_unit : empty
        '''
        p[0] = p[1]

    # Empty
    def p_empty1(self, p):
        '''
        empty :
        '''
        p[0] = ''

    # Statement
    def p_statement1(self, p):
        '''
        statement : import_statement
                    | function_statement
                    | if_statement
                    | special_if_statement
                    | unless_statement
                    | for_statement
                    | forin_statement
                    | while_statement
                    | expression_statement
        '''
        p[0] = p[1]

    # Import statement
    def p_import_statement1(self, p):
        '''
        import_statement : IMPORT id SEMICOLON
        '''
        p[0] = interpreter.ImportStatement(self, p.lineno(0), p[2])

    # Function statement
    def p_function_statement1(self, p):
        '''
        function_statement : FUNCTION id LPAREN RPAREN compound_statement
        '''
        p[0] = interpreter.FunctionStatement(p.lineno(0), p[2], None, p[5])

    def p_function_statement2(self, p):
        '''
        function_statement : FUNCTION id LPAREN declaration_expression RPAREN compound_statement
        '''
        p[0] = interpreter.FunctionStatement(p.lineno(0), p[2], p[4], p[6])

    # Declaration expression
    def p_declaration_expression1(self, p):
        '''
        declaration_expression : id
        '''
        p[0] = interpreter.Declaration(p.lineno(0))
        p[0].add(p[1])

    def p_declaration_expression2(self, p):
        '''
        declaration_expression : declaration_expression COMMA id
        '''
        p[1].add(p[3])
        p[0] = p[1]

    # If, elif, else statements
    def p_if_statement1(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement
        '''
        p[0] = interpreter.IfStatement(p.lineno(0), p[3], p[5], None, None)

    def p_if_statement2(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement elif_statement
        '''
        p[0] = interpreter.IfStatement(p.lineno(0), p[3], p[5], p[6], None)

    def p_if_statement3(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement elif_statement else_statement
        '''
        p[0] = interpreter.IfStatement(p.lineno(0), p[3], p[5], p[6], p[7])

    def p_if_statement4(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement else_statement
        '''
        p[0] = interpreter.IfStatement(p.lineno(0), p[3], p[5], None, p[6])

    def p_elif_statement1(self, p):
        '''
        elif_statement : ELIF LPAREN conditional_expression RPAREN compound_statement
        '''
        p[0] = interpreter.ElIfStatement(p.lineno(0))
        p[0].add((p[3], p[5]))

    def p_elif_statement2(self, p):
        '''
        elif_statement : elif_statement ELIF LPAREN conditional_expression RPAREN compound_statement
        '''
        p[1].add((p[4], p[6]))
        p[0] = p[1]

    def p_else_statement1(self, p):
        '''
        else_statement : ELSE compound_statement
        '''
        p[0] = interpreter.ElseStatement(p.lineno(0), p[2])

    # Special if statement
    def p_special_if_statement1(self, p):
        '''
        special_if_statement : assignment_expression IF LPAREN conditional_expression RPAREN SEMICOLON
                        | expression IF LPAREN conditional_expression RPAREN SEMICOLON
        '''
        p[0] = interpreter.SpecialIfStatement(p.lineno(0), p[1], p[4])

    # Unless statement
    def p_unless_statement1(self, p):
        '''
        unless_statement : assignment_expression UNLESS LPAREN conditional_expression RPAREN SEMICOLON
                        | expression UNLESS LPAREN conditional_expression RPAREN SEMICOLON
        '''
        p[0] = interpreter.UnlessStatement(p.lineno(0), p[1], p[4])

    # For statement
    def p_for_statement1(self, p):
        '''
        for_statement : FOR LPAREN single_id_assignment_expression SEMICOLON expression SEMICOLON increment_expression RPAREN compound_statement
        '''
        p[0] = interpreter.ForStatement(p.lineno(0), p[3], p[5], p[7], p[9])

    # For..in statement
    def p_forin_statement1(self, p):
        '''
        forin_statement : FOR LPAREN id IN expression RPAREN compound_statement
        '''
        p[0] = interpreter.ForInStatement(p.lineno(0), p[3], p[5], p[7])

    # While statement
    def p_while_statement1(self, p):
        '''
        while_statement : WHILE LPAREN expression RPAREN compound_statement
        '''
        p[0] = interpreter.WhileStatement(p.lineno(0), p[3], p[5])

    # Compound statement
    def p_compound_statement1(self, p):
        '''
        compound_statement : LBRACE translation_unit RBRACE
        '''
        p[0] = interpreter.CompoundStatement(p.lineno(0), p[2])

    # Expression statement
    def p_expression_statement1(self, p):
        '''
        expression_statement : assignment_expression SEMICOLON
                    | increment_expression SEMICOLON
                    | break SEMICOLON
                    | continue SEMICOLON
                    | return SEMICOLON
                    | expression SEMICOLON
        '''
        p[0] = interpreter.ExpressionStatement(p.lineno(0), p[1])

    # Assignment expression
    def p_assignment_expression1(self, p):
        '''
        assignment_expression : multiple_assignment_expression
                            | increment_assignment_expression
        '''
        p[0] = p[1]

    def p_multiple_assignment_expression1(self, p):
        '''
        multiple_assignment_expression : attribute ASSIGN multiple_assignment_expression
                            | array_access ASSIGN multiple_assignment_expression
        '''
        p[0] = interpreter.VariableAssignment(p.lineno(0), p[1], p[3])

    def p_multiple_assignment_expression2(self, p):
        '''
        multiple_assignment_expression : single_id_assignment_expression
                            | single_array_assignment_expression
        '''
        p[0] = p[1]

    def p_single_id_assignment_expression1(self, p):
        '''
        single_id_assignment_expression : attribute ASSIGN expression
        '''
        p[0] = interpreter.VariableAssignment(p.lineno(0), p[1], p[3])

    def p_single_array_assignment_expression1(self, p):
        '''
        single_array_assignment_expression : array_access ASSIGN expression
        '''
        p[0] = interpreter.VariableAssignment(p.lineno(0), p[1], p[3])

    def p_increment_assignment_expression(self, p):
        '''
        increment_assignment_expression : attribute EQ_PLUS expression
                            | attribute EQ_MINUS expression
                            | array_access EQ_PLUS expression
                            | array_access EQ_MINUS expression
        '''
        p[0] = interpreter.IncrementAssignment(p.lineno(0), p[1], p[2], p[3])

    # Increment expression
    def p_increment_expression1(self, p):
        '''
        increment_expression : id DOUBLE_PLUS
                            | id DOUBLE_MINUS
        '''
        operation = {'++': '+=', '--': '-='}.get(p[2])
        one = interpreter.BasicType(p.lineno(0), 1)
        p[0] = interpreter.IncrementAssignment(p.lineno(0), p[1], operation, one)

    # Break expression
    def p_break_statement1(self, p):
        '''
        break : BREAK
        '''
        p[0] = interpreter.LoopCommandStatement(p.lineno(0), p[1])

    # Continue expression
    def p_continue_statement1(self, p):
        '''
        continue : CONTINUE
        '''
        p[0] = interpreter.LoopCommandStatement(p.lineno(0), p[1])

    # Return expression
    def p_return_statement1(self, p):
        '''
        return : RETURN expression
        '''
        p[0] = interpreter.Return(p.lineno(0), p[2])

    # Expression
    def p_expression1(self, p):
        '''
        expression : group_expression
                    | conditional_expression
                    | multiplicative_expression
                    | additive_expression
                    | primary_expression
                    | unary_expression
        '''
        p[0] = p[1]

    # Group expression
    def p_group_expression1(self, p):
        '''
        group_expression : LPAREN expression RPAREN
        '''
        p[0] = p[2]

    # Conditional expression
    def p_conditional_expression1(self, p):
        '''
        conditional_expression : logical_expression
                    | relational_expression
        '''
        p[0] = p[1]

    # Logical expression
    def p_logical_expression1(self, p):
        '''
        logical_expression : logical_or_expression
                    | logical_and_expression
                    | logical_not_expression
        '''
        p[0] = p[1]

    def p_logical_or_expression1(self, p):
        '''
        logical_or_expression : expression OR expression
        '''
        p[0] = interpreter.LogicalExpression(p.lineno(0), p[1], p[2], p[3])

    def p_logical_and_expression1(self, p):
        '''
        logical_and_expression : expression AND expression
        '''
        p[0] = interpreter.LogicalExpression(p.lineno(0), p[1], p[2], p[3])

    def p_logical_not_expression1(self, p):
        '''
        logical_not_expression : NOT expression
        '''
        p[0] = interpreter.LogicalExpression(p.lineno(0), None, p[1], p[2])

    # Relational expression
    def p_relational_expression1(self, p):
        '''
        relational_expression : expression EQUAL expression
                            | expression NOT_EQUAL expression
                            | expression LESS expression
                            | expression GREATER expression
                            | expression LESS_EQUAL expression
                            | expression GREATER_EQUAL expression
        '''
        p[0] = interpreter.RelationalExpression(p.lineno(0), p[1], p[2], p[3])

    # Additive expression
    def p_additive_expression1(self, p):
        '''
        additive_expression : expression PLUS expression
                    | expression MINUS expression
        '''
        p[0] = interpreter.BinaryExpression(p.lineno(0), p[1], p[2], p[3])

    # Multiplicative expression
    def p_multiplicative_expression1(self, p):
        '''
        multiplicative_expression : expression TIMES expression
                    | expression DIVIDE expression

        '''
        p[0] = interpreter.BinaryExpression(p.lineno(0), p[1], p[2], p[3])

    # Primary expression
    def p_primary_expression1(self, p):
        '''
        primary_expression : call
                    | hash
                    | array
                    | array_access
                    | attribute
                    | constant
        '''
        p[0] = p[1]

    # Call
    def p_call1(self, p):
        '''
        call : attribute LPAREN RPAREN
        '''
        p[0] = interpreter.Call(p.lineno(0), p[1], None)

    def p_call2(self, p):
        '''
        call : attribute LPAREN call_element RPAREN
        '''
        p[0] = interpreter.Call(p.lineno(0), p[1], p[3])

    def p_call_element1(self, p):
        '''
        call_element : expression
                    | id ASSIGN expression
        '''
        p[0] = interpreter.CallElement(p.lineno(0))
        if len(p) == 2:
            p[0].add(p[1])
        else:
            p[0].add(interpreter.VariableAssignment(p.lineno(0), p[1], p[3]))

    def p_call_element2(self, p):
        '''
        call_element : call_element COMMA expression
                    | call_element COMMA id ASSIGN expression
        '''
        if len(p) == 4:
            p[1].add(p[3])
        else:
            p[1].add(interpreter.VariableAssignment(p.lineno(0), p[3], p[5]))
        p[0] = p[1]

    # Array
    def p_array1(self, p):
        '''
        array : LBRACKET RBRACKET
        '''
        p[0] = interpreter.Array(p.lineno(0), None)

    def p_array2(self, p):
        '''
        array : LBRACKET array_element RBRACKET
        '''
        p[0] = interpreter.Array(p.lineno(0), p[2])

    def p_array_element1(self, p):
        '''
        array_element : expression
        '''
        p[0] = interpreter.ArrayElement(p.lineno(0))
        p[0].add(p[1])

    def p_array_element2(self, p):
        '''
        array_element : array_element COMMA expression
        '''
        p[1].add(p[3])
        p[0] = p[1]

    # Hash
    def p_hash1(self, p):
        '''
        hash : LBRACE RBRACE
        '''
        p[0] = interpreter.Hash(p.lineno(0))

    def p_hash2(self, p):
        '''
        hash : LBRACE hash_element RBRACE
        '''
        p[0] = interpreter.Hash(p.lineno(0), p[2])

    def p_hash_element1(self, p):
        '''
        hash_element : constant COLON expression
                    | attribute COLON expression
        '''
        p[0] = interpreter.HashElement(p.lineno(0))
        p[0].add((p[1], p[3]))

    def p_hash_element2(self, p):
        '''
        hash_element : hash_element COMMA hash_element
        '''
        for k, v in p[3].children:
            p[1].add((k, v))
        p[0] = p[1]

    # Array_access
    def p_array_access1(self, p):
        '''
        array_access : attribute LBRACKET expression RBRACKET
        '''
        p[0] = interpreter.ArrayAccess(p.lineno(0), p[1], p[3])

    # Attribute
    def p_attribute1(self, p):
        '''
        attribute : id
        '''
        p[0] = interpreter.Attribute(p.lineno(0), None, p[1])

    def p_attribute2(self, p):
        '''
        attribute : attribute DOT id
        '''
        p[0] = interpreter.Attribute(p.lineno(0), p[1], p[3])

    # Id
    def p_id1(self, p):
        '''
        id : ID
        '''
        p[0] = interpreter.Id(p.lineno(0), p[1])

    # Constants
    def p_constant1(self, p):
        '''
        constant : INTEGER
        '''
        p[0] = interpreter.BasicType(p.lineno(0), int(p[1]))

    def p_constant2(self, p):
        '''
        constant : STRING
        '''
        value = p[1]
        if value.startswith('\''):
            symbol = '\''
        else:
            symbol = '"'
        p[0] = interpreter.StringType(p.lineno(0), value.strip(symbol))

    def p_constant3(self, p):
        '''
        constant : DECIMAL
        '''
        p[0] = interpreter.BasicType(p.lineno(0), decimal.Decimal(p[1]))

    def p_constant4(self, p):
        '''
        constant : TRUE
        '''
        p[0] = interpreter.BasicType(p.lineno(0), True)

    def p_constant5(self, p):
        '''
        constant : FALSE
        '''
        p[0] = interpreter.BasicType(p.lineno(0), False)

    def p_constant6(self, p):
        '''
        constant : NULL
        '''
        p[0] = interpreter.BasicType(p.lineno(0), None)

    # Unary expression
    def p_unary_expression1(self, p):
        '''
        unary_expression : unary_operator expression
        '''
        p[0] = interpreter.UnaryExpression(p.lineno(0), p[1], p[2])

    # Unary operator
    def p_unary_operator1(self, p):
        '''
        unary_operator : MINUS
                    | PLUS
        '''
        p[0] = p[1]

    # Error handling
    def p_error(self, p):
        if p is not None:
            startpos = getattr(p.lexer, 'startpos', 1)
            column = p.lexer.lexpos - startpos
            raise lex.SyntaxError(
                    self.error_msg('can\'t parse', p.lineno, column, p.value))
        else:
            startpos = getattr(self.lexer, 'startpos', 1)
            column = self.lexer.lexpos - startpos + 1
            raise lex.SyntaxError(
                    self.error_msg('can\'t parse', self.lexer.lineno, column,
                                   self.lexer.lexdata))

    # Parser
    def parse(self, code):
        lexer = self.lexer.clone()
        bytecode = self.yacc.parse(code, lexer=lexer, tracking=True)
        if bytecode:
            bytecode.code = code
        return bytecode

    # Utils
    def get(self, name):
        if self.__locals.has_key(name):
            return self.__locals.get(name)
        return self.__globals.get(name)
