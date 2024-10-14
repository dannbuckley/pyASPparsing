import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldedExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,folded,exp_cmp_type,exp_left,exp_right",
    [
        (
            "1 Is 1",
            True,
            CompareExprType.COMPARE_IS,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 Is Not 1",
            True,
            CompareExprType.COMPARE_ISNOT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(12, 13)),
        ),
        (
            "1 >= 1",
            True,
            CompareExprType.COMPARE_GTEQ,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 => 1",
            True,
            CompareExprType.COMPARE_EQGT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 <= 1",
            True,
            CompareExprType.COMPARE_LTEQ,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 =< 1",
            True,
            CompareExprType.COMPARE_EQLT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 > 1",
            True,
            CompareExprType.COMPARE_GT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 < 1",
            True,
            CompareExprType.COMPARE_LT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 <> 1",
            True,
            CompareExprType.COMPARE_LTGT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 = 1",
            True,
            CompareExprType.COMPARE_EQ,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
    ],
)
def test_parse_compare_expr(
    exp_code: str, folded: bool, exp_cmp_type: CompareExprType, exp_left: Expr, exp_right: Expr
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        compare_expr: Expr = ExpressionParser.parse_compare_expr(tkzr)
        if folded:
            assert isinstance(compare_expr, FoldedExpr)
            assert isinstance(compare_expr.expr_to_fold, CompareExpr)
            assert compare_expr.expr_to_fold.cmp_type == exp_cmp_type
            assert compare_expr.expr_to_fold.left == exp_left
            assert compare_expr.expr_to_fold.right == exp_right
