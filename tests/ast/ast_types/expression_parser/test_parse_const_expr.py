import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("1.0E3", EvalExpr(1.0e3)),
        ('"Hello, world!"', EvalExpr("Hello, world!")),
        ("#1970/01/01#", ConstExpr(Token.date_literal(3, 15))),
        ("0", EvalExpr(0)),
        ("&H7F", EvalExpr(127)),
        ("&777", EvalExpr(511)),
        ("True", EvalExpr(True)),
        ("False", EvalExpr(False)),
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
