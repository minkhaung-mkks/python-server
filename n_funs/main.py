"""Simple library to parse and manipulate LaTeX math expressions.
Not entirely finished and tested yet, but currently provides the basis.
Author: Robbie Koevoets
"""
import sys

from n1 import N1
from n2 import N2
from n3 import N3
from n4 import N4
from util_trav import *


def N(n, input_str):
    """The N-func, use this to apply the nfunc to your choosing.

    Returns:
        str: The string of the resulting expression tree.
    """
    n_funcs = [N1, N2, N3, N4]

    return str(n_funcs[n - 1](input_str))


def apply_n_func(n, input_str):
    """This function applies each nfunc to the expression and displays the
    results one by one. Useful for seeing the effects of each nfunc.

    Args:
        n (int): The n-level
        input_str (str): The (raw and escaped) latex string to parse.
    """
    print(0, input_str)
    for i in range(n):
        print(i + 1, N(i + 1, input_str))

def apply_n_func_result_only(n, input_str):
    results = []
    results.append(input_str)
    for i in range(n):
        result = N(i + 1, input_str)
        results.append(result)
    # Print only the final result
    print(results[-1])


if __name__ == '__main__':
    args = sys.argv

    # Take in two arguments, the latex expression to parse and the n-level
    if len(args) == 3:
        raw_expr = args[1]
        n_level = int(args[2])

        apply_n_func(n_level, raw_expr)
        apply_n_func_result_only(n_level, raw_expr)
    else:
        print("Please provide a LaTeX expression and the n-level as follows:")
        print(r'> python main.py "\frac{a+b}{c}" 2')
        print()
        print(r"Where \frac{a+b}{c} is the expression and 2 is the n-level")
