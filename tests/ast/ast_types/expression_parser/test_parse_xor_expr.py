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
            "True Xor False",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 17)),
        ),
        (
            "True Xor False Xor True",
            True,
            XorExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Xor (False Xor True)",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            XorExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True Xor False Xor True Xor False",
            True,
            XorExpr(
                XorExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "True Or False Xor True",
            True,
            OrExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(11, 16)),
            ),
            BoolLiteral(Token.identifier(21, 25)),
        ),
        (
            "True Xor False Or True",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            OrExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(21, 25)),
            ),
        ),
        (
            "True Or False Xor True Or False",
            True,
            OrExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(11, 16)),
            ),
            OrExpr(
                BoolLiteral(Token.identifier(21, 25)),
                BoolLiteral(Token.identifier(29, 34)),
            ),
        ),
    ],
)
def test_parse_xor_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        xor_expr: Expr = ExpressionParser.parse_xor_expr(tkzr)
        if folded:
            assert isinstance(xor_expr, FoldableExpr)
            assert isinstance(xor_expr.wrapped_expr, XorExpr)
            assert xor_expr.wrapped_expr.left == exp_left
            assert xor_expr.wrapped_expr.right == exp_right
