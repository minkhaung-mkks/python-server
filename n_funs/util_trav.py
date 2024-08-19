from .data_types import *


def trav_flatten_exprs(root: Expr):
    """If there are any sums or products with a single term/factor,
    just change the expression to that term/factor.
    """
    root.traverse_children(trav_flatten_exprs)


    if isinstance(root, Mul):
        if len(root) == 1:
            return root.get_factors()[0]

    if isinstance(root, Sum):
        if len(root) == 1:
            return root.get_terms()[0]

    return root


def trav_remove_identity(root: Expr):
    root.traverse_children(trav_remove_identity)

    if isinstance(root, Fraction):
        if root.num == root.denom:
            root = Number(1)


    if isinstance(root, Mul):
        one_factors = root.get_factors(lambda x: isinstance(x, Number) and abs(x) == 1)

        # Factors that are equal to one can be omitted
        for one_fac in one_factors:
            root.remove_factor(one_fac)

    return root


def cleanup_traversals(ast_root: Expr):
    ast_root = trav_flatten_exprs(ast_root)
    ast_root = trav_remove_identity(ast_root)

    return ast_root
