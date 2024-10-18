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
            "True Imp True",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 16)),
        ),
        (
            "True Imp False Imp True",
            True,
            ImpExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Imp (False Imp True)",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            ImpExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True Imp False Imp True Imp False",
            True,
            ImpExpr(
                ImpExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "True Eqv False Imp True",
            True,
            EqvExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Imp False Eqv True",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            EqvExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(22, 26)),
            ),
        ),
        (
            "True Eqv False Imp True Eqv False",
            True,
            EqvExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            EqvExpr(
                BoolLiteral(Token.identifier(22, 26)),
                BoolLiteral(Token.identifier(31, 36)),
            ),
        ),
    ],
)
def test_parse_imp_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        imp_expr: Expr = ExpressionParser.parse_imp_expr(tkzr)
        if folded:
            assert isinstance(imp_expr, FoldableExpr)
            assert isinstance(imp_expr.wrapped_expr, ImpExpr)
            assert imp_expr.wrapped_expr.left == exp_left
            assert imp_expr.wrapped_expr.right == exp_right
