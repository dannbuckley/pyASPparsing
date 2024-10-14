import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldedExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,folded,exp_term",
    [
        ("Not True", True, BoolLiteral(Token.identifier(7, 11))),
        (
            "Not 1 > 1",
            True,
            CompareExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(11, 12)),
                CompareExprType.COMPARE_GT,
            ),
        ),
    ],
)
def test_parse_not_expr(exp_code: str, folded: bool, exp_term: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        not_expr: Expr = ExpressionParser.parse_not_expr(tkzr)
        if folded:
            assert isinstance(not_expr, FoldedExpr)
            assert isinstance(not_expr.expr_to_fold, NotExpr)
            assert not_expr.expr_to_fold.term == exp_term
