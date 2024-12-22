import ply.yacc as yacc

from .lexer import tokens
from .data_types import *


precedence = [
    ('left', 'HAT')
]


def p_final(p):
    """final : answers
    """
    p[0] = p[1]

def p_final_expr(p):
    """final : expr
    """
    p[0] = p[1]


# Answers seperated by vee symbol
def p_answers(p):
    """answers : answer VEE answers
               | answer
    """
    if len(p) == 4:
        p[0] = p[3]
        p[0].insert(0, p[1])
    elif len(p) == 2:
        p[0] = [p[1]]

def p_answer(p):
    """answer : sym EQUALS expr"""
    p[0] = (p[1], p[3])


# An expression, which is a general form of any equation. Optional parentheses.
def p_expr(p):
    """expr : term
            | sum
    """
    p[0] = p[1]


# Term (used in addition)
def p_term(p):
    """term : factor
            | prod
    """
    p[0] = p[1]


# Represents a singular factor, like: x, 1, (a + b), etc.
# Something you can view as a single factor in an equation.
def p_factor(p):
    """factor : atom
              | minop
    """
    p[0] = p[1]


# Used in negative numbers
def p_minop(p):
    """minop : MINUS atom
             | MINUS minop
    """
    p[0] = p[2]
    p[0].is_negative ^= True


# Highest precendence non-terminal
def p_atom(p):
    """atom : num
            | sym
            | LPAREN expr RPAREN
            | fraction
            | sqrt
            | expo
            | factorial
    """
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = p[2]
        p[0].has_parens = True

# Colon Conversion to Fraction
def p_atom_colon_fraction(p):
    """atom : num COLON num"""
    p[0] = Fraction(p[1], p[3])


# Exponents
def p_expo(p):
    """expo : atom HAT LBRACKET expr RBRACKET
            | atom HAT atom
    """
    p[0] = p[1]

    if len(p) == 4:
        p[0].exponent = p[3]
    elif len(p) == 6:
        p[0].exponent = p[4]


# Numbers
def p_num_int(p):
    """num : INTEGER
    """
    p[0] = Number(p[1], True)

def p_num_float(p):
    """num : FLOAT
    """
    p[0] = Number(p[1], False)


# Variables/symbols
def p_sym(p):
    """sym : SYMBOL"""
    p[0] = Symbol(p[1])


# Addition
def p_sum(p):
    """sum : term PLUS term
           | term MINUS term
    """
    if p[2] == '+':
        p[0] = Sum()

        p[0].add_term(-1, p[1], False)
        p[0].add_term(-1, p[3], False)
    elif p[2] == '-':
        if isinstance(p[3], Expr):
            p[3].is_negative ^= True
            p[3].print_minus = False  # Don't print the minus, because it's printed by the Sum expression

        p[0] = Sum()

        p[0].add_term(-1, p[1], False)
        p[0].add_term(-1, p[3], True)

def p_sum_chain(p):
    """sum : term PLUS sum
           | term MINUS sum
    """
    if p[2] == '+':
        p[0] = p[3]

        p[0].add_term(0, p[1], False)
    elif p[2] == '-':
        p[0] = p[3]

        first_next_term = p[0].get_children()[0]

        first_next_term.is_negative ^= True
        first_next_term.print_minus = False

        p[0].is_subtraction[0] = True

        p[0].add_term(0, p[1], False)


# Rules for chaining multiplication
def p_prod(p):
    """prod : negprod
            | posprod
    """
    p[0] = p[1]

# Products with a negative sign in front
def p_negprod(p):
    """negprod : MINUS posprod
    """
    p[0] = p[2]
    p[0].get_children()[0].is_negative ^= True

# Separate product, to prevent implicit multiplication like this:
# x-22 -> x * (-22)
# posprod is basically a product where the first factor does not start with a
# minus sign.
def p_posprod(p):
    """posprod : atom TIMES factor
               | atom atom
    """
    if len(p) == 4:
        p[0] = Mul([p[1], p[3]])
    elif len(p) == 3:
        p[0] = Mul([p[1], p[2]])

    p[0].is_implicit.insert(0, len(p) == 3)

def p_posprod_chain(p):
    """posprod : atom TIMES prod
               | atom posprod
    """
    if len(p) == 4:
        p[0] = p[3]
    elif len(p) == 3:
        p[0] = p[2]

    p[0].factors.insert(0, p[1])
    p[0].is_implicit.insert(0, len(p) == 3)


# Fractions
def p_fraction(p):
    """fraction : FRAC LBRACKET expr RBRACKET LBRACKET expr RBRACKET
    """
    p[0] = Fraction(p[3], p[6])


# Square roots
def p_sqrt(p):
    """sqrt : SQRT LBRACKET expr RBRACKET
    """
    p[0] = Root(p[3])


# Factorials
def p_factorial(p):
    """factorial : atom FACT"""
    p[0] = Factorial(p[1])


# Colons 
def p_expr_colon_fraction(p):
    """expr : num COLON num"""
    p[0] = Fraction(p[1], p[3])


# Error message
def p_error(p):
    print("Syntax error!", p)


parser = yacc.yacc()
