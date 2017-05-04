#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import logging
import ply.yacc

import esl.lex
import esl.interpreter


logger = logging.getLogger('esl')


class ParseError(Exception):
    pass


class Parser(object):

    tokens = esl.lex.Lexer.tokens

    def __init__(self, debug=False, write_tables=False):
        self.lexer = esl.lex.Lexer()
        self.lexer.build()

        self.yacc = ply.yacc.yacc(module=self, debug=debug,
                                  write_tables=write_tables,
                                  errorlog=logger)

    def p_chunk(self, p):
        '''chunk : block'''
        p[0] = esl.interpreter.Chunk(p.lineno(0), p[1])

    def p_block1(self, p):
        '''block : blockpart'''
        p[0] = p[1]

    def p_block2(self, p):
        '''block : laststat
                 | blockpart laststat'''
        if len(p) == 2:
            p[0] = esl.interpreter.Block(p.lineno(0))
            p[0].append(p[1])
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_blockpart(self, p):
        '''blockpart : stat
                     | blockpart stat'''
        if len(p) == 2:
            p[0] = esl.interpreter.Block(p.lineno(0))
            p[0].append(p[1])
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_stat1(self, p):
        '''stat : empty'''
        p[0] = p[1]

    def p_stat2(self, p):
        '''stat : varlist ASSIGN explist'''
        p[0] = esl.interpreter.Assignment(p.lineno(0), p[1], p[3])

    def p_stat3(self, p):
        '''stat : functioncall'''
        p[0] = p[1]

    def p_stat4(self, p):
        '''stat : DO block END'''
        p[0] = esl.interpreter.Block(p.lineno(0))
        p[0].append(p[2])

    def p_stat5(self, p):
        '''stat : WHILE exp DO block END'''
        p[0] = esl.interpreter.While(p.lineno(0), p[2], p[4])

    def p_stat6(self, p):
        '''stat : REPEAT block UNTIL exp'''
        p[0] = esl.interpreter.While(p.lineno(0), p[4], p[2], False)

    def p_stat7(self, p):
        '''stat : IF exp THEN block elseiflist else END'''
        p[0] = esl.interpreter.If(p.lineno(0), p[2], p[4], p[5], p[6])

    def p_stat8(self, p):
        '''stat : FOR name ASSIGN exp COMMA exp DO block END'''
        p[0] = esl.interpreter.NumericFor(
                p.lineno(0), p[2], p[4], p[6], None, p[8])

    def p_stat9(self, p):
        '''stat : FOR name ASSIGN exp COMMA exp COMMA exp DO block END'''
        p[0] = esl.interpreter.NumericFor(
                p.lineno(0), p[2], p[4], p[6], p[8], p[10])

    def p_stat10(self, p):
        '''stat : FOR namelist IN explist DO block END'''
        p[0] = esl.interpreter.GenericFor(p.lineno(0), p[2], p[4], p[6])

    def p_stat11(self, p):
        '''stat : FUNCTION funcname funcbody'''
        p[0] = esl.interpreter.Function(p.lineno(0), p[2], p[3], False)

    def p_stat12(self, p):
        '''stat : LOCAL FUNCTION name funcbody'''
        p[0] = esl.interpreter.Function(p.lineno(0), p[3], p[4], True)

    def p_stat13(self, p):
        '''stat : LOCAL namelist'''
        p[0] = esl.interpreter.Assignment(p.lineno(0), p[2], None, True)

    def p_stat14(self, p):
        '''stat : LOCAL namelist ASSIGN explist'''
        p[0] = esl.interpreter.Assignment(p.lineno(0), p[2], p[4], True)

    def p_laststat1(self, p):
        '''laststat : BREAK'''
        p[0] = esl.interpreter.Break(p.lineno(0))

    def p_laststat2(self, p):
        '''laststat : RETURN explist empty
                    | RETURN empty'''
        if len(p) == 4:
            p[0] = esl.interpreter.Return(p.lineno(0), p[2])
        else:
            p[0] = esl.interpreter.Return(p.lineno(0), None)

    def p_empty(self, p):
        '''empty : SEMICOLON
                 |'''

    def p_elseiflist(self, p):
        '''elseiflist : elseif
                      | elseiflist elseif
                      |'''
        if len(p) == 1:
            p[0] = esl.interpreter.ElseIfList(p.lineno(0))
        elif len(p) == 2:
            p[0] = esl.interpreter.ElseIfList(p.lineno(0))
            p[0].append(p[1])
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_elseif(self, p):
        '''elseif : ELSEIF exp THEN block'''
        p[0] = esl.interpreter.ElseIf(p.lineno(0), p[2], p[4])

    def p_else(self, p):
        '''else : ELSE block
                |'''
        if len(p) == 3:
            p[0] = esl.interpreter.Else(p.lineno(0), p[2])

    def p_funcname(self, p):
        '''funcname : funcname_dot
                    | funcname_dot COLON name'''
        p[0] = p[1]
        if len(p) > 2:
            p[0].append(p[3])
            p[0].colon = True

    def p_funcname_dot(self, p):
        '''funcname_dot : name
                        | funcname_dot DOT name'''
        if len(p) == 2:
            p[0] = esl.interpreter.FunctionName(p.lineno(0))
            p[0].append(p[1])
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_varlist1(self, p):
        '''varlist : var'''
        p[0] = esl.interpreter.VariableList(p.lineno(0))
        p[0].append(p[1])

    def p_varlist2(self, p):
        '''varlist : varlist COMMA var'''
        p[0] = p[1]
        p[0].append(p[3])

    def p_var1(self, p):
        '''var : name'''
        p[0] = esl.interpreter.Variable(p.lineno(0), None, p[1])

    def p_var2(self, p):
        '''var : prefixexp BRACKET_L exp BRACKET_R'''
        p[0] = esl.interpreter.Variable(p.lineno(0), p[1], p[3])

    def p_var3(self, p):
        '''var : prefixexp DOT name'''
        p[0] = esl.interpreter.Variable(p.lineno(0), p[1], p[3], 'attr')

    def p_namelist1(self, p):
        '''namelist : name'''
        p[0] = esl.interpreter.NameList(p.lineno(0))
        p[0].append(p[1])

    def p_namelist2(self, p):
        '''namelist : namelist COMMA name'''
        p[0] = p[1]
        p[0].append(p[3])

    def p_explist1(self, p):
        '''explist : exp'''
        p[0] = esl.interpreter.ExpressionList(p.lineno(0))
        p[0].append(p[1])

    def p_explist2(self, p):
        '''explist : explist COMMA exp'''
        p[0] = p[1]
        p[0].append(p[3])

    def p_exp1(self, p):
        '''exp : NIL'''
        p[0] = esl.interpreter.Constant(p.lineno(0), None)

    def p_exp2(self, p):
        '''exp : TRUE'''
        p[0] = esl.interpreter.Constant(p.lineno(0), True)

    def p_exp3(self, p):
        '''exp : FALSE'''
        p[0] = esl.interpreter.Constant(p.lineno(0), False)

    def p_exp4(self, p):
        '''exp : NUMBER'''
        p[0] = esl.interpreter.Constant(p.lineno(0), int(p[1]))

    def p_exp5(self, p):
        '''exp : STRING'''
        p[0] = esl.interpreter.Constant(p.lineno(0), p[1][1:-1])

    def p_exp6(self, p):
        '''exp : TDOT'''
        raise NotImplementedError('triple dots are not implemented yet')

    def p_exp7(self, p):
        '''exp : function
               | prefixexp
               | tableconstructor
               | op'''
        p[0] = p[1]

    def p_prefixexp1(self, p):
        '''prefixexp : var
                     | functioncall'''
        p[0] = p[1]

    def p_prefixexp2(self, p):
        '''prefixexp : PARANTHESES_L exp PARANTHESES_R'''
        p[0] = p[2]

    def p_functioncall(self, p):
        '''functioncall : prefixexp args
                        | prefixexp COLON name args'''
        if len(p) == 3:
            p[0] = esl.interpreter.FunctionCall(p.lineno(0), p[1], None, p[2])
        else:
            p[0] = esl.interpreter.FunctionCall(p.lineno(0), p[1], p[3], p[4])

    def p_args(self, p):
        '''args : PARANTHESES_L PARANTHESES_R
                | PARANTHESES_L explist PARANTHESES_R
                | tableconstructor
                | string'''
        if len(p) == 2:
            p[0] = esl.interpreter.Args(p.lineno(0))
            p[0].append(p[1])
        elif len(p) == 3:
            p[0] = esl.interpreter.Args(p.lineno(0))
        else:
            p[0] = esl.interpreter.Args(p.lineno(0))
            for exp in p[2]:
                p[0].append(exp)

    def p_function(self, p):
        '''function : FUNCTION funcbody'''
        raise NotImplementedError('function is not ready yet')

    def p_funcbody(self, p):
        '''funcbody : PARANTHESES_L parlist PARANTHESES_R block END
                    | PARANTHESES_L PARANTHESES_R block END'''
        if len(p) == 6:
            p[0] = esl.interpreter.FunctionBody(p.lineno(0), p[2], p[4])
        else:
            p[0] = esl.interpreter.FunctionBody(p.lineno(0), None, p[3])

    def p_parlist1(self, p):
        '''parlist : namelist'''
        p[0] = esl.interpreter.ParametersList(p.lineno(0), p[1])

    def p_parlist2(self, p):
        '''parlist : namelist COMMA TDOT
                   | TDOT'''
        if len(p) == 4:
            p[0] = esl.interpreter.ParametersList(p.lineno(0), p[1], True)
        else:
            p[0] = esl.interpreter.ParametersList(p.lineno(0), None, True)

    def p_tableconstructor(self, p):
        '''tableconstructor : BRACES_L fieldlist BRACES_R
                            | BRACES_L BRACES_R'''
        if len(p) == 3:
            p[0] = esl.interpreter.Table(p.lineno(0), None)
        else:
            p[0] = esl.interpreter.Table(p.lineno(0), p[2])

    def p_fieldlist1(self, p):
        '''fieldlist : field'''
        p[0] = esl.interpreter.FieldList(p.lineno(0))
        p[0].append(p[1])

    def p_fieldlist2(self, p):
        '''fieldlist : fieldlist fieldsep field'''
        p[0] = p[1]
        p[0].append(p[3])

    def p_fieldlist3(self, p):
        '''fieldlist : fieldlist optfieldsep'''
        p[0] = p[1]

    def p_field(self, p):
        '''field : BRACKET_L exp BRACKET_R ASSIGN exp
                 | name ASSIGN exp
                 | exp'''
        if len(p) == 6:
            p[0] = esl.interpreter.Field(p.lineno(0), p[2], p[5])
        elif len(p) == 4:
            p[0] = esl.interpreter.Field(p.lineno(0), p[1], p[3])
        else:
            p[0] = esl.interpreter.Field(p.lineno(0), None, p[1])

    def p_fieldsep(self, p):
        '''fieldsep : COMMA
                    | SEMICOLON'''

    def p_optfieldsep(self, p):
        '''optfieldsep : fieldsep
                       |'''

    def p_op(self, p):
        '''op : op_one'''
        p[0] = p[1]

    def p_op_one1(self, p):
        '''op_one : op_one OR op_two'''
        p[0] = esl.interpreter.Logical(p.lineno(0), p[1], p[2], p[3])

    def p_op_one2(self, p):
        '''op_one : op_two'''
        p[0] = p[1]

    def p_op_two1(self, p):
        '''op_two : op_two AND op_three'''
        p[0] = esl.interpreter.Logical(p.lineno(0), p[1], p[2], p[3])

    def p_op_two2(self, p):
        '''op_two : op_three'''
        p[0] = p[1]

    def p_op_three1(self, p):
        '''op_three : op_three LESS_THEN op_four
                    | op_three LESS_EQUAL_THEN op_four
                    | op_three MORE_THEN op_four
                    | op_three MORE_EQUAL_THEN op_four
                    | op_three TILDE_EQUAL op_four
                    | op_three EQUALS op_four'''
        p[0] = esl.interpreter.Relational(p.lineno(0), p[1], p[2], p[3])

    def p_op_three2(self, p):
        '''op_three : op_four'''
        p[0] = p[1]

    def p_op_four1(self, p):
        '''op_four : op_four APPEND op_five'''
        p[0] = esl.interpreter.Append(p.lineno(0), p[1], p[3])

    def p_op_four2(self, p):
        '''op_four : op_five'''
        p[0] = p[1]

    def p_op_five1(self, p):
        '''op_five : op_five PLUS op_six
                   | op_five MINUS op_six'''
        p[0] = esl.interpreter.Arithmetic(p.lineno(0), p[1], p[2], p[3])

    def p_op_five2(self, p):
        '''op_five : op_six'''
        p[0] = p[1]

    def p_op_six1(self, p):
        '''op_six : op_six TIMES op_seven
                  | op_six DIVIDE op_seven
                  | op_six MODULO op_seven'''
        p[0] = esl.interpreter.Arithmetic(p.lineno(0), p[1], p[2], p[3])

    def p_op_six2(self, p):
        '''op_six : op_seven'''
        p[0] = p[1]

    def p_op_seven1(self, p):
        '''op_seven : NOT op_eight
                    | SQUARE op_eight
                    | MINUS op_eight'''
        p[0] = esl.interpreter.Unary(p.lineno(0), p[1], p[2])

    def p_op_seven2(self, p):
        '''op_seven : op_eight'''
        p[0] = p[1]

    def p_op_eight1(self, p):
        '''op_eight : op_eight POWER op_nine'''
        p[0] = esl.interpreter.Arithmetic(p.lineno(0), p[1], p[2], p[3])

    def p_op_eight2(self, p):
        '''op_eight : op_nine'''
        p[0] = p[1]

    def p_op_nine(self, p):
        '''op_nine : exp'''
        p[0] = p[1]

    def p_name(self, p):
        '''name : NAME'''
        p[0] = esl.interpreter.Name(p.lineno(0), p[1])

    def p_string(self, p):
        '''string : STRING'''

    def p_error(self, p):
        lexer = p.lexer
        startpos = getattr(lexer, 'startpos', 1)
        column = lexer.lexpos - startpos + 1
        raise ParseError('can\'t parse `{}\' '
                          'at line {} col {}'.format(p.value, p.lineno, column))

    def parse(self, code):
        return self.yacc.parse(code, lexer=self.lexer.lexer, tracking=True)
