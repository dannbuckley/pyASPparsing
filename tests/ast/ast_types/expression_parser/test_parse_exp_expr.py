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
            "1 ^ 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 ^ 2 ^ 3",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(11, 12)),
            ),
        ),
        (
            # NOT equivalent to above "1 ^ 2 ^ 3"
            "(1 ^ 2) ^ 3",
            True,
            ExpExpr(
                IntLiteral(Token.int_literal(4, 5)), IntLiteral(Token.int_literal(8, 9))
            ),
            IntLiteral(Token.int_literal(13, 14)),
        ),
        (
            "1 ^ 2 ^ 3 ^ 4",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)),
                ExpExpr(
                    IntLiteral(Token.int_literal(11, 12)),
                    IntLiteral(Token.int_literal(15, 16)),
                ),
            ),
        ),
        (
            # right argument is evaluated first
            # don't know what "a" is, so can't do constant folding
            "1 ^ 2 ^ a",
            False,
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)),
                LeftExpr(QualifiedID([Token.identifier(11, 12)])),
            ),
        ),
        (
            # "a" is on the left
            # the right can be folded
            "a ^ 1 ^ 2",
            False,
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
            FoldedExpr(
                ExpExpr(
                    IntLiteral(Token.int_literal(7, 8)),
                    IntLiteral(Token.int_literal(11, 12)),
                )
            ),
        ),
        (
            "1 ^ a ^ 2",
            False,
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                LeftExpr(QualifiedID([Token.identifier(7, 8)])),
                IntLiteral(Token.int_literal(11, 12)),
            ),
        ),
        (
            # only "4 ^ 5" can be folded
            "a ^ 1 ^ 2 ^ b ^ 3 ^ c ^ 4 ^ 5",
            False,
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)),
                ExpExpr(
                    IntLiteral(Token.int_literal(11, 12)),
                    ExpExpr(
                        LeftExpr(QualifiedID([Token.identifier(15, 16)])),
                        ExpExpr(
                            IntLiteral(Token.int_literal(19, 20)),
                            ExpExpr(
                                LeftExpr(QualifiedID([Token.identifier(23, 24)])),
                                FoldedExpr(
                                    ExpExpr(
                                        IntLiteral(Token.int_literal(27, 28)),
                                        IntLiteral(Token.int_literal(31, 32)),
                                    )
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ],
)
def test_parse_exp_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        exp_expr: Expr = ExpressionParser.parse_exp_expr(tkzr)
        if folded:
            assert isinstance(exp_expr, FoldedExpr)
            assert isinstance(exp_expr.wrapped_expr, ExpExpr)
            assert exp_expr.wrapped_expr.left == exp_left
            assert exp_expr.wrapped_expr.right == exp_right
        else:
            assert isinstance(exp_expr, ExpExpr)
            assert exp_expr.left == exp_left
            assert exp_expr.right == exp_right
        tkzr.advance_pos()
