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
            "1 + 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 - 2",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            AddNegated(IntLiteral(Token.int_literal(7, 8))),
        ),
        (
            "1 + 2 - 3",
            True,
            AddExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            AddNegated(IntLiteral(Token.int_literal(11, 12))),
        ),
        (
            "1 + (2 - 3)",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            AddExpr(
                IntLiteral(Token.int_literal(8, 9)),
                AddNegated(IntLiteral(Token.int_literal(12, 13))),
            ),
        ),
        (
            "1 + 2 - 3 + 4",
            True,
            AddExpr(
                AddExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                AddNegated(IntLiteral(Token.int_literal(11, 12))),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "2 Mod 1 + 3",
            True,
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(9, 10)),
            ),
            IntLiteral(Token.int_literal(13, 14)),
        ),
        (
            "2 + 3 Mod 1",
            True,
            IntLiteral(Token.int_literal(3, 4)),
            ModExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(13, 14)),
            ),
        ),
        (
            "2 Mod 1 + 3 Mod 1",
            True,
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(9, 10)),
            ),
            ModExpr(
                IntLiteral(Token.int_literal(13, 14)),
                IntLiteral(Token.int_literal(19, 20)),
            ),
        ),
        (
            # no moves made, constants stay on left
            "1 + 2 + a",
            False,
            FoldableExpr(
                AddExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                )
            ),
            LeftExpr(QualifiedID([Token.identifier(11, 12)])),
        ),
        (
            # 'a' and '2' swap places
            "1 + a + 2",
            False,
            FoldableExpr(
                AddExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(11, 12)),
                )
            ),
            LeftExpr(QualifiedID([Token.identifier(7, 8)])),
        ),
        (
            # 'a' moved to end of expression
            "a + 1 + 2",
            False,
            FoldableExpr(
                AddExpr(
                    IntLiteral(Token.int_literal(7, 8)),
                    IntLiteral(Token.int_literal(11, 12)),
                )
            ),
            LeftExpr(QualifiedID([Token.identifier(3, 4)])),
        ),
    ],
)
def test_parse_add_expr(exp_code: str, folded: bool, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        add_expr: Expr = ExpressionParser.parse_add_expr(tkzr)
        if folded:
            assert isinstance(add_expr, FoldableExpr)
            assert isinstance(add_expr.wrapped_expr, AddExpr)
            assert add_expr.wrapped_expr.left == exp_left
            assert add_expr.wrapped_expr.right == exp_right
