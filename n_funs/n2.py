import fractions
import math

from .data_types import *
from .n1 import N1
from .util_trav import cleanup_traversals


def trav_sort_expressions(root: Expr):
    """Sort expressions with a sequence of expressions within them. Like
    sums or products: (b + a + c) or (b * a * 2).
    """
    root.traverse_children(trav_sort_expressions)

    # Finally sort this node if it is sortable
    if isinstance(root, (Sum, Mul)):

        root.sort_children()

    return root


def get_coefficients(expr: Expr):
    """This is a helper function that gets the constant values of a product.
    It is used to see what constants a product can be divided by.
    It currently ignores constants with an exponent.
    Note that in case of a symbol (basically a product with a single factor),
    it returns just 1.

    As of now this function is not very logical (why does it not return a
    factor for numbers?) This was just done because it works for the traversals
    that are currently used.

    Args:
        expr (Expr): The expression to get the factors for.

    Returns:
        list: List of expressions, can be empty.
    """
    if isinstance(expr, Mul):
        return expr.get_factors(lambda x: isinstance(x, Number) and x.exponent == 1)
    elif isinstance(expr, Symbol):
        return [Number(1)]
    else:
        return []


def divide_fraction(frac: Fraction):
    """This is helper function which takes a fraction and converts it to a
    multiplication of the numerator and denominator. Which results in the
    denominator having a negated exponent.

    Args:
        frac (Fraction): Fraction to transform to a product.

    Returns:
        Mul: The resulting product.
    """
    if isinstance(frac.denom, Symbol):
        prod = Mul([])
        prod.exponent = frac.exponent
        prod.is_negative = frac.is_negative
        prod.has_parens = frac.has_parens

        prod.add_factor(0, frac.denom, False)
        prod.add_factor(0, frac.num, False)

        frac.num.has_parens = len(frac.num) != 1
        prod.has_parens = True

        if frac.denom.exponent == 1:
            frac.denom.exponent = Number(1)
            frac.denom.exponent.is_negative = True
        else:
            frac.denom.exponent = -frac.denom.exponent

        return prod
    return frac


def trav_split_fractions(root: Expr):
    """For every fraction in an expression, check if there is a factor in the
    numerator and denominator that can be split off in a separate fraction.
    """
    root.traverse_children(trav_split_fractions)

    if isinstance(root, Fraction):
        num_coeffs = get_coefficients(root.num)
        denom_coeffs = get_coefficients(root.denom)

        # Initialize fractions
        numeric_fraction = None
        variable_fraction = None

        if num_coeffs and not denom_coeffs:
            # Case: Numbers only in numerator
            numeric_num = num_coeffs[0]
            if isinstance(root.num, Mul) and not root.num.has_parens:
                root.num.remove_factor(numeric_num)
                variable_num = root.num if len(root.num.factors) > 1 else root.num.factors[0]
            else:
                variable_num = root.num

            numeric_denom = root.denom
            variable_denom = Number(1)

            numeric_fraction = Fraction(numeric_num, numeric_denom)
            variable_fraction = Fraction(variable_num, variable_denom)

        elif denom_coeffs and not num_coeffs:
            # Case: Numbers only in denominator
            numeric_denom = denom_coeffs[0]

            if isinstance(root.denom, Mul) and not root.denom.has_parens:
                root.denom.remove_factor(numeric_denom)
                variable_denom = root.denom if len(root.denom.factors) > 1 else root.denom.factors[0]
            else:
                variable_denom = root.denom

            numeric_num = root.num
            variable_num = Number(1)

            numeric_fraction = Fraction(numeric_num, numeric_denom)
            variable_fraction = Fraction(variable_num, variable_denom)

        elif num_coeffs and denom_coeffs:
            # Case: Numbers in both numerator and denominator
            numeric_num = num_coeffs[0]
            numeric_denom = denom_coeffs[0]

            if isinstance(root.num, Mul) and not root.num.has_parens:
                root.num.remove_factor(numeric_num)
                variable_num = root.num if len(root.num.factors) > 1 else root.num.factors[0]
            else:
                variable_num = root.num

            if isinstance(root.denom, Mul) and not root.denom.has_parens:
                root.denom.remove_factor(numeric_denom)
                variable_denom = root.denom if len(root.denom.factors) > 1 else root.denom.factors[0]
            else:
                variable_denom = root.denom

            numeric_fraction = Fraction(numeric_num, numeric_denom)
            variable_fraction = Fraction(variable_num, variable_denom)

        # Check if fractions should be simplified
        if numeric_fraction and isinstance(numeric_fraction.denom, Number) and numeric_fraction.denom.value == 1:
            numeric_fraction = numeric_fraction.num

        if variable_fraction and isinstance(variable_fraction.denom, Number) and variable_fraction.denom.value == 1:
            variable_fraction = variable_fraction.num

        if numeric_fraction and variable_fraction:
            # Combine both fractions in multiplication
            if isinstance(numeric_fraction, Expr) and isinstance(variable_fraction, Expr):
                new_root = Mul([numeric_fraction, variable_fraction])
            else:
                new_root = numeric_fraction if numeric_fraction != Number(1) else variable_fraction
            return new_root

    return root



def float_to_fraction(expr: Expr):
    """Convert a decimal number to a proper fraction. Ignores (assumed) floating
    point errors.
    """
    if isinstance(expr, Number) and expr.exponent == 1 and not expr.is_integer:
        f = fractions.Fraction(expr.value).limit_denominator()
        n, d = f.numerator, f.denominator

        new_frac = Fraction(Number(n), Number(d))

        return new_frac
    else:
        return expr


def trav_rewrite_decimal_numbers(root: Expr):
    """Rewrite decimal numbers to fractions, only where they are multiplied by a variable
    """
    root.traverse_children(trav_rewrite_decimal_numbers)

    if isinstance(root, Mul):
        root.factors = list(map(float_to_fraction, root.factors))

    return root


def trav_N2_rule5(root: Expr):
    """This traversal converts all fraction to multiplication.
    """
    root.traverse_children(trav_N2_rule5)

    if isinstance(root, Fraction):
        return divide_fraction(root)

    return root


def N2(input_str):
    ast_root = N1(input_str)

    # Sort any sortable expressions
    ast_root = trav_sort_expressions(ast_root)

    # Seperate fractions if two numbers have gcd(a, b) = 1
    ast_root = trav_split_fractions(ast_root)

    ast_root = trav_rewrite_decimal_numbers(ast_root)

    ast_root = trav_N2_rule5(ast_root)

    ast_root = cleanup_traversals(ast_root)

    return ast_root
