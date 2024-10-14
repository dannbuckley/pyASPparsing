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
            "6 Mod 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(9, 10)),
        ),
        (
            "6 Mod 4 Mod 2",
            True,
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(9, 10)),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "6 Mod (4 Mod 2)",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            ModExpr(
                IntLiteral(Token.int_literal(10, 11)),
                IntLiteral(Token.int_literal(16, 17)),
            ),
        ),
        (
            "8 Mod 6 Mod 4 Mod 2",
            True,
            ModExpr(
                ModExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(9, 10)),
                ),
                IntLiteral(Token.int_literal(15, 16)),
            ),
            IntLiteral(Token.int_literal(21, 22)),
        ),
        (
            "6 \\ 2 Mod 4",
            True,
            IntDivExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntLiteral(Token.int_literal(13, 14)),
        ),
        (
            "6 Mod 4 \\ 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            IntDivExpr(
                IntLiteral(Token.int_literal(9, 10)),
                IntLiteral(Token.int_literal(13, 14)),
            ),
        ),
        (
            "6 \\ 2 Mod 8 \\ 4",
            True,
            IntDivExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntDivExpr(
                IntLiteral(Token.int_literal(13, 14)),
                IntLiteral(Token.int_literal(17, 18)),
            ),
        ),
    ],
)
def test_parse_mod_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mod_expr: Expr = ExpressionParser.parse_mod_expr(tkzr)
        if folded:
            assert isinstance(mod_expr, FoldedExpr)
            assert isinstance(mod_expr.expr_to_fold, ModExpr)
            assert mod_expr.expr_to_fold.left == exp_left
            assert mod_expr.expr_to_fold.right == exp_right
