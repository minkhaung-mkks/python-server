from .data_types import *
from .n2 import N2, get_coefficients, divide_fraction
from .util_trav import *


def trav_distribute_exp_fraction(root: Expr):
    """Takes a fraction, if the fraction has a non-one power, then the exponent
    gets distributed over the numerator and denominator.
    """
    root.traverse_children(trav_distribute_exp_fraction)

    if isinstance(root, Fraction):
        if isinstance(root.num, Symbol) and isinstance(root.denom, Symbol):
            if root.num.exponent == 1 and root.denom.exponent == 1:
                # Check if the entire fraction is being exponentiated
                if root.exponent != 1:
                    new_root = Mul([])

                    new_root.is_negative = root.is_negative
                    new_root.has_parens = root.has_parens

                    root.num.exponent = root.exponent
                    root.denom.exponent = -root.exponent

                    new_root.add_factor(0, root.denom, False)
                    new_root.add_factor(0, root.num, False)

                    return new_root

    return root


def fraction_to_decimal(frac: Fraction):
    """Converts a fraction object into a Number object containing the evaluated
    value. (If possible, it does not work when there are symbols or non-constants
    involved.)

    Args:
        frac (Fraction):

    Returns:
        Number: The result
    """
    if isinstance(frac.num, Number) and isinstance(frac.denom, Number):
        temp = Number(frac.num.get_value() / frac.denom.get_value(), False)

        return temp
    return frac


def trav_n3_rule2(root: Expr):
    """Takes constants out of a fraction and converts the entire thing into
    a multiplication.
    """
    root.traverse_children(trav_n3_rule2)

    if isinstance(root, Fraction):
        num_coeffs = get_coefficients(root.num)
        denom_coeffs = get_coefficients(root.denom)

        # Skip if the exponent is not 1, because there is a different rule at
        # N=4 for this.
        if root.exponent != 1:
            return root

        if len(num_coeffs) == 1 and len(denom_coeffs) == 1:
            a = num_coeffs[0]
            b = denom_coeffs[0]

            new_root = Mul([])
            temp = Number(a.get_value() / b.get_value(), False)

            if isinstance(root.num, Mul):
                root.num.remove_factor(a)

                if len(root.num) == 1:
                    root.num = root.num.get_factors()[0]

            if isinstance(root.denom, Mul):
                root.denom.remove_factor(b)

                if len(root.denom) == 1:
                    root.denom = root.denom.get_factors()[0]

            new_root.add_factor(0, divide_fraction(root), False)
            new_root.add_factor(0, temp, False)

            return new_root

    return root



def trav_frac_to_dec(root: Expr):
    """Evaluates fractions. Results in Number objects.
    """
    root.traverse_children(trav_frac_to_dec)

    if isinstance(root, Fraction):
        if isinstance(root.num, Number) and isinstance(root.denom, Number):
            denom_value = root.denom.get_value()
            if denom_value == 0:
                # Return the fraction itself if denominator is zero
                return root
            
            evaluation = root.num.get_value() / root.denom.get_value()

            new_num = Number(evaluation, False)
            new_num.is_negative ^= root.is_negative

            return new_num

    return root


def switch_num_to_dec(root: Expr):
    """Formats Number objects to three decimal places.
    """
    root.traverse_children(switch_num_to_dec)

    if isinstance(root, Number):
        value = root.get_value()
        new_num = Number(float(value), False)
        new_num.is_negative = root.is_negative
        
        return new_num

    return root



def N3(input_str):
    ast_root = N2(input_str)

    ast_root = switch_num_to_dec(ast_root)
    
    ast_root = trav_frac_to_dec(ast_root)

    ast_root = trav_distribute_exp_fraction(ast_root)

    ast_root = trav_n3_rule2(ast_root)

    ast_root = cleanup_traversals(ast_root)

    return ast_root
