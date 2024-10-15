import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    "codeblock,exp_if_expr,exp_block_stmt_list,exp_else_stmt_list",
    [
        (
            # if statement (BlockStmtList), empty block list
            "If 1 = 1 Then\nEnd If\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [],
            [],
        ),
        (
            # if statement (BlockStmtList), one block statement
            "If 1 = 1 Then\nDim my_var\nEnd If\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [VarDecl([VarName(ExtendedID(Token.identifier(20, 26)))])],
            [],
        ),
        (
            # if statement (BlockStmtList), empty elseif (BlockStmtList)
            "If 1 = 2 Then\nElseIf 1 = 1 Then\nEnd If\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [],
            [
                ElseStmt(
                    [],
                    elif_expr=FoldedExpr(
                        CompareExpr(
                            IntLiteral(Token.int_literal(23, 24)),
                            IntLiteral(Token.int_literal(27, 28)),
                            CompareExprType.COMPARE_EQ,
                        )
                    ),
                )
            ],
        ),
        (
            # if statement (BlockStmtList), elseif with block statement
            "If 1 = 2 Then\nElseIf 1 = 1 Then\nDim my_var\nEnd If\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [],
            [
                ElseStmt(
                    [VarDecl([VarName(ExtendedID(Token.identifier(38, 44)))])],
                    elif_expr=FoldedExpr(
                        CompareExpr(
                            IntLiteral(Token.int_literal(23, 24)),
                            IntLiteral(Token.int_literal(27, 28)),
                            CompareExprType.COMPARE_EQ,
                        )
                    ),
                )
            ],
        ),
        (
            # if statement (BlockStmtList), elseif with inline statement
            'If 1 = 2 Then\nElseIf 1 = 1 Then Response.Write("Hello, world!")\nEnd If\n',
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [],
            [
                ElseStmt(
                    [
                        SubCallStmt(
                            LeftExpr(
                                QualifiedID(
                                    [
                                        Token.identifier(34, 43, dot_end=True),
                                        Token.identifier(43, 48),
                                    ]
                                ),
                                [
                                    IndexOrParams(
                                        [ConstExpr(Token.string_literal(49, 64))]
                                    )
                                ],
                            )
                        )
                    ],
                    elif_expr=FoldedExpr(
                        CompareExpr(
                            IntLiteral(Token.int_literal(23, 24)),
                            IntLiteral(Token.int_literal(27, 28)),
                            CompareExprType.COMPARE_EQ,
                        )
                    ),
                )
            ],
        ),
        (
            # if statement (BlockStmtList), empty else (BlockStmtList)
            "If 1 = 2 Then\nElse\nEnd If\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [],
            [ElseStmt(is_else=True)],
        ),
        (
            # if statement (BlockStmtList), else with block statement
            "If 1 = 2 Then\nElse\nDim my_var\nEnd If\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [],
            [
                ElseStmt(
                    [VarDecl([VarName(ExtendedID(Token.identifier(25, 31)))])],
                    is_else=True,
                )
            ],
        ),
        (
            # if statement (BlockStmtList), else with inline statement
            'If 1 = 2 Then\nElse Response.Write("Hello, world!")\nEnd If\n',
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [],
            [
                ElseStmt(
                    [
                        SubCallStmt(
                            LeftExpr(
                                QualifiedID(
                                    [
                                        Token.identifier(21, 30, dot_end=True),
                                        Token.identifier(30, 35),
                                    ]
                                ),
                                [
                                    IndexOrParams(
                                        [ConstExpr(Token.string_literal(36, 51))]
                                    )
                                ],
                            )
                        )
                    ],
                    is_else=True,
                )
            ],
        ),
        (
            # if statement (InlineStmt), empty until newline
            "If 1 = 1 Then a = 1\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [
                AssignStmt(
                    LeftExpr(QualifiedID([Token.identifier(16, 17)])),
                    IntLiteral(Token.int_literal(20, 21)),
                )
            ],
            [],
        ),
        (
            # if statement (InlineStmt), else
            "If 1 = 2 Then a = 1 Else a = 2\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [
                AssignStmt(
                    LeftExpr(QualifiedID([Token.identifier(16, 17)])),
                    IntLiteral(Token.int_literal(20, 21)),
                )
            ],
            [
                ElseStmt(
                    [
                        AssignStmt(
                            LeftExpr(QualifiedID([Token.identifier(27, 28)])),
                            IntLiteral(Token.int_literal(31, 32)),
                        )
                    ],
                    is_else=True,
                )
            ],
        ),
        (
            # if statement (InlineStmt), end if
            "If 1 = 1 Then a = 1 End If\n",
            FoldedExpr(
                CompareExpr(
                    IntLiteral(Token.int_literal(5, 6)),
                    IntLiteral(Token.int_literal(9, 10)),
                    CompareExprType.COMPARE_EQ,
                )
            ),
            [
                AssignStmt(
                    LeftExpr(QualifiedID([Token.identifier(16, 17)])),
                    IntLiteral(Token.int_literal(20, 21)),
                )
            ],
            [],
        ),
    ],
)
def test_parse_if_stmt(
    codeblock: str,
    exp_if_expr: Expr,
    exp_block_stmt_list: typing.List[BlockStmt],
    exp_else_stmt_list: typing.List[ElseStmt],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        if_stmt = Parser.parse_if_stmt(tkzr)
        assert if_stmt.if_expr == exp_if_expr
        assert if_stmt.block_stmt_list == exp_block_stmt_list
        assert if_stmt.else_stmt_list == exp_else_stmt_list
        tkzr.advance_pos()


def test_nested_inline_if_stmt():
    # TODO: test this case, currently broken
    # affected code: iterative calls to parse_block_stmt() in the first while loop of parse_if_stmt()
    codeblock = (
        """<% if True then %><% if True then %>content<% end if %><% end if %>"""
    )
