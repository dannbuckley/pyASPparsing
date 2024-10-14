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
            "1 + 2",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 - 2",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 + 2 - 3",
            True,
            Token.symbol(9, 10),
            AddExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
                Token.symbol(5, 6),
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "1 + (2 - 3)",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            AddExpr(
                IntLiteral(Token.int_literal(8, 9)),
                IntLiteral(Token.int_literal(12, 13)),
                Token.symbol(10, 11),
            ),
        ),
        (
            "1 + 2 - 3 + 4",
            True,
            Token.symbol(13, 14),
            AddExpr(
                AddExpr(
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
            "2 Mod 1 + 3",
            True,
            Token.symbol(11, 12),
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(9, 10)),
            ),
            IntLiteral(Token.int_literal(13, 14)),
        ),
        (
            "2 + 3 Mod 1",
            True,
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            ModExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(13, 14)),
            ),
        ),
        (
            "2 Mod 1 + 3 Mod 1",
            True,
            Token.symbol(11, 12),
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(9, 10)),
            ),
            ModExpr(
                IntLiteral(Token.int_literal(13, 14)),
                IntLiteral(Token.int_literal(19, 20)),
            ),
        ),
    ],
)
def test_parse_add_expr(
    exp_code: str, folded: bool, exp_op: Token, exp_left: Expr, exp_right: Expr
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        add_expr: Expr = ExpressionParser.parse_add_expr(tkzr)
        if folded:
            assert isinstance(add_expr, FoldedExpr)
            assert isinstance(add_expr.expr_to_fold, AddExpr)
            assert add_expr.expr_to_fold.op == exp_op
            assert add_expr.expr_to_fold.left == exp_left
            assert add_expr.expr_to_fold.right == exp_right
