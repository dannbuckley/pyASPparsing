import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldableExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,folded,exp_left,exp_right",
    [
        (
            "True Or False",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(11, 16)),
        ),
        (
            "True Or False Or True",
            True,
            OrExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(11, 16)),
            ),
            BoolLiteral(Token.identifier(20, 24)),
        ),
        (
            "True Or (False Or True)",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            OrExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(21, 25)),
            ),
        ),
        (
            "True Or False Or True Or False",
            True,
            OrExpr(
                OrExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(11, 16)),
                ),
                BoolLiteral(Token.identifier(20, 24)),
            ),
            BoolLiteral(Token.identifier(28, 33)),
        ),
        (
            "True And False Or True",
            True,
            AndExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(21, 25)),
        ),
        (
            "True Or False And True",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            AndExpr(
                BoolLiteral(Token.identifier(11, 16)),
                BoolLiteral(Token.identifier(21, 25)),
            ),
        ),
        (
            "True And False Or True And False",
            True,
            AndExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            AndExpr(
                BoolLiteral(Token.identifier(21, 25)),
                BoolLiteral(Token.identifier(30, 35)),
            ),
        ),
    ],
)
def test_parse_or_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        or_expr: Expr = ExpressionParser.parse_or_expr(tkzr)
        if folded:
            assert isinstance(or_expr, FoldableExpr)
            assert isinstance(or_expr.wrapped_expr, OrExpr)
            assert or_expr.wrapped_expr.left == exp_left
            assert or_expr.wrapped_expr.right == exp_right
