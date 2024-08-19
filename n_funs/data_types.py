import config


def expr_key(expr):
    """Generate a sorting key for the expressions/objects encountered in
    the ast.

    Args:
        expr (Expr/int): The expression to get a key for.

    Returns:
        tuple(): (precedence_level, length, children, exponent)
    """
    ordering = {
        Number: 0,
        Symbol: 1,
        Sum: 2,
        Mul: 2,
        Fraction: 3,
        Root: 3,
        Factorial: 4
    }

    if isinstance(expr, int):
        return (0, 1, expr, 1)

    temp = []
    for sub_expr in expr.get_children():
        temp += list(expr_key(sub_expr))

    if isinstance(expr, (Number, Symbol)):
        temp.append(str(expr))

    return (ordering[type(expr)], len(expr), tuple(temp), expr_key(expr.exponent))


# Represents something that can be used in multiplication.
class Expr:
    def __init__(self):
        self.has_parens = False
        self.is_negative = False
        self.exponent = 1

        self.print_minus = True

    def get_children(self) -> list:
        return []

    def traverse_children(self, func) -> None:
        # Because 1 is the default value, when an expression basically has no
        # specific exponent. Then we just ignore it and leave it be.
        if type(self.exponent) != int and type(self.exponent) != float:
            self.exponent = func(self.exponent)

    def get_factors(self, filter=None):
        if filter != None:
            if filter(self):
                return [self]
            else:
                return []
        else:
            return [self]

    def get_terms(self, filter=None):
        return self.get_factors(filter)

    def to_latex(self):
        raise NotImplementedError("To LaTeX method not implemented")

    def is_like(self, other) -> bool:
        return self.exponent == other.exponent

    def copy_from_to(src, dest):
        dest.has_parens = src.has_parens
        dest.exponent = src.exponent
        dest.print_minus = src.print_minus
        dest.is_negative = src.is_negative

    def __add__(self, other):
        if isinstance(other, Expr):
            return Sum([self, other])
        raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, Expr):
            return Mul([self, other])
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if isinstance(other, Expr):
            return self.exponent == other.exponent and (self.is_negative == other.is_negative)
        return False

    def __pow__(self, other):
        temp = self.create_copy(True)
        temp.exponent = temp.exponent * other

        return temp

    def __rpow__(self, base):
        return base.__pow__(self)

    def __str__(self) -> str:
        temp = self.to_latex()

        if self.has_parens or config.always_parens:
            temp = f"({temp})"

        if self.exponent != 1:
            temp = f"{temp}^{{{self.exponent}}}"

        if self.is_negative and self.print_minus:
            temp = f"-{temp}"

        return temp

    def __repr__(self) -> str:
        return self.to_latex()


# Represents a number
class Number(Expr):
    def __init__(self, value, is_integer=True):
        super().__init__()

        self.value = abs(value)
        self.is_integer = is_integer

        # Precision in case it is a floating point
        self.prec = 3

        self.is_negative = value < 0

    def traverse_children(self, func) -> None:
        super().traverse_children(func)

    def get_value(self):
        return -self.value if self.is_negative else self.value

    def to_latex(self) -> str:
        if self.is_integer:
            return str(self.value)
        else:
            return f"{float(self.value):.3f}"

    def is_like(self, other) -> bool:
        return super().is_like(other)

    def create_copy(self, is_full_copy):
        temp = Number(self.get_value())

        Expr.copy_from_to(self, temp)

        if is_full_copy:
            temp.is_integer = self.is_integer

        return temp

    def __len__(self):
        return 1

    def __neg__(self):
        temp = self.create_copy(True)
        temp.is_negative ^= True

        return temp

    def __add__(self, other):
        if isinstance(other, (int, float)):
            temp = Sum([self, Number(other, type(other) == int)])

            return temp
        else:
            return super().__add__(other)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        temp = Mul([self, other])

        if isinstance(other, (int, float)):
            temp = Mul([self, Number(other, type(other) == int)])

            return temp
        else:
            return super().__mul__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __abs__(self):
        temp = self.create_copy(False)
        temp.is_negative = False

        return temp

    def __eq__(self, other):
        if super().__eq__(other):
            if isinstance(other, Number):
                return self.get_value() == other.get_value()
        elif isinstance(other, int):
            return self.get_value() == other

        return False

    def __lt__(self, other):
        if isinstance(other, (int, float)):
            return self.get_value() < other
        return self.get_value() < other.get_value()

    def __iadd__(self, other):
        if isinstance(other, Number):
            result = self.get_value() + other.get_value()

            self.value = abs(result)
            self.is_negative = result < 0

            return self
        else:
            raise TypeError("Cannot add this to Number instance")

# Represents a symbol or variable
class Symbol(Expr):
    def __init__(self, name):
        super().__init__()

        self.name = name

    def traverse_children(self, func) -> None:
        super().traverse_children(func)

    def degree(self) -> Expr:
        return self.exponent

    def to_latex(self) -> str:
        return self.name

    def is_like(self, other) -> bool:
        if super().is_like(other):
            if isinstance(other, Symbol):
                return self.name == other.name
            elif isinstance(other, Mul):
                other_vars = other.get_factors(lambda x: not isinstance(x, Number))

                if len(other_vars) == 1:
                    return other_vars[0] == self

        return False

    def create_copy(self, is_full_copy):
        temp = Symbol(self.name)

        Expr.copy_from_to(self, temp)

        return temp

    def __eq__(self, other):
        if super().__eq__(other):
            if isinstance(other, Symbol):
                return self.name == other.name

        return False

    def __lt__(self, other):
        return self.name < other.name

    def __len__(self):
        return 1


# Class representing multiplication with multiple factors
class Mul(Expr):
    def __init__(self, factors=None):
        super().__init__()

        self.factors = factors or []
        self.is_implicit = [False for _ in range(len(self.factors))]

    def traverse_children(self, func) -> None:
        super().traverse_children(func)

        new_factors = []

        for term in self.factors:
            new_factors.append(func(term))

        self.factors = new_factors

    def get_factors(self, filter=None) -> list:
        if filter == None:
            return self.factors

        return [factor for factor in self.factors if filter(factor)]

    def get_terms(self, filter=None):
        if filter != None:
            if filter(self):
                return [self]
            else:
                return []
        else:
            return [self]

    def is_like(self, other):
        """Check if this term can be added with the other term.
        Example: 3x and 3x are alike, they can be added together into a single term.
        3x and 3y are not alike, they cannot be added into a single term.
        """
        var_filter = lambda fac: not isinstance(fac, Number)
        self_vars = self.get_factors(var_filter)

        if len(self_vars) == len(other.get_factors(var_filter)):
            other_factors = other.get_factors(var_filter)

            for var_a in self.get_factors(var_filter):
                if var_a not in other_factors:
                    return False
            return True
        else:
            return False

    # Get the polynomial order of this product
    def degree(self) -> int:
        max_degree = 0

        for variable in self.get_factors(lambda x: isinstance(x, Symbol)):
            if variable.exponent > max_degree:
                max_degree = variable.exponent

        return max_degree

    def sort_children(self) -> None:
        # Similar to sorting sums, after sorting the order might change.
        # So it is not logical to keep track of implicit multiplications by
        # index anymore. So just set them all to explcit products.
        self.is_implicit = [False for _ in self.factors]

        self.factors.sort(key=expr_key)

    def add_factor(self, index, factor: Expr, is_implicit=False) -> None:
        if index == -1:
            self.factors.append(factor)
            self.is_implicit.append(is_implicit)
        else:
            self.factors.insert(index, factor)
            self.is_implicit.insert(index, is_implicit)

    def remove_factor(self, factor) -> None:
        self.factors.remove(factor)

    def get_children(self) -> list:
        return self.factors

    def to_latex(self) -> str:
        temp = f"{self.factors[0]}"

        for i in range(1, len(self.factors)):
            if self.is_implicit[i - 1]:
                temp += f"{self.factors[i]}"
            else:
                temp += f" * {self.factors[i]}"

        return temp

    def create_copy(self, is_full_copy):
        temp = Mul()

        Expr.copy_from_to(self, temp)

        if is_full_copy:
            for factor in self.get_factors():
                temp.add_factor(-1, factor.create_copy(True), False)
            temp.is_implicit = self.is_implicit

        return temp

    def __eq__(self, other) -> bool:
        if super().__eq__(other):
            if len(self) == len(other):
                other_factors = other.get_factors()

                for i, fac in enumerate(self.get_factors()):
                    if fac != other_factors[i]:
                        return False
                return True

        return False

    def __len__(self) -> int:
        return len(self.factors)

    def __mul__(self, other):
        if self.has_parens:
            return Mul([self, other])
        else:
            temp = self.create_copy(True)
            temp.add_factor(-1, other, False)

            return temp

    def __rmul__(self, other):
        return self.__mul__(other)


# Class representing addition with multiple terms
class Sum(Expr):
    def __init__(self, terms=None):
        super().__init__()

        self.terms = terms or []

        if terms == None:
            self.is_subtraction = []
        else:
            self.is_subtraction = [False for _ in terms]

    def traverse_children(self, func) -> None:
        super().traverse_children(func)

        new_terms = []

        for term in self.terms:
            new_terms.append(func(term))

        self.terms = new_terms

    def sort_children(self):
        # Because the ordering might change with sorting, checking per index
        # whether a term is part of a subtraction is not valid anymore.
        # Thus we just print every minus sign in case of a negative value, and just use plus signs for addition.
        self.is_subtraction = [False for _ in self.terms]  # Fill with False (no subtractions anymore)

        for term in self.terms:
            term.print_minus = True

        self.terms.sort(key=expr_key)

    def get_terms(self, filter=None) -> list:
        if filter == None:
            return self.terms

        return [term for term in self.terms if filter(term)]

    def add_term(self, index: int, term: Expr, is_subtraction: bool = False):
        if index == -1:
            self.terms.append(term)
            self.is_subtraction.append(is_subtraction)
        else:
            self.terms.insert(index, term)
            self.is_subtraction.insert(index, is_subtraction)

    def get_children(self):
        return self.terms

    def to_latex(self) -> str:
        if self.terms:
            temp = f"{self.terms[0]}"

            # For each term, determine whether to print a plus or minus
            # If it's a minus (substraction), then don't print a unary negative sign
            for i in range(1, len(self.terms)):
                if self.is_subtraction[i]:
                    temp += f" - {self.terms[i]}"
                else:
                    temp += f" + {self.terms[i]}"

            return temp
        else:
            return ""

    def is_like(self, other):
        if len(self) == len(other):
            other_terms = other.get_terms()

            for var_a in self.get_terms():
                if var_a not in other_terms:
                    return False
            return True

        return False

    def create_copy(self, is_full_copy: bool):
        """Create a new instance of this class, copy the Expr attributes.
        If is_full_copy is True, then also copy the class specific attributes.
        """
        temp = Sum()

        Expr.copy_from_to(self, temp)

        if is_full_copy:
            for term in self.get_terms():
                temp.add_term(-1, term.create_copy(True), False)

            temp.is_subtraction = list(self.is_subtraction)

        return temp

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return self.__add__(Number(other, type(other) == int))

        if self.has_parens:
            return Sum([self, other])
        else:
            temp = self.create_copy(False)

            temp.add_term(-1, other, False)

            return temp

    def __radd__(self, other):
        return self.__add__(other)

    def __iter__(self):
        for fac in self.get_factors():
            yield fac

    def __eq__(self, other) -> bool:
        if super().__eq__(other):
            if len(self) == len(other):
                other_terms = other.get_terms()

                for i, fac in enumerate(self.get_terms()):
                    if fac != other_terms[i]:
                        return False
                return True

        return False

    def __len__(self):
        return len(self.terms)


# Class representing a fraction \frac{num}{denom}
class Fraction(Expr):
    def __init__(self, num, denom) -> None:
        super().__init__()

        self.num = num
        self.denom = denom

    def traverse_children(self, func) -> None:
        super().traverse_children(func)

        self.num = func(self.num)
        self.denom = func(self.denom)

    def get_children(self):
        return [self.num, self.denom]

    def to_latex(self) -> str:
        return fr"\frac{{{self.num}}}{{{self.denom}}}"

    def create_copy(self, is_full_copy: bool):
        temp = Fraction()

        Expr.copy_from_to(self, temp)

        if is_full_copy:
            temp.num = self.num.create_copy()
            temp.denom = self.denom.create_copy()

        return temp

    def __eq__(self, other):
        if super().__eq__(other) and isinstance(other, Fraction):
            return self.num == other.num and self.denom == other.denom

        return False


# Class representing a square root
class Root(Expr):
    def __init__(self, base) -> None:
        super().__init__()

        self.base = base

    def traverse_children(self, func) -> None:
        super().traverse_children(func)

        self.base = func(self.base)

    def get_children(self):
        return [self.base]

    def to_latex(self) -> str:
        return fr"\sqrt{{{self.base}}}"

    def create_copy(self, is_full_copy: bool):
        temp = Root(self.base.create_copy())

        Expr.copy_from_to(self, temp)

        return temp

    def __eq__(self, other) -> bool:
        if super().__eq__(other):
            if isinstance(other, Root):
                return self.base == other.base

        return False


# Represents a factorial
class Factorial(Expr):
    def __init__(self, val):
        super().__init__()

        self.val = val

    def traverse_children(self, func) -> None:
        super().traverse_children(func)

        self.val = func(self.val)

    def get_children(self):
        return [self.val]

    def to_latex(self) -> str:
        return fr"{self.val}!"

    def create_copy(self, is_full_copy: bool):
        temp = Factorial(self.val.create_copy())

        Expr.copy_from_to(self, temp)

        return temp

    def __eq__(self, other) -> bool:
        if super().__eq__(other):
            if isinstance(other, Factorial):
                return self.val == other.val

        return False
