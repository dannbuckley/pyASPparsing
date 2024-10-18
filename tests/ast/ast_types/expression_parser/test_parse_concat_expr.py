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
            '"Hello, " & "world!"',
            True,
            ConstExpr(Token.string_literal(3, 12)),
            ConstExpr(Token.string_literal(15, 23)),
        ),
        (
            # 'a' is in the middle, can't fold
            '"Hello, " & a & "world!"',
            False,
            ConcatExpr(
                ConstExpr(Token.string_literal(3, 12)),
                LeftExpr(QualifiedID([Token.identifier(15, 16)])),
            ),
            ConstExpr(Token.string_literal(19, 27)),
        ),
        (
            # strings on right should be folded
            'a & "Hello, " & "world!"',
            False,
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
            FoldedExpr(
                ConcatExpr(
                    ConstExpr(Token.string_literal(7, 16)),
                    ConstExpr(Token.string_literal(19, 27)),
                )
            ),
        ),
        (
            # strings on left should be folded
            '"Hello, " & "world!" & a',
            False,
            FoldedExpr(
                ConcatExpr(
                    ConstExpr(Token.string_literal(3, 12)),
                    ConstExpr(Token.string_literal(15, 23)),
                )
            ),
            LeftExpr(QualifiedID([Token.identifier(26, 27)])),
        ),
        (
            # string between 'a' and 'b' should be folded
            'a & "Hello, " & "world!" & b',
            False,
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
            ConcatExpr(
                FoldedExpr(
                    ConcatExpr(
                        ConstExpr(Token.string_literal(7, 16)),
                        ConstExpr(Token.string_literal(19, 27)),
                    )
                ),
                LeftExpr(QualifiedID([Token.identifier(30, 31)])),
            ),
        ),
        (
            # strings between 'a' and 'b' should be folded
            '"What?" & a & "Hello, " & "world!" & b',
            False,
            ConcatExpr(
                ConstExpr(Token.string_literal(3, 10)),
                LeftExpr(QualifiedID([Token.identifier(13, 14)])),
            ),
            ConcatExpr(
                FoldedExpr(
                    ConcatExpr(
                        ConstExpr(Token.string_literal(17, 26)),
                        ConstExpr(Token.string_literal(29, 37)),
                    )
                ),
                LeftExpr(QualifiedID([Token.identifier(40, 41)])),
            ),
        ),
        (
            # strings between 'a' and 'b'
            'a & "Hello, " & "world!" & b & "What?"',
            False,
            ConcatExpr(
                LeftExpr(QualifiedID([Token.identifier(3, 4)])),
                ConcatExpr(
                    FoldedExpr(
                        ConcatExpr(
                            ConstExpr(Token.string_literal(7, 16)),
                            ConstExpr(Token.string_literal(19, 27)),
                        )
                    ),
                    LeftExpr(QualifiedID([Token.identifier(30, 31)])),
                ),
            ),
            ConstExpr(Token.string_literal(34, 41)),
        ),
    ],
)
def test_parse_concat_expr(
    exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        concat_expr: Expr = ExpressionParser.parse_concat_expr(tkzr)
        if folded:
            assert isinstance(concat_expr, FoldedExpr)
            assert isinstance(concat_expr.wrapped_expr, ConcatExpr)
            assert concat_expr.wrapped_expr.left == exp_left
            assert concat_expr.wrapped_expr.right == exp_right
