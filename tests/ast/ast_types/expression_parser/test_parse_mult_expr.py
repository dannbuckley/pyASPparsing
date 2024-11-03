import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import *
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,expr_value",
    [
        ("1 * 2", 2),
        ("1 / 2", 0.5),
        ("1 * 2 / 3", 2 / 3),
        ("1 * (2 / 3)", 2 / 3),
        ("1 * 2 / 3 * 4", 8 / 3),
        ("-1 * 2", -2),
        ("1 * -2", -2),
        ("-1 * -2", 2),
        ("1 ^ 2 * 3", 3),
        ("1 * 2 ^ 3", 8),
        ("1 ^ 2 * 3 ^ 4", 81),
    ],
)
def test_parse_mult_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mult_expr: Expr = ExpressionParser.parse_mult_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(mult_expr, EvalExpr)
        assert mult_expr.expr_value == expr_value


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            # no moves made, constants stay on the left
            "1 * 2 * a",
            EvalExpr(2),
            LeftExpr("a"),
        ),
        (
            # 'a' and '2' swap places
            "1 * a * 2",
            EvalExpr(2),
            LeftExpr("a"),
        ),
        (
            # 'a' moved to end of expression
            "a * 1 * 2",
            EvalExpr(2),
            LeftExpr("a"),
        ),
    ],
)
def test_parse_mult_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mult_expr: Expr = ExpressionParser.parse_mult_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(mult_expr, MultExpr)
        assert mult_expr.left == exp_left
        assert mult_expr.right == exp_right
