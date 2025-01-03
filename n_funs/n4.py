from functools import reduce

from .data_types import *
from .n3 import N3, get_coefficients, divide_fraction
from .n2 import N2
from .util_trav import cleanup_traversals



def real_addition(num):
    num_str = str(num)
    num_str = num_str.replace("+", "+")
    return num_str


def is_perfect_square(val: float):
    return np.isclose(np.sqrt(val) % 1, 0.0)


def trav_evaluate_square_root(root: Expr):
    """If there is a square root where the base contains a two in the exponent,
    evaluate the square root.
    """
    root.traverse_children(trav_evaluate_square_root)

    # NOTE: The variable root refers to the ast 'root' (which is not necessarily the root for the entire AST)
    # The Root refers to the class representing square roots
    if isinstance(root, Root):
        if isinstance(root.base.exponent, Mul):
            two_factors = root.base.exponent.get_factors(lambda x: isinstance(x, Number) and x == 2)

            if len(two_factors) > 0:
                new_expr = root.base
                factor_to_remove = two_factors[0]

                new_expr.exponent.remove_factor(factor_to_remove)

                # One factor left? Convert expression to that factor instead of a Mul instance
                if len(new_expr.exponent) == 1:
                    new_expr.exponent = new_expr.exponent.get_factors()[0]

                return new_expr
        elif isinstance(root.base.exponent, Number) and root.base.exponent == 2:
            root.base.exponent = 1

            return root.base

    return root


def trav_evaluate_perfect_squares(root: Expr):
    """For every square root in the expression, evaluate the integer numbers
    for which the square root is also an integer.
    """
    root.traverse_children(trav_evaluate_perfect_squares)

    if isinstance(root, Root):
        # Find integers that we can evaluate in the expression
        if isinstance(root.base, Mul):
            new_mul = Mul()
            all_nums = root.base.get_factors(lambda x: isinstance(x, Number) and x.exponent == 1 and not x.is_negative)

            while all_nums:
                num = all_nums.pop()

                if is_perfect_square(num.value):  # Check if it is a perfect square
                    root.base.remove_factor(num)

                    new_num = Number(np.sqrt(num.value), False)
                    new_mul.add_factor(-1, new_num)

            new_mul.add_factor(-1, root.create_copy(True))

            return new_mul
        elif isinstance(root.base, Number):
            if root.base.exponent == 1 and is_perfect_square(root.base.value):
                return Number(np.sqrt(root.base.value))

    return root


def trav_sum_similar_terms(root: Expr):
    """In any sum, look for similar terms and add them together if they are alike.
    """
    root.traverse_children(trav_sum_similar_terms)

    if isinstance(root, Sum):
        # For each term, check if it fits in some 'equivalence class'
        # If it does, then add it to that group, else create a new group
        # Finally all terms in the same group get added together.
        equiv_terms = []

        for term in root.get_terms():
            # Look for the equivalence group
            num_facs = term.get_factors(lambda x: isinstance(x, Number))

            if len(num_facs) == 0:
                temp = Number(1)
                temp.is_negative = term.is_negative

                num_facs = [temp]

            for i, equiv_class in enumerate(equiv_terms):
                if term.is_like(equiv_class[0]):
                    result_coeff = reduce(lambda x, y: x * y, num_facs)

                    equiv_terms[i][1] += result_coeff

                    break
            else:
                # If it did not find a equiv. group, create one
                var_facs = term.get_factors(lambda x: not isinstance(x, Number))

                if len(var_facs) == 1:
                    equiv_terms.append([var_facs[0], reduce(lambda x, y: x * y, num_facs)])
                else:
                    equiv_terms.append([Mul(var_facs), reduce(lambda x, y: x * y, num_facs)])

        if len(equiv_terms) > 0:
            # Now add all similar terms
            new_sum = Sum()
            new_sum.is_negative = root.is_negative
            new_sum.has_parens = root.has_parens
            new_sum.exponent = root.exponent

            for var, new_coeff in equiv_terms:
                new_term = None

                if var:
                    if new_coeff == Number(1):
                        new_term = var
                    else:
                        new_term = Mul([new_coeff, var])
                else:
                    new_term = new_coeff

                new_sum.add_term(-1, new_term, False)

            return new_sum

    return root


def trav_n4_rule1(root: Expr):
    """Takes a fraction with constants and symbols raised to some power,
    distributes the power and converts it into a multiplication.
    """
    root.traverse_children(trav_n4_rule1)

    if isinstance(root, Fraction):
        num_coeffs = get_coefficients(root.num)
        denom_coeffs = get_coefficients(root.denom)

        if len(num_coeffs) == 1 and len(denom_coeffs) == 1:
            a = num_coeffs[0]
            b = denom_coeffs[0]

            new_root = Mul([])
            new_root.has_parens = root.has_parens
            new_root.exponent = 1

            coeff = Number((a.get_value() / b.get_value())**root.exponent.get_value(), False)

            if isinstance(root.num, Mul):
                root.num.remove_factor(a)

                if len(root.num) == 1:
                    root.num = root.num.get_factors()[0]

            if isinstance(root.denom, Mul):
                root.denom.remove_factor(b)

                if len(root.denom) == 1:
                    root.denom = root.denom.get_factors()[0]

            root.num.exponent = root.exponent
            root.denom.exponent = root.exponent
            root.exponent = 1

            new_root.add_factor(0, divide_fraction(root), False)
            new_root.add_factor(0, coeff, False)

            return new_root

    return root


def trav_n4_rule4(root: Expr):
    """In a product of multiple factors, multiply the same variable together
    and add the exponents. Also rewrite the constants into a single constant.
    """
    root.traverse_children(trav_n4_rule4)

    if isinstance(root, Mul):
        coeffs = root.get_factors(lambda x: isinstance(x, Number))
        if len(coeffs) == 0:
            coeffs.append(Number(1))

        combined_value = 1.0
        for coeff in coeffs:
            combined_value *= float(coeff.get_value())

        result_coeff = Number(combined_value)

        new_mul = Mul([])
        new_mul.add_factor(-1, result_coeff)

        var_factors = root.get_factors(lambda x: not isinstance(x, Number))
        var_groups = []

        for var_a in var_factors:
            var_a.exponent = var_a.exponent or Number(1)

            for i, (var_b, exp_sum) in enumerate(var_groups):
                exp_sum: Sum

                var_a_no_exp = var_a.create_copy(True)
                var_a_no_exp.exponent = Number(1)

                var_b_no_exp = var_b.create_copy(True)
                var_b_no_exp.exponent = Number(1)

                if var_a_no_exp == var_b_no_exp:
                    exp_sum = exp_sum + var_a.exponent
                    var_groups[i] = (var_b, exp_sum)
                    break
            else:
                var_groups.append((var_a, var_a.exponent))

        for (var, exponents) in var_groups:
            temp = var
            temp.exponent = exponents
            new_mul.add_factor(-1, temp, False)

        return new_mul

    return root


def trav_cleanup_decimals(root: Expr):
    """Cleans up numbers in the expression by removing unnecessary decimals."""
    root.traverse_children(trav_cleanup_decimals)

    if hasattr(root, 'exponent'):
        exp = root.exponent
        if isinstance(exp, Number):
            value = exp.get_value()
            if abs(value - int(round(value))) < 1e-6:
                exp.value = int(round(value))
                exp.is_integer = True
            else:
                exp.value = round(value, 3)
                exp.is_integer = False
            root.exponent = exp
        elif isinstance(exp, (int, float)):
            value = exp
            if abs(value - int(round(value))) < 1e-6:
                root.exponent = int(round(value))
            else:
                root.exponent = round(value, 3)
        elif isinstance(exp, Expr):
            root.exponent = trav_cleanup_decimals(exp)

    if isinstance(root, Number):
        value = root.get_value()
        if abs(value - int(round(value))) < 1e-6:
            root.value = int(round(value))
            root.is_integer = True
        else:
            root.value = round(value, 3)
            root.is_integer = False

    return root




def N4(input_str):
    ast_root = N3(input_str)
    ast_root = real_addition(ast_root)
    ast_root = N3(ast_root)


    ast_root = trav_evaluate_perfect_squares(ast_root)
    ast_root = trav_evaluate_square_root(ast_root)
    ast_root = trav_sum_similar_terms(ast_root)
    ast_root = trav_n4_rule1(ast_root)
    ast_root = trav_n4_rule4(ast_root)

    ast_root = trav_cleanup_decimals(ast_root)
    ast_root = cleanup_traversals(ast_root)

    return ast_root
