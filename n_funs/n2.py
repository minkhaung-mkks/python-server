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
    numerator and denominator that can be split off in a seperate fraction.
    """
    root.traverse_children(trav_split_fractions)

    # Check if a number in the numerator and denominator have gcd = 1
    if isinstance(root, Fraction):
        num_coeffs = get_coefficients(root.num)
        denom_coeffs = get_coefficients(root.denom)

        # Don't perform this transformation if there are multiple coefficients.
        if len(num_coeffs) != 1 or len(denom_coeffs) != 1:
            return root

        m = num_coeffs[0]
        n = denom_coeffs[0]

        if m.is_integer and n.is_integer and math.gcd(m.value, n.value) != 1:
            return root

        # Convert m and n to proper fractions (gcd = 1)
        pq = fractions.Fraction(m.value * (-1 if m.is_negative else 1)).limit_denominator()
        rs = fractions.Fraction(n.value * (-1 if n.is_negative else 1)).limit_denominator()

        ps = pq.numerator * rs.denominator
        qr = pq.denominator * rs.numerator

        a = ps / math.gcd(ps, qr)
        b = qr / math.gcd(ps, qr)

        a = Number(int(a))
        b = Number(int(b))

        # Remove the numbers from the original fraction
        if isinstance(root.num, Mul) and not root.num.has_parens:
            root.num.remove_factor(m)

            # If there is just one factor left, just change the expression
            # to that factor
            if len(root.num.factors) == 1:
                root.num = root.num.factors[0]

        if isinstance(root.denom, Mul) and not root.denom.has_parens:
            root.denom.remove_factor(n)

            if len(root.denom.factors) == 1:
                root.denom = root.denom.factors[0]

        new_frac = Fraction(a, b)

        # Create a new expression to multiply the expressions
        new_root = Mul([])

        new_root.add_factor(0, root, False)
        new_root.add_factor(0, new_frac, False)

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
