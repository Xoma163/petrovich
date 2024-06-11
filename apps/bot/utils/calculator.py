# By E.Dubovitsky and A.Popova
from apps.bot.classes.const.exceptions import PWarning

ACCURACY = 15


class Symbol:

    def match(self, expr):
        raise NotImplementedError

    def compute(self, left, right):
        raise NotImplementedError

    def separations(self, expr):
        raise NotImplementedError


class BinaryOperator(Symbol):

    def __init__(self, character):
        self.character = character

    def match(self, expr):
        return expr.find(self.character) > 0

    def separations(self, expr):
        _split = expr.split(self.character)
        result = []
        for i in range(1, len(_split)):
            left_expr = self.character.join(_split[0:i])
            right_expr = self.character.join(_split[i:len(_split)])
            result.append((left_expr, right_expr))
        return result


class Plus(BinaryOperator):

    def __init__(self):
        super().__init__("+")

    def compute(self, left, right):
        return round(left + right, ACCURACY)


class Minus(BinaryOperator):

    def __init__(self):
        super().__init__("-")

    def compute(self, left, right):
        return round(left - right, ACCURACY)


class Multiply(BinaryOperator):

    def __init__(self):
        super().__init__("*")

    def compute(self, left, right):
        return round(left * right, ACCURACY)


class Divide(BinaryOperator):

    def __init__(self):
        super().__init__("/")

    def compute(self, left, right):
        if right == 0:
            raise ZeroDivisionError
        return round(left / right, ACCURACY)


class Power(BinaryOperator):

    def __init__(self):
        super().__init__("^")

    def compute(self, left, right):
        try:
            return round(left ** right, ACCURACY)
        except OverflowError:
            return float("inf")


class Function(Symbol):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def match(self, expr):
        return expr.startswith(self.left) and expr.endswith(self.right)

    def separations(self, expr):
        return [(expr[len(self.left): -len(self.right)], None)]


class Brackets(Function):

    def __init__(self):
        super().__init__("(", ")")

    def compute(self, left, right):
        return left


# Node - parse tree
class Node:
    def __init__(self, grammar, digit=None, left_child=None, right_child=None):
        self.grammar = grammar
        self.left_child = left_child
        self.right_child = right_child
        if left_child is None:
            self.value = digit
        elif grammar.symbol is None:
            self.value = left_child.value
        elif right_child is None:
            self.value = grammar.symbol.compute(left_child.value, None)
        else:
            self.value = grammar.symbol.compute(left_child.value, right_child.value)


class Grammar:
    """
    splits expression by symbol
    for example, S->T+S. gram_from = "S", left = "T", symbol = "+", right = "S"
    """

    def __init__(self):
        self.gram_from = None
        self.left = None
        self.symbol = None
        self.right = None

    def parse(self, expr):
        if self.symbol is None:
            if self.left == "R":
                try:
                    return Node(self, float(expr))
                except ValueError:
                    return None
            else:
                child_node = Calculator.build_subtree(expr, Calculator.get_possible_grammars(self.left))
                if child_node:
                    return Node(self, left_child=child_node)
                return None
        else:
            if not self.symbol.match(expr):
                return None
            splits = self.symbol.separations(expr)
            for _split in splits:
                possible_node = self.check_separation(_split[0], _split[1])
                if possible_node is not None:
                    return possible_node
            return None

    def check_separation(self, left_expr, right_expr):
        left_child = Calculator.build_subtree(left_expr, Calculator.get_possible_grammars(self.left))
        if left_child is None:
            return None
        right_child = Calculator.build_subtree(right_expr, Calculator.get_possible_grammars(self.right))
        if right_expr and right_child is None:
            return None
        return Node(self, left_child=left_child, right_child=right_child)


class Calculator:
    # all possible arithmetic operations
    COMPUTABLE_SYMBOLS = (Plus(), Minus(), Multiply(), Divide(), Power(), Brackets())
    GRAMS_RAW = [
        "S->S+T",
        "S->S-T",
        "S->T",
        "T->T*G",
        "T->T/G",
        "T->G",
        "G->G^F",
        "G->F",
        "F->(S)",
        "F->R"
    ]
    _COMPILED_GRAMMARS: list = []

    # grammar compilation
    # compiled_grammar is class Grammar instance
    @classmethod
    def compiled_grammars(cls):
        if cls._COMPILED_GRAMMARS:
            return cls._COMPILED_GRAMMARS

        compiled_grammars = []
        for gram_raw in cls.GRAMS_RAW:
            compiled_grammar = Grammar()
            split = gram_raw.split("->", 1)
            compiled_grammar.gram_from = split[0]
            gram_to = split[1]
            compiled_grammar.symbol = cls.find_symbol(gram_to)
            if compiled_grammar.symbol is None:
                compiled_grammar.left = gram_to
                compiled_grammar.right = None
            else:
                split = compiled_grammar.symbol.separations(gram_to)
                if len(split) != 1:
                    raise ValueError("Grammar " + gram_raw + " is not correct")
                compiled_grammar.left = split[0][0]  # left_expr
                compiled_grammar.right = split[0][1]  # right_expr
            compiled_grammars.append(compiled_grammar)
        cls.COMPILED_GRAMMARS = compiled_grammars
        return cls.COMPILED_GRAMMARS

    # searching arithmetic operation in grammar
    @classmethod
    def find_symbol(cls, gram_raw_right):
        for symbol in cls.COMPUTABLE_SYMBOLS:
            if symbol.match(gram_raw_right):
                return symbol
        return None

    @classmethod
    def get_possible_grammars(cls, left_sign):
        result = []
        for grammar in cls.compiled_grammars():
            if left_sign is grammar.gram_from:
                result.append(grammar)
        return result

    @classmethod
    def build_subtree(cls, expr, grammars):
        if not expr:
            return None
        for possible_grammar in grammars:
            child_node = possible_grammar.parse(expr)
            if child_node:
                return child_node
        return None

    @classmethod
    def calculate(cls, expression):
        try:
            root = cls.build_subtree(expression, cls.compiled_grammars())
        except ZeroDivisionError:
            raise PWarning("Деление на 0")
        if root is None:
            raise PWarning("Не смог распарсить выражение")
        else:
            try:
                if isinstance(root.value, float) and root.value == int(root.value):
                    answer = str(int(root.value))
                else:
                    answer = str(root.value)
            except OverflowError:
                if root.value > 0:
                    answer = "∞"
                else:
                    answer = "-∞"
            return answer
