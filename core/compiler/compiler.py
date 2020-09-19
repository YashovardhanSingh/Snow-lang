from ..lexer.lexer import Lexer
from ..parser.parser import Parser
from ..errors.pointer import point


def run(file):
    with open(file, "r") as f:
        code = f.read()

    lexer = Lexer(code)
    res = lexer.lex()
    tokens, error = res

    if error:
        print(point(code, error.pos))
        print(f"<{file}> " + repr(error))
        return

    parser = Parser(tokens)
    res = parser.parse()
    nodes, error = res

    if error:
        print(point(code, error.pos))
        print(f"<{file}> " + repr(error))
        return

    print("\n".join(map(repr, nodes)))