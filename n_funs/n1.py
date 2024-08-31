import re

from .yacc import parser
from .data_types import *
from .data_types import LatexNormalizer
from .util_trav import cleanup_traversals


def clean_string(latex_str):
    # Remove whitespace and trailing periods
    temp = latex_str.rstrip('. ')
    temp = temp.lstrip()

    # Replace multiplication symbols with asterix
    temp = re.sub(r"\\times|\\cdot", '*', temp)

    normalizer = LatexNormalizer(temp)
    temp = normalizer.normalize()

    return temp


# Convert a LaTeX expression into a abstract syntax tree.
# This allows for easier manipulation of symbols, while not losing the
# semantic meaning of the mathematical symbols.
def convert_expression_to_AST(latex_str):
    # Use a lexer + parser to convert into an AST
    answers = parser.parse(clean_string(latex_str))

    return answers


def custom_count(iter, key=None):
    """Function to count items in a list, with the option to only count them
    if they satisfy some key function.

    Args:
        iter (iterable): Iterable to count
        key (function(x) -> Boolean, optional): Requirement function to satisfy
        Defaults to None.

    Returns:
        int: The amount of items in the iterable that satisfy the optional
        function.
    """
    count = 0

    if key is None:
        return len(iter)

    for elem in iter:
        if key(elem):
            count += 1

    return count


def answers_to_polynomial(answers):
    """This function takes multiple 'answers' resulting from an expression like:
    "x = 1 v x = a + b", where x = 1 is an answer and x = a + b is an answer.
    These are then converted into a polynomial, as specified.

    Args:
        answers (list): List of answer expressions.

    Returns:
        Expr: The new tree with a single polynomial.
    """
    ast_root = Mul([])

    for ans in answers:
        # Create an add expression per polynomial factor
        poly_factor = Sum()
        poly_factor.has_parens = True

        poly_factor.add_term(-1, ans[0], False)
        poly_factor.add_term(-1, ans[1], True)

        ans[1].is_negative ^= True
        ans[1].print_minus = False
        ans[1].has_parens = True

        ast_root.factors.insert(0, poly_factor)
        ast_root.is_implicit.insert(0, False)

    return ast_root


def trav_remove_implicit_mult(root: Expr):
    """Remove implicit multiplication by setting all the flags indicating
    whether it is implicit to False.
    """
    root.traverse_children(trav_remove_implicit_mult)

    # For each term, set all implicit mul flags to False
    if isinstance(root, Mul):
        root.is_implicit = [False for _ in root.is_implicit]

    return root


def N1(input_str):
    ast_root = convert_expression_to_AST(input_str)

    # Transform multiple answers seperated by \vee into a single polynomial
    if not isinstance(ast_root, Expr):
        ast_root = answers_to_polynomial(ast_root)

    # Remove implicit multiplication
    ast_root = trav_remove_implicit_mult(ast_root)

    ast_root = cleanup_traversals(ast_root)

    return ast_root
