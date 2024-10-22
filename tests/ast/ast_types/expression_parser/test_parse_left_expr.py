import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldableExpr
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
                            EvalExpr(1),
                            None,
                            EvalExpr(3),
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
                                    EvalExpr(1),
                                    None,
                                    EvalExpr(3),
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
                [IndexOrParams([EvalExpr(1)])],
            ),
        ),
        (
            "HelloWorld((1))",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams([EvalExpr(1)])],
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
                    IndexOrParams([EvalExpr(1)]),
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
                        [IndexOrParams([EvalExpr(1)])],
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
                                    EvalExpr(1),
                                    EvalExpr(2),
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
                            IndexOrParams([EvalExpr(1)]),
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
