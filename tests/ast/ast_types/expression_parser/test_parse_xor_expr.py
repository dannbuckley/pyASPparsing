import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldableExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,expr_value",
    [
        ("True Xor False", True),
        ("True Xor False Xor True", False),
        ("True Xor (False Xor True)", False),
        ("True Xor False Xor True Xor False", False),
        ("True Or False Xor True", False),
        ("True Xor False Or True", False),
        ("True Or False Xor True Or False", False),
    ],
)
def test_parse_xor_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        xor_expr: Expr = ExpressionParser.parse_xor_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(xor_expr, EvalExpr)
        assert xor_expr.expr_value == expr_value
