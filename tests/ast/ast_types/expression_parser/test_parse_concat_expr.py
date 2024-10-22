import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldableExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            # 'a' is in the middle, can't fold
            '"Hello, " & a & "world!"',
            ConcatExpr(
                EvalExpr("Hello, "),
                LeftExpr(QualifiedID([Token.identifier(15, 16)])),
            ),
            EvalExpr("world!"),
        ),
        (
            # strings on right should be folded
            'a & "Hello, " & "world!"',
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
            EvalExpr("Hello, world!"),
        ),
        (
            # strings on left should be folded
            '"Hello, " & "world!" & a',
            EvalExpr("Hello, world!"),
            LeftExpr(QualifiedID([Token.identifier(26, 27)])),
        ),
        (
            # string between 'a' and 'b' should be folded
            'a & "Hello, " & "world!" & b',
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
            ConcatExpr(
                EvalExpr("Hello, world!"),
                LeftExpr(QualifiedID([Token.identifier(30, 31)])),
            ),
        ),
        (
            # strings between 'a' and 'b' should be folded
            '"What?" & a & "Hello, " & "world!" & b',
            ConcatExpr(
                EvalExpr("What?"),
                LeftExpr(QualifiedID([Token.identifier(13, 14)])),
            ),
            ConcatExpr(
                EvalExpr("Hello, world!"),
                LeftExpr(QualifiedID([Token.identifier(40, 41)])),
            ),
        ),
        (
            # strings between 'a' and 'b'
            'a & "Hello, " & "world!" & b & "What?"',
            ConcatExpr(
                LeftExpr(QualifiedID([Token.identifier(3, 4)])),
                ConcatExpr(
                    EvalExpr("Hello, world!"),
                    LeftExpr(QualifiedID([Token.identifier(30, 31)])),
                ),
            ),
            EvalExpr("What?"),
        ),
    ],
)
def test_parse_concat_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        concat_expr: Expr = ExpressionParser.parse_concat_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(concat_expr, ConcatExpr)
        assert concat_expr.left == exp_left
        assert concat_expr.right == exp_right
