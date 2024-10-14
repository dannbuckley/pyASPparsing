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
            "True And False",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 17)),
        ),
        (
            "True And False And True",
            True,
            AndExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True And (False And True)",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            AndExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True And False And True And False",
            True,
            AndExpr(
                AndExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "Not False And True",
            True,
            NotExpr(BoolLiteral(Token.identifier(7, 12))),
            BoolLiteral(Token.identifier(17, 21)),
        ),
        (
            "True And Not False",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            NotExpr(BoolLiteral(Token.identifier(16, 21))),
        ),
        (
            "Not False And Not False",
            True,
            NotExpr(BoolLiteral(Token.identifier(7, 12))),
            NotExpr(BoolLiteral(Token.identifier(21, 26))),
        ),
        (
            "Not Not True And True",
            True,
            BoolLiteral(Token.identifier(11, 15)),  # 'Not Not' ignored
            BoolLiteral(Token.identifier(20, 24)),
        ),
        (
            "1 = 1 And True",
            True,
            CompareExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
                CompareExprType.COMPARE_EQ,
            ),
            BoolLiteral(Token.identifier(13, 17)),
        ),
        (
            "True And 1 = 1",
            True,
            BoolLiteral(Token.identifier(3, 7)),
            CompareExpr(
                IntLiteral(Token.int_literal(12, 13)),
                IntLiteral(Token.int_literal(16, 17)),
                CompareExprType.COMPARE_EQ,
            ),
        ),
        (
            "1 = 1 And 2 = 2",
            True,
            CompareExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
                CompareExprType.COMPARE_EQ,
            ),
            CompareExpr(
                IntLiteral(Token.int_literal(13, 14)),
                IntLiteral(Token.int_literal(17, 18)),
                CompareExprType.COMPARE_EQ,
            ),
        ),
        (
            "Not 1 <> 1 And 2 = 2",
            True,
            NotExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(7, 8)),
                    IntLiteral(Token.int_literal(12, 13)),
                    CompareExprType.COMPARE_LTGT,
                )
            ),
            CompareExpr(
                IntLiteral(Token.int_literal(18, 19)),
                IntLiteral(Token.int_literal(22, 23)),
                CompareExprType.COMPARE_EQ,
            ),
        ),
        (
            "1 = 1 And Not 2 <> 2",
            True,
            CompareExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
                CompareExprType.COMPARE_EQ,
            ),
            NotExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(17, 18)),
                    IntLiteral(Token.int_literal(22, 23)),
                    CompareExprType.COMPARE_LTGT,
                )
            ),
        ),
        (
            "Not 1 <> 1 And Not 2 <> 2",
            True,
            NotExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(7, 8)),
                    IntLiteral(Token.int_literal(12, 13)),
                    CompareExprType.COMPARE_LTGT,
                )
            ),
            NotExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(22, 23)),
                    IntLiteral(Token.int_literal(27, 28)),
                    CompareExprType.COMPARE_LTGT,
                )
            ),
        ),
    ],
)
def test_parse_and_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        and_expr: Expr = ExpressionParser.parse_and_expr(tkzr)
        if folded:
            assert isinstance(and_expr, FoldedExpr)
            assert isinstance(and_expr.expr_to_fold, AndExpr)
            assert and_expr.expr_to_fold.left == exp_left
            assert and_expr.expr_to_fold.right == exp_right
