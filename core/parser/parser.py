from .nodes import *
from ..lexer.tokens import Token
from ..errors.error import *

COMPARISONS = ("LT", "GT", "LTEQ", "GTEQ", "DBEQ", "NOTEQ")


class Parser:
    def __init__(self, tokens):
        self.tokens = iter(tokens)
        self.current: Token or None = None
        self.nodes = []
        self.next()

    def next(self):
        try:
            self.current = next(self.tokens)
        except StopIteration:
            self.current = None

    def eof(self):
        return self.current.type == "EOF"

    def parse(self):
        while self.current.type != "EOF":
            res, e = self.expr()
            if e:
                return None, e

            self.nodes.append(res)

        return self.nodes, None

    def look_for_body(self):
        if self.current.type != "LCURLY":
            return None, SnowError.SyntaxError(self.current.start)

        self.next()

        children = []
        while not self.eof() and self.current.type != "RCURLY":
            body, e = self.expr()
            if e:
                return None, e
            children.append(body)

        if self.eof():
            return None, SnowError.SyntaxError(self.current.end)

        return children, None

    """EXPR"""

    def expr(self):
        if self.current.type == "KEYWORD":
            if self.current.value == "out":
                start = self.current.start
                self.next()
                res, e = self.expr()
                if e:
                    return None, e
                return OutNode(res, start, res.end), None

            if self.current.value == "if":
                start = self.current.start
                self.next()

                cond, e = self.comp()
                if e:
                    return None, e

                children, e = self.look_for_body()
                if e:
                    return None, e

                end = self.current.end
                self.next()

                if self.current.type == "KEYWORD" and self.current.value == "else":
                    self.next()
                    else_children, e = self.look_for_body()
                    if e:
                        return None, e

                    end = self.current.end
                    self.next()

                else:
                    else_children = None

                return IfNode(cond, children, else_children, start, end), None

            if self.current.value == "loop":
                start = self.current.start
                self.next()

                children, e = self.look_for_body()
                if e:
                    return None, e

                end = self.current.end
                self.next()

                return LoopNode(children, start, end), None

            if self.current.value == "repeat":
                start = self.current.start
                self.next()
                times, e = self.comp()
                if e:
                    return None, e

                children, e = self.look_for_body()
                if e:
                    return None, e

                end = self.current.end
                self.next()

                return RepeatNode(times, children, start, end), None

            if self.current.value == "break":
                start = self.current.start
                end = self.current.end
                self.next()
                return BreakNode(start, end), None

        res, e = self.comp()
        if e:
            return None, e

        return res, None

    """COMP"""

    def comp(self):
        left, e = self.layer_1()
        if e:
            return None, e

        if self.current.type in COMPARISONS:
            l = []
            while not self.eof() and self.current.type in COMPARISONS:
                comp = self.current
                self.next()
                right, e = self.layer_1()
                if e:
                    return None, e
                l.append(ComparisonNode(left, comp, right))
                left = right

            return CompListNode(l), None

        return left, None

    """LAYERS"""

    def layer_1(self):
        left, e = self.layer_2()
        if e:
            return None, e

        while not self.eof() and self.current.type in ("ADD", "MIN"):
            op = self.current
            self.next()

            right, e = self.layer_2()
            if e:
                return None, e

            left = OperationNode(left, op, right)

        return left, None

    def layer_2(self):
        left, e = self.factor()
        if e:
            return None, e

        while not self.eof() and self.current.type in ("MUL", "DIV"):
            op = self.current
            self.next()

            right, e = self.factor()
            if e:
                return None, e

            left = OperationNode(left, op, right)

        return left, None

    """FACTOR"""

    def factor(self):
        current = self.current

        if current.type == "LPAREN":
            self.next()
            res, e = self.expr()
            if e:
                return None, e

            if self.current.type != "RPAREN":
                return None, SnowError.SyntaxError(self.current.start)

            self.next()
            return res, None

        # INT, FLOAT
        if current.type in ("INT", "FLOAT"):
            self.next()
            return NumberNode(current.value, current.start, current.end), None

        # ID
        if current.type == "ID":
            # Identifier
            self.next()
            name = current.value
            if self.current.type == "EQ":
                self.next()
                value, e = self.expr()
                if e:
                    return None, e
                return VarAssignNode(name, value, current.start, self.current.end), None

            if self.current.type == "WALRUS":
                self.next()
                value, e = self.expr()
                if e:
                    return None, e
                return WalrusVarAssignNode(name, value, current.start, self.current.end), None

            return VarAccessNode(name, current.start, current.end), None

        return None, SnowError.SyntaxError(self.current.start)
