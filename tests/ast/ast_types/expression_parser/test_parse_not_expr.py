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
        ("Not True", False),
        ("Not False", True),
        ("Not 1 > 1", True),
    ],
)
def test_parse_not_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        not_expr: Expr = ExpressionParser.parse_not_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(not_expr, EvalExpr)
        assert not_expr.expr_value == expr_value
