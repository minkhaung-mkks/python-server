# n_funcs/n_func.py
"""Simple library to parse and manipulate LaTeX math expressions.
Not entirely finished and tested yet, but currently provides the basis.
Author: Robbie Koevoets
"""
from .n1 import N1
from .n2 import N2
from .n3 import N3
from .n4 import N4

def N(n, input_str):
    """The N-func, use this to apply the nfunc of your choosing."""
    n_funcs = [N1, N2, N3, N4]
    return str(n_funcs[n - 1](input_str))

def apply_n_func(n, input_str):
    """Applies nfunc to the expression and returns the results as a dictionary."""
    results = {}
    results['input'] = input_str
    for i in range(n):
        results[f'N{i + 1}'] = N(i + 1, input_str)
    return results
