import re

from .yacc import parser
from .data_types import *
from .data_types import LatexNormalizer
from .util_trav import cleanup_traversals



def normalize_numbers_in_string(s):
    def normalize_number(num_str):
        if ',' in num_str and '.' in num_str:
            if num_str.find(',') < num_str.find('.'):  # US notation
                num_str = num_str.replace(',', '')
            else:  # European notation
                num_str = num_str.replace('.', '').replace(',', '.')
        elif ',' in num_str and num_str.count(',') > 1:  # Multiple commas imply grouping
            num_str = num_str.replace(',', '')
        elif '.' in num_str and num_str.count('.') > 1:  # Multiple dots imply grouping
            num_str = num_str.replace('.', '')
        elif ',' in num_str:  # Commas without dots
            num_str = num_str.replace(',', '.')
        # If only dots are present, keep as is
        return num_str

    # Regular expression to find numbers in the string
    number_pattern = r'\b\d[\d.,]*\b'

    # Function to replace each number using normalize_number
    def replace_number(match):
        num_str = match.group(0)
        norm_num = normalize_number(num_str)
        return norm_num

    # Apply the normalization to all numbers in the string
    s = re.sub(number_pattern, replace_number, s)
    return s

def clean_string(latex_str):
    # Remove whitespace and trailing periods
    temp = latex_str.rstrip('. ')
    temp = temp.lstrip()
    temp = temp.lower()

    temp = normalize_numbers_in_string(temp)

    # Replace multiplication symbols with asterisks
    temp = re.sub(r"\\times|\\cdot", '*', temp)

    normalizer = LatexNormalizer(temp)
    temp = normalizer.normalize()

    # Function to check if a string represents a number
    def is_numeric(s):
        return re.fullmatch(r'\d+(\.\d+)?', s) is not None

    # Pattern to match a digit followed by \frac{numerator}{denominator}
    pattern = r'(\d)\s*\\frac\s*{\s*([^}]*)\s*}\s*{\s*([^}]*)\s*}'

    # Function to determine whether to insert '+' or '*'
    def replace_mixed_number(match):
        integer_part = match.group(1)
        numerator = match.group(2)
        denominator = match.group(3)

        if is_numeric(numerator) and is_numeric(denominator):
            # Both numerator and denominator are numeric, insert '+'
            return f'{integer_part}+\\frac{{{numerator}}}{{{denominator}}}'
        else:
            # Either numerator or denominator is not numeric, keep as multiplication
            return f'{integer_part}*\\frac{{{numerator}}}{{{denominator}}}'

    # Apply the substitution
    temp = re.sub(pattern, replace_mixed_number, temp)

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
    """Remove implicit multiplication by setting specific flags indicating
    whether it is implicit to False or True based on the presence of numerical fractions.
    """
    root.traverse_children(trav_remove_implicit_mult)

    if isinstance(root, Mul):
        new_is_implicit = []

        for i in range(1, len(root.factors)):
            prev_factor = root.factors[i - 1]
            curr_factor = root.factors[i]

            # Check if the current factor is a numerical fraction
            if isinstance(prev_factor, Number) and isinstance(curr_factor, Fraction) and curr_factor.is_numerical():
                # If no '*' symbol exists in the expression, set is_implicit to True for this multiplication
                if "*" not in str(root):  # Check if there is no explicit multiplication sign
                    new_is_implicit.append(True)  # Implicit addition (treated as addition in LaTeX)
                else:
                    new_is_implicit.append(False)  # Explicit multiplication
            else:
                new_is_implicit.append(False)

        root.is_implicit = new_is_implicit

    return root



def currency_vals(input_str):
    def replace_currency(match):
        num_str = match.group(0)
        num_str = num_str[:-2] + '.00'
        return num_str
    
    pattern = r'\b\d+(?:[.,]\d+)?[.,]-'

    output_str = re.sub(pattern, replace_currency, input_str)

    return output_str


def N1(input_str):
    input_str = currency_vals(input_str)
    if '=' in input_str:
        rhs_str = input_str.split('=')[-1]
        rhs_ast = convert_expression_to_AST(rhs_str)
        input_str = rhs_ast
    else:
        input_str = convert_expression_to_AST(input_str)
    
    ast_root = input_str

    if not isinstance(ast_root, Expr):
        ast_root = answers_to_polynomial(ast_root)

    ast_root = trav_remove_implicit_mult(ast_root)

    ast_root = cleanup_traversals(ast_root)

    return ast_root