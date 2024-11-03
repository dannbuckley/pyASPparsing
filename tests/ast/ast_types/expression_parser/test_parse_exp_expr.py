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
        ("1 ^ 2", 1),
        ("2 ^ 2 ^ 3", 256),
        (
            # NOT equivalent to above "1 ^ 2 ^ 3"
            "(2 ^ 2) ^ 3",
            64,
        ),
        ("1 ^ 2 ^ 3 ^ 4", 1),
    ],
)
def test_parse_exp_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        exp_expr: Expr = ExpressionParser.parse_exp_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(exp_expr, EvalExpr)
        assert exp_expr.expr_value == expr_value


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            # right argument is evaluated first
            # don't know what "a" is, so can't do constant folding
            "1 ^ 2 ^ a",
            EvalExpr(1),
            ExpExpr(
                EvalExpr(2),
                LeftExpr("a"),
            ),
        ),
        (
            # "a" is on the left
            # the right can be folded
            "a ^ 1 ^ 2",
            LeftExpr("a"),
            EvalExpr(1),
        ),
        (
            "1 ^ a ^ 2",
            EvalExpr(1),
            ExpExpr(
                LeftExpr("a"),
                EvalExpr(2),
            ),
        ),
        (
            # only "4 ^ 5" can be folded
            "a ^ 1 ^ 2 ^ b ^ 3 ^ c ^ 4 ^ 5",
            LeftExpr("a"),
            ExpExpr(
                EvalExpr(1),
                ExpExpr(
                    EvalExpr(2),
                    ExpExpr(
                        LeftExpr("b"),
                        ExpExpr(
                            EvalExpr(3),
                            ExpExpr(
                                LeftExpr("c"),
                                EvalExpr(4**5),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ],
)
def test_parse_exp_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        exp_expr: Expr = ExpressionParser.parse_exp_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(exp_expr, ExpExpr)
        assert exp_expr.left == exp_left
        assert exp_expr.right == exp_right
