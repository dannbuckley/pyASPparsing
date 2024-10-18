import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import *
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,folded,exp_left,exp_right",
    [
        (
            "1 * 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 / 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            MultReciprocal(IntLiteral(Token.int_literal(7, 8))),
        ),
        (
            "1 * 2 / 3",
            True,
            MultExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            MultReciprocal(IntLiteral(Token.int_literal(11, 12))),
        ),
        (
            "1 * (2 / 3)",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            MultExpr(
                IntLiteral(Token.int_literal(8, 9)),
                MultReciprocal(IntLiteral(Token.int_literal(12, 13))),
            ),
        ),
        (
            "1 * 2 / 3 * 4",
            True,
            MultExpr(
                MultExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                MultReciprocal(IntLiteral(Token.int_literal(11, 12))),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "-1 * 2",
            True,
            UnaryExpr(Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 * -2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            UnaryExpr(Token.symbol(7, 8), IntLiteral(Token.int_literal(8, 9))),
        ),
        (
            "-1 * -2",
            True,
            UnaryExpr(Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
            UnaryExpr(Token.symbol(8, 9), IntLiteral(Token.int_literal(9, 10))),
        ),
        (
            "1 ^ 2 * 3",
            True,
            ExpExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "1 * 2 ^ 3",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(11, 12)),
            ),
        ),
        (
            "1 ^ 2 * 3 ^ 4",
            True,
            ExpExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            ExpExpr(
                IntLiteral(Token.int_literal(11, 12)),
                IntLiteral(Token.int_literal(15, 16)),
            ),
        ),
        (
            # no moves made, constants stay on the left
            "1 * 2 * a",
            False,
            FoldableExpr(
                MultExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                )
            ),
            LeftExpr(QualifiedID([Token.identifier(11, 12)])),
        ),
        (
            # 'a' and '2' swap places
            "1 * a * 2",
            False,
            FoldableExpr(
                MultExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(11, 12)),
                )
            ),
            LeftExpr(QualifiedID([Token.identifier(7, 8)])),
        ),
        (
            # 'a' moved to end of expression
            "a * 1 * 2",
            False,
            FoldableExpr(
                MultExpr(
                    IntLiteral(Token.int_literal(7, 8)),
                    IntLiteral(Token.int_literal(11, 12)),
                )
            ),
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
        ),
    ],
)
def test_parse_mult_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mult_expr: Expr = ExpressionParser.parse_mult_expr(tkzr)
        if folded:
            assert isinstance(mult_expr, FoldableExpr)
            assert isinstance(mult_expr.wrapped_expr, MultExpr)
            assert mult_expr.wrapped_expr.left == exp_left
            assert mult_expr.wrapped_expr.right == exp_right
