import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldedExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,folded,exp_sign,exp_term",
    [
        ("-1", True, Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
        ("+1", True, Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
        (
            "+-1",
            True,
            Token.symbol(3, 4),
            UnaryExpr(Token.symbol(4, 5), IntLiteral(Token.int_literal(5, 6))),
        ),
        (
            "-(1 ^ 2)",
            True,
            Token.symbol(3, 4),
            ExpExpr(
                IntLiteral(Token.int_literal(5, 6)),
                IntLiteral(Token.int_literal(9, 10)),
            ),
        ),
    ],
)
def test_parse_unary_expr(exp_code: str, folded: bool, exp_sign: Token, exp_term: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        unary_expr: Expr = ExpressionParser.parse_unary_expr(tkzr)
        if folded:
            assert isinstance(unary_expr, FoldedExpr)
            assert isinstance(unary_expr.wrapped_expr, UnaryExpr)
            assert unary_expr.wrapped_expr.sign == exp_sign
            assert unary_expr.wrapped_expr.term == exp_term
