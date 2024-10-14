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
            "4 \\ 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "4 \\ 2 \\ 1",
            True,
            IntDivExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "4 \\ (2 \\ 1)",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            IntDivExpr(
                IntLiteral(Token.int_literal(8, 9)),
                IntLiteral(Token.int_literal(12, 13)),
            ),
        ),
        (
            "8 \\ 4 \\ 2 \\ 1",
            True,
            IntDivExpr(
                IntDivExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                IntLiteral(Token.int_literal(11, 12)),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "2 * 4 \\ 8",
            True,
            MultExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "4 \\ 2 * 8",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            MultExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(11, 12)),
            ),
        ),
        (
            "2 * 4 \\ 4 * 2",
            True,
            MultExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            MultExpr(
                IntLiteral(Token.int_literal(11, 12)),
                IntLiteral(Token.int_literal(15, 16)),
            ),
        ),
    ],
)
def test_parse_int_div_expr(
    exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        int_div_expr: Expr = ExpressionParser.parse_int_div_expr(tkzr)
        if folded:
            assert isinstance(int_div_expr, FoldedExpr)
            assert isinstance(int_div_expr.wrapped_expr, IntDivExpr)
            assert int_div_expr.wrapped_expr.left == exp_left
            assert int_div_expr.wrapped_expr.right == exp_right
