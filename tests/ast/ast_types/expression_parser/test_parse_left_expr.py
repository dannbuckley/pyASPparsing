import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldedExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("a", LeftExpr(QualifiedID([Token.identifier(3, 4)]))),
        (
            "a(1,, 3)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 4)]),
                [
                    IndexOrParams(
                        [
                            IntLiteral(Token.int_literal(5, 6)),
                            None,
                            IntLiteral(Token.int_literal(9, 10)),
                        ]
                    )
                ],
            ),
        ),
        (
            "a().b(1,, 3)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 4)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(6, 8, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(9, 10)),
                                    None,
                                    IntLiteral(Token.int_literal(13, 14)),
                                ]
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            "Hello.World()",
            LeftExpr(
                QualifiedID(
                    [Token.identifier(3, 9, dot_end=True), Token.identifier(9, 14)]
                ),
                [IndexOrParams()],
            ),
        ),
        (
            "HelloWorld()",
            LeftExpr(QualifiedID([Token.identifier(3, 13)]), [IndexOrParams()]),
        ),
        (
            "HelloWorld(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams([IntLiteral(Token.int_literal(14, 15))])],
            ),
        ),
        (
            "HelloWorld((1))",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams([IntLiteral(Token.int_literal(15, 16))])],
            ),
        ),
        (
            "HelloWorld(a)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams([LeftExpr(QualifiedID([Token.identifier(14, 15)]))])],
            ),
        ),
        (
            "HelloWorld()()",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(), IndexOrParams()],
            ),
        ),
        (
            "HelloWorld()(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [
                    IndexOrParams(),
                    IndexOrParams([IntLiteral(Token.int_literal(16, 17))]),
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()()",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [IndexOrParams(), IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [IndexOrParams([IntLiteral(Token.int_literal(28, 29))])],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning(1, 2)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(28, 29)),
                                    IntLiteral(Token.int_literal(31, 32)),
                                ]
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [
                            IndexOrParams(),
                            IndexOrParams([IntLiteral(Token.int_literal(30, 31))]),
                        ],
                    )
                ],
            ),
        ),
    ],
)
def test_parse_left_expr(expr_code: str, expr_val: Expr):
    with Tokenizer(f"<%={expr_code}%>", False) as tkzr:
        tkzr.advance_pos()
        left_expr: Expr = ExpressionParser.parse_left_expr(tkzr)
        assert left_expr == expr_val
