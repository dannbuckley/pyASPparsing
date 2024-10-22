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
        ("4 \\ 2", 2),
        ("4 \\ 2 \\ 1", 2),
        ("4 \\ (2 \\ 1)", 2),
        ("8 \\ 4 \\ 2 \\ 1", 1),
        ("2 * 4 \\ 8", 1),
        ("4 \\ 2 * 8", 0),
        ("2 * 4 \\ 4 * 2", 1),
    ],
)
def test_parse_int_div_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        int_div_expr: Expr = ExpressionParser.parse_int_div_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(int_div_expr, EvalExpr)
        assert int_div_expr.expr_value == expr_value
