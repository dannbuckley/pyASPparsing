import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *


def test_parse_option_explicit():
    with Tokenizer("<%Option Explicit%>", False) as tkzr:
        tkzr.advance_pos()
        OptionExplicit.from_tokenizer(tkzr)
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_redim_decl_list,exp_preserve",
    [
        (
            "ReDim my_array(10)",
            [
                RedimDecl(
                    ExtendedID(Token.identifier(8, 16)),
                    [IntLiteral(Token.int_literal(17, 19))],
                )
            ],
            False,
        ),
        (
            "ReDim my_array(10, 10)",
            [
                RedimDecl(
                    ExtendedID(Token.identifier(8, 16)),
                    [
                        IntLiteral(Token.int_literal(17, 19)),
                        IntLiteral(Token.int_literal(21, 23)),
                    ],
                )
            ],
            False,
        ),
        (
            "ReDim Preserve my_array(10, 10)",
            [
                RedimDecl(
                    ExtendedID(Token.identifier(17, 25)),
                    [
                        IntLiteral(Token.int_literal(26, 28)),
                        IntLiteral(Token.int_literal(30, 32)),
                    ],
                )
            ],
            True,
        ),
    ],
)
def test_parse_redim_stmt(
    codeblock: str, exp_redim_decl_list: typing.List[RedimDecl], exp_preserve: bool
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        redim_stmt = RedimStmt.from_tokenizer(tkzr)
        assert redim_stmt.redim_decl_list == exp_redim_decl_list
        assert redim_stmt.preserve == exp_preserve
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_target_expr,exp_assign_expr,exp_is_new",
    [
        (
            # LeftExpr = Expr
            "a = 1",
            LeftExpr(QualifiedID([Token.identifier(2, 3)])),
            IntLiteral(Token.int_literal(6, 7)),
            False,
        ),
        (
            # Set LeftExpr = Expr
            "Set a = 1",
            LeftExpr(QualifiedID([Token.identifier(6, 7)])),
            IntLiteral(Token.int_literal(10, 11)),
            False,
        ),
        (
            # Set LeftExpr = New LeftExpr
            "Set a = New b",
            LeftExpr(QualifiedID([Token.identifier(6, 7)])),
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            True,
        ),
        (
            # LeftExpr with omitted expr in index or params list
            "Set a(1,, 3) = 42",
            LeftExpr(
                QualifiedID([Token.identifier(6, 7)]),
                [
                    IndexOrParams(
                        [
                            IntLiteral(Token.int_literal(8, 9)),
                            None,
                            IntLiteral(Token.int_literal(12, 13)),
                        ]
                    )
                ],
            ),
            IntLiteral(Token.int_literal(17, 19)),
            False,
        ),
        (
            # LeftExpr with omitted expr in tail index or params list
            "Set a().b(1,, 3) = 42",
            LeftExpr(
                QualifiedID([Token.identifier(6, 7)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(9, 11, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(12, 13)),
                                    None,
                                    IntLiteral(Token.int_literal(16, 17)),
                                ]
                            )
                        ],
                    )
                ],
            ),
            IntLiteral(Token.int_literal(21, 23)),
            False,
        ),
    ],
)
def test_parse_assign_stmt(
    codeblock: str, exp_target_expr: Expr, exp_assign_expr: Expr, exp_is_new: bool
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        assign_stmt = AssignStmt.from_tokenizer(tkzr)
        assert assign_stmt.target_expr == exp_target_expr
        assert assign_stmt.assign_expr == exp_assign_expr
        assert assign_stmt.is_new == exp_is_new
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_left_expr",
    [
        (
            # call QualifiedID with a QualifiedIDTail
            "Call Hello.World()",
            LeftExpr(
                QualifiedID(
                    [Token.identifier(7, 13, dot_end=True), Token.identifier(13, 18)]
                ),
                [IndexOrParams()],
            ),
        ),
        (
            # no params
            "Call HelloWorld()",
            LeftExpr(QualifiedID([Token.identifier(7, 17)]), [IndexOrParams()]),
        ),
        (
            # one param
            "Call HelloWorld(1)",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [IndexOrParams([IntLiteral(Token.int_literal(18, 19))])],
            ),
        ),
        (
            # multiple IndexOrParam in LeftExpr
            "Call HelloWorld()()",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [IndexOrParams(), IndexOrParams()],
            ),
        ),
        (
            # param in later IndexOrParam for LeftExpr
            "Call HelloWorld()(1)",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [
                    IndexOrParams(),
                    IndexOrParams([IntLiteral(Token.int_literal(20, 21))]),
                ],
            ),
        ),
        (
            # LeftExprTail
            "Call HelloWorld().GoodMorning()",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(19, 31, dot_start=True)]),
                        [IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            # multiple IndexOrParam in LeftExprTail
            "Call HelloWorld().GoodMorning()()",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(19, 31, dot_start=True)]),
                        [IndexOrParams(), IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            # param in LeftExprTail
            "Call HelloWorld().GoodMorning(1)",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(19, 31, dot_start=True)]),
                        [IndexOrParams([IntLiteral(Token.int_literal(32, 33))])],
                    )
                ],
            ),
        ),
        (
            # multiple params in LeftExprTail
            "Call HelloWorld().GoodMorning(1, 2)",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(19, 31, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(32, 33)),
                                    IntLiteral(Token.int_literal(35, 36)),
                                ]
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            # param in later IndexOrParam for LeftExprTail
            "Call HelloWorld().GoodMorning()(1)",
            LeftExpr(
                QualifiedID([Token.identifier(7, 17)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(19, 31, dot_start=True)]),
                        [
                            IndexOrParams(),
                            IndexOrParams([IntLiteral(Token.int_literal(34, 35))]),
                        ],
                    )
                ],
            ),
        ),
    ],
)
def test_parse_call_stmt(codeblock: str, exp_left_expr: LeftExpr):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        call_stmt = CallStmt.from_tokenizer(tkzr)
        assert call_stmt.left_expr == exp_left_expr
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_resume_next,exp_goto_spec",
    [
        ("On Error Resume Next", True, None),
        ("On Error GoTo 0", False, Token.int_literal(16, 17)),
    ],
)
def test_parse_error_stmt(
    codeblock: str, exp_resume_next: bool, exp_goto_spec: typing.Optional[Token]
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        error_stmt = ErrorStmt.from_tokenizer(tkzr)
        assert error_stmt.resume_next == exp_resume_next
        assert error_stmt.goto_spec == exp_goto_spec
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_exit_token",
    [
        ("Exit Do", Token.identifier(7, 9)),
        ("Exit For", Token.identifier(7, 10)),
        ("Exit Function", Token.identifier(7, 15)),
        ("Exit Property", Token.identifier(7, 15)),
        ("Exit Sub", Token.identifier(7, 10)),
    ],
)
def test_parse_exit_stmt(codeblock: str, exp_exit_token: Token):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        exit_stmt = ExitStmt.from_tokenizer(tkzr)
        assert exit_stmt.exit_token == exp_exit_token
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_extended_id", [("Erase my_var", ExtendedID(Token.identifier(8, 14)))]
)
def test_parse_erase_stmt(codeblock: str, exp_extended_id: ExtendedID):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        erase_stmt = EraseStmt.from_tokenizer(tkzr)
        assert erase_stmt.extended_id == exp_extended_id
        tkzr.advance_pos()
