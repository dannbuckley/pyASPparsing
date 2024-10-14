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
        )
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
            assert isinstance(concat_expr.expr_to_fold, ConcatExpr)
            assert concat_expr.expr_to_fold.left == exp_left
            assert concat_expr.expr_to_fold.right == exp_right
