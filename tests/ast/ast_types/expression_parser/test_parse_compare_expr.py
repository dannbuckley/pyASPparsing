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
        ("1 >= 1", True),
        ("1 <= 1", True),
        ("1 > 1", False),
        ("1 < 1", False),
        ("1 <> 1", False),
        ("1 = 1", True),
    ],
)
def test_parse_compare_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        compare_expr: Expr = ExpressionParser.parse_compare_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(compare_expr, EvalExpr)
        assert compare_expr.expr_value == expr_value
