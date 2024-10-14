import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldedExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,folded,exp_op,exp_left,exp_right",
    [
        (
            "1 * 2",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 / 2",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 * 2 / 3",
            True,
            Token.symbol(9, 10),
            MultExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
                Token.symbol(5, 6),
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "1 * (2 / 3)",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            MultExpr(
                IntLiteral(Token.int_literal(8, 9)),
                IntLiteral(Token.int_literal(12, 13)),
                Token.symbol(10, 11),
            ),
        ),
        (
            "1 * 2 / 3 * 4",
            True,
            Token.symbol(13, 14),
            MultExpr(
                MultExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                    Token.symbol(5, 6),
                ),
                IntLiteral(Token.int_literal(11, 12)),
                Token.symbol(9, 10),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "-1 * 2",
            True,
            Token.symbol(6, 7),
            UnaryExpr(Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 * -2",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            UnaryExpr(Token.symbol(7, 8), IntLiteral(Token.int_literal(8, 9))),
        ),
        (
            "-1 * -2",
            True,
            Token.symbol(6, 7),
            UnaryExpr(Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
            UnaryExpr(Token.symbol(8, 9), IntLiteral(Token.int_literal(9, 10))),
        ),
        (
            "1 ^ 2 * 3",
            True,
            Token.symbol(9, 10),
            ExpExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "1 * 2 ^ 3",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(11, 12)),
            ),
        ),
        (
            "1 ^ 2 * 3 ^ 4",
            True,
            Token.symbol(9, 10),
            ExpExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            ExpExpr(
                IntLiteral(Token.int_literal(11, 12)),
                IntLiteral(Token.int_literal(15, 16)),
            ),
        ),
    ],
)
def test_parse_mult_expr(exp_code: str, folded: bool, exp_op: Token, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mult_expr: Expr = ExpressionParser.parse_mult_expr(tkzr)
        if folded:
            assert isinstance(mult_expr, FoldedExpr)
            assert isinstance(mult_expr.expr_to_fold, MultExpr)
            assert mult_expr.expr_to_fold.op == exp_op
            assert mult_expr.expr_to_fold.left == exp_left
            assert mult_expr.expr_to_fold.right == exp_right
