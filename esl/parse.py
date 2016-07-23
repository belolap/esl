__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(C) 2010 Business group of development management'
__licence__ = 'GPL'

from ply.yacc import yacc
from decimal import Decimal

from edera.esl.lex import ESLLex
from edera.esl.interpreter import *


# Parser as is
class Parser(ESLLex):

    def __init__(self):
        self.build()

        # create yacc
        self.yacc = yacc(module=self, debug=0)

    # rules
    def p_translation_unit1(self, p):
        '''
        translation_unit : statement
        '''
        p[0] = TranslationUnit(p.lineno(0), p[1])

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

    # empty
    def p_empty1(self, p):
        '''
        empty :
        '''
        p[0] = ''

    # statement
    def p_statement1(self, p):
        '''
        statement : expression_statement
                    | import_statement
                    | function_statement
                    | if_statement
                    | special_if_statement
                    | unless_statement
                    | for_statement
                    | forin_statement
                    | while_statement
        '''
        p[0] = p[1]

    # import statement
    def p_import_statement1(self, p):
        '''
        import_statement : IMPORT id SEMICOLON
        '''
        p[0] = ImportStatement(self, p.lineno(0), p[2])

    # function statement
    def p_function_statement1(self, p):
        '''
        function_statement : FUNCTION id LPAREN RPAREN compound_statement
        '''
        p[0] = FunctionStatement(p.lineno(0), p[2], None, p[5])

    def p_function_statement2(self, p):
        '''
        function_statement : FUNCTION id LPAREN declaration RPAREN compound_statement
        '''
        p[0] = FunctionStatement(p.lineno(0), p[2], p[4], p[6])

    # declaration statement
    def p_declaration1(self, p):
        '''
        declaration : id
        '''
        p[0] = Declaration(p.lineno(0))
        p[0].add(p[1])

    def p_declaration2(self, p):
        '''
        declaration : declaration COMMA id
        '''
        p[1].add(p[3])
        p[0] = p[1]

    # if, elif, else statements
    def p_if_statement1(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement
        '''
        p[0] = IfStatement(p.lineno(0), p[3], p[5], None, None)

    def p_if_statement2(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement elif_statement
        '''
        p[0] = IfStatement(p.lineno(0), p[3], p[5], p[6], None)

    def p_if_statement3(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement elif_statement else_statement
        '''
        p[0] = IfStatement(p.lineno(0), p[3], p[5], p[6], p[7])

    def p_if_statement4(self, p):
        '''
        if_statement : IF LPAREN conditional_expression RPAREN compound_statement else_statement
        '''
        p[0] = IfStatement(p.lineno(0), p[3], p[5], None, p[6])

    def p_elif_statement1(self, p):
        '''
        elif_statement : ELIF LPAREN conditional_expression RPAREN compound_statement
        '''
        p[0] = ElIfStatement(p.lineno(0))
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
        p[0] = ElseStatement(p.lineno(0), p[2])

    # special if statement
    def p_special_if_statement1(self, p):
        '''
        special_if_statement : expression IF LPAREN conditional_expression RPAREN SEMICOLON
        '''
        p[0] = SpecialIfStatement(p.lineno(0), p[1], p[4])

    # unless statement
    def p_unless_statement1(self, p):
        '''
        unless_statement : expression UNLESS LPAREN conditional_expression RPAREN SEMICOLON
        '''
        p[0] = UnlessStatement(p.lineno(0), p[1], p[4])


    # for statement
    def p_for_statement1(self, p):
        '''
        for_statement : FOR LPAREN expression SEMICOLON expression SEMICOLON expression RPAREN compound_statement
        '''
        p[0] = ForStatement(p.lineno(0), p[3], p[5], p[7], p[9])

    # for..in statement
    def p_forin_statement1(self, p):
        '''
        forin_statement : FOR LPAREN id IN expression RPAREN compound_statement
        '''
        p[0] = ForInStatement(p.lineno(0), p[3], p[5], p[7])

    # while statement
    def p_while_statement1(self, p):
        '''
        while_statement : WHILE LPAREN expression RPAREN compound_statement
        '''
        p[0] = WhileStatement(p.lineno(0), p[3], p[5])

    # compound statement
    def p_compound_statement1(self, p):
        '''
        compound_statement : LBRACE translation_unit RBRACE
        '''
        p[0] = CompoundStatement(p.lineno(0), p[2])

    # expression statement
    def p_expression_statement1(self, p):
        '''
        expression_statement : expression SEMICOLON
                    | break SEMICOLON
                    | continue SEMICOLON
                    | return SEMICOLON
        '''
        p[0] = ExpressionStatement(p.lineno(0), p[1])

    def p_break_statement1(self, p):
        '''
        break : BREAK
        '''
        p[0] = LoopCommandStatement(p.lineno(0), p[1])

    def p_continue_statement1(self, p):
        '''
        continue : CONTINUE
        '''
        p[0] = LoopCommandStatement(p.lineno(0), p[1])

    def p_return_statement1(self, p):
        '''
        return : RETURN expression
        '''
        p[0] = Return(p.lineno(0), p[2])

    # expression
    def p_expression1(self, p):
        '''
        expression : assignment_expression
        '''
        p[0] = p[1]

    # assignment expression
    def p_assignment_expression1(self, p):
        '''
        assignment_expression : increment_expression
        '''
        p[0] = p[1]

    def p_assignment_expression2(self, p):
        '''
        assignment_expression : attribute ASSIGN assignment_expression
                            | attribute EQ_PLUS assignment_expression
                            | attribute EQ_MINUS assignment_expression
                            | array_access ASSIGN assignment_expression
                            | array_access EQ_PLUS assignment_expression
                            | array_access EQ_MINUS assignment_expression
        '''
        p[0] = VariableAssignment(p.lineno(0), p[1], p[2], p[3])

    def p_increment_expression1(self, p):
        '''
        increment_expression : conditional_expression
        '''
        p[0] = p[1]

    def p_increment_expression(self, p):
        '''
        increment_expression : id DOUBLE_PLUS
                            | id DOUBLE_MINUS
        '''
        p[0] = IncrementExpression(p.lineno(0), p[1], p[2])

    # conditional expression
    def p_conditional_expression1(self, p):
        '''
        conditional_expression : logical_or_expression
        '''
        p[0] = p[1]

    # logical or expression
    def p_logical_or_expression1(self, p):
        '''
        logical_or_expression : logical_and_expression
        '''
        p[0] = p[1]

    def p_logical_or_expression2(self, p):
        '''
        logical_or_expression : logical_or_expression OR logical_and_expression
        '''
        p[0] = LogicalExpression(p.lineno(0), p[1], p[2], p[3])

    # logical and expression
    def p_logical_and_expression1(self, p):
        '''
        logical_and_expression : equality_expression
        '''
        p[0] = p[1]

    def p_logical_and_expression2(self, p):
        '''
        logical_and_expression : logical_and_expression AND equality_expression
        '''
        p[0] = LogicalExpression(p.lineno(0), p[1], p[2], p[3])

    # equality expression
    def p_equality_expression1(self, p):
        '''
        equality_expression : relational_expression
        '''
        p[0] = p[1]

    def p_equality_expression2(self, p):
        '''
        equality_expression : equality_expression EQUAL relational_expression
                            | equality_expression NOT_EQUAL relational_expression
        '''
        p[0] = RelationalExpression(p.lineno(0), p[1], p[2], p[3])

    # relational expression
    def p_relational_expression1(self, p):
        '''
        relational_expression : additive_expression
        '''
        p[0] = p[1]

    def p_relational_expression2(self, p):
        '''
        relational_expression : relational_expression EQUAL additive_expression
                            | relational_expression NOT_EQUAL additive_expression
                            | relational_expression LESS additive_expression
                            | relational_expression GREATER additive_expression
                            | relational_expression LESS_EQUAL additive_expression
                            | relational_expression GREATER_EQUAL additive_expression
        '''
        p[0] = RelationalExpression(p.lineno(0), p[1], p[2], p[3])

    # additive expression
    def p_additive_expression1(self, p):
        '''
        additive_expression : multiplicative_expression
        '''
        p[0] = p[1]

    def p_additive_expression2(self, p):
        '''
        additive_expression : additive_expression PLUS multiplicative_expression
                    | additive_expression MINUS multiplicative_expression
        '''
        p[0] = BinaryExpression(p.lineno(0), p[1], p[2], p[3])

    # multiplicative expression
    def p_multiplicative_expression1(self, p):
        '''
        multiplicative_expression : unary_expression
        '''
        p[0] = p[1]

    def p_multiplicative_expression2(self, p):
        '''
        multiplicative_expression : multiplicative_expression TIMES unary_expression
                    | multiplicative_expression DIVIDE unary_expression

        '''
        p[0] = BinaryExpression(p.lineno(0), p[1], p[2], p[3])

    # unary expression
    def p_unary_expression1(self, p):
        '''
        unary_expression : postfix_expression
        '''
        p[0] = p[1]

    def p_unary_expression2(self, p):
        '''
        unary_expression : unary_operator unary_expression
        '''
        p[0] = UnaryExpression(p.lineno(0), p[1], p[2])

    # unary operator
    def p_unary_operator1(self, p):
        '''
        unary_operator : NOT
                    | MINUS
                    | PLUS
        '''
        p[0] = p[1]

    # postfix expression
    def p_postfix_expression1(self, p):
        '''
        postfix_expression : primary_expression
        '''
        p[0] = p[1]

    # primary expression
    def p_primary_expression1(self, p):
        '''
        primary_expression : call
                    | hash
                    | array
                    | array_access
                    | attribute
                    | id
                    | constant
        '''
        p[0] = p[1]

    def p_primary_expression2(self, p):
        '''
        primary_expression : LPAREN expression RPAREN
        '''
        p[0] = p[2]

    # call
    def p_call1(self, p):
        '''
        call : attribute LPAREN RPAREN
        '''
        p[0] = Call(p.lineno(0), p[1], None)

    def p_call2(self, p):
        '''
        call : attribute LPAREN call_element RPAREN
        '''
        p[0] = Call(p.lineno(0), p[1], p[3])

    # call element
    def p_call_element1(self, p):
        '''
        call_element : assignment_expression
        '''
        p[0] = CallElement(p.lineno(0))
        p[0].add(p[1])

    def p_call_element2(self, p):
        '''
        call_element : call_element COMMA assignment_expression
        '''
        p[1].add(p[3])
        p[0] = p[1]

    # hash
    def p_hash1(self, p):
        '''
        hash : LBRACE hash_element RBRACE
        '''
        p[0] = Hash(p.lineno(0), p[2])

    def p_hash_element1(self, p):
        '''
        hash_element : expression COLON expression
        '''
        p[0] = HashElement(p.lineno(0))
        p[0].add((p[1], p[3]))

    def p_hash_element2(self, p):
        '''
        hash_element : hash_element COMMA expression COLON expression
        '''
        p[1].add((p[3], p[5]))
        p[0] = p[1]

    # array
    def p_array1(self, p):
        '''
        array : LBRACKET RBRACKET
        '''
        p[0] = Array(p.lineno(0), None)

    def p_array2(self, p):
        '''
        array : LBRACKET array_element RBRACKET
        '''
        p[0] = Array(p.lineno(0), p[2])

    def p_array_element1(self, p):
        '''
        array_element : primary_expression
        '''
        p[0] = ArrayElement(p.lineno(0))
        p[0].add(p[1])

    def p_array_element2(self, p):
        '''
        array_element : array_element COMMA primary_expression
        '''
        p[1].add(p[3])
        p[0] = p[1]

    # array_access
    def p_array_access1(self, p):
        '''
        array_access : id LBRACKET expression RBRACKET
        '''
        p[0] = ArrayAccess(p.lineno(0), p[1], p[3])

    # attribute
    def p_attribute1(self, p):
        '''
        attribute : id
        '''
        p[0] = Attribute(p.lineno(0), p[1])

    def p_attribute2(self, p):
        '''
        attribute : attribute DOT id
        '''
        p[1].id.name += '.' + p[3].name
        p[0] = p[1]

    # id
    def p_id1(self, p):
        '''
        id : ID
        '''
        p[0] = Id(p.lineno(0), p[1])

    # constants
    def p_constant1(self, p):
        '''
        constant : INTEGER
        '''
        p[0] = BasicType(p.lineno(0), int(p[1]))

    def p_constant2(self, p):
        '''
        constant : STRING
        '''
        p[0] = BasicType(p.lineno(0), p[1].strip('"'))

    def p_constant3(self, p):
        '''
        constant : DECIMAL
        '''
        p[0] = BasicType(p.lineno(0), Decimal(p[1]))

    def p_constant4(self, p):
        '''
        constant : TRUE
        '''
        p[0] = BasicType(p.lineno(0), True)

    def p_constant5(self, p):
        '''
        constant : FALSE
        '''
        p[0] = BasicType(p.lineno(0), False)

    def p_constant6(self, p):
        '''
        constant : NULL
        '''
        p[0] = BasicType(p.lineno(0), None)


    # Error handling
    def p_error(self, p):
        if p is not None:
            startpos = getattr(p.lexer, 'startpos', 1)
            column = p.lexer.lexpos - startpos
            raise SyntaxError(self.error_msg('can\'t parse', p.lineno, column,
                p.value))
        else:
            startpos = getattr(self.lexer, 'startpos', 1)
            column = self.lexer.lexpos - startpos + 1
            raise SyntaxError(self.error_msg('can\'t parse', self.lexer.lineno,
                column, self.lexer.lexdata))

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


ESLParser = Parser
