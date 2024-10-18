import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldableExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("1.0E3", ConstExpr(Token.float_literal(3, 8))),
        ('"Hello, world!"', ConstExpr(Token.string_literal(3, 18))),
        ("#1970/01/01#", ConstExpr(Token.date_literal(3, 15))),
        ("0", IntLiteral(Token.int_literal(3, 4))),
        ("&H7F", IntLiteral(Token.hex_literal(3, 7))),
        ("&777", IntLiteral(Token.oct_literal(3, 7))),
        ("True", BoolLiteral(Token.identifier(3, 7))),
        ("False", BoolLiteral(Token.identifier(3, 8))),
        ("Nothing", Nothing(Token.identifier(3, 10))),
        ("Null", Nothing(Token.identifier(3, 7))),
        ("Empty", Nothing(Token.identifier(3, 8))),
    ],
)
def test_parse_const_expr(expr_code: str, expr_val: Expr):
    with Tokenizer(f"<%={expr_code}%>", False) as tkzr:
        tkzr.advance_pos()
        const_expr: Expr = ExpressionParser.parse_const_expr(tkzr)
        assert const_expr == expr_val
