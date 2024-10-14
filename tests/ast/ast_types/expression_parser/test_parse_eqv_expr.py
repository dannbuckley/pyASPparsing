import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldedExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,folded,exp_left,exp_right",
    [
        (
            "True Eqv True",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 16)),
        ),
        (
            "True Eqv False Eqv True",
            True,
            EqvExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Eqv (False Eqv True)",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            EqvExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True Eqv False Eqv True Eqv False",
            True,
            EqvExpr(
                EqvExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "True Xor False Eqv True",
            True,
            XorExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Eqv False Xor True",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            XorExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(22, 26)),
            ),
        ),
        (
            "True Xor False Eqv True Xor False",
            True,
            XorExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            XorExpr(
                BoolLiteral(Token.identifier(22, 26)),
                BoolLiteral(Token.identifier(31, 36)),
            ),
        ),
    ],
)
def test_parse_eqv_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        eqv_expr: Expr = ExpressionParser.parse_eqv_expr(tkzr)
        if folded:
            assert isinstance(eqv_expr, FoldedExpr)
            assert isinstance(eqv_expr.wrapped_expr, EqvExpr)
            assert eqv_expr.wrapped_expr.left == exp_left
            assert eqv_expr.wrapped_expr.right == exp_right
