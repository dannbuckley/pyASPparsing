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
            EvalExpr(True),
            [],
            [],
        ),
        (
            # if statement (BlockStmtList), one block statement
            "If 1 = 1 Then\nDim my_var\nEnd If\n",
            EvalExpr(True),
            [VarDecl([VarName(ExtendedID("my_var"))])],
            [],
        ),
        (
            # if statement (BlockStmtList), empty elseif (BlockStmtList)
            "If 1 = 2 Then\nElseIf 1 = 1 Then\nEnd If\n",
            EvalExpr(False),
            [],
            [
                ElseStmt(
                    [],
                    elif_expr=EvalExpr(True),
                )
            ],
        ),
        (
            # if statement (BlockStmtList), elseif with block statement
            "If 1 = 2 Then\nElseIf 1 = 1 Then\nDim my_var\nEnd If\n",
            EvalExpr(False),
            [],
            [
                ElseStmt(
                    [VarDecl([VarName(ExtendedID("my_var"))])],
                    elif_expr=EvalExpr(True),
                )
            ],
        ),
        (
            # if statement (BlockStmtList), elseif with inline statement
            'If 1 = 2 Then\nElseIf 1 = 1 Then Response.Write("Hello, world!")\nEnd If\n',
            EvalExpr(False),
            [],
            [
                ElseStmt(
                    [
                        SubCallStmt(
                            LeftExpr("response").get_subname("write")(
                                EvalExpr("Hello, world!")
                            )
                        )
                    ],
                    elif_expr=EvalExpr(True),
                )
            ],
        ),
        (
            # if statement (BlockStmtList), empty else (BlockStmtList)
            "If 1 = 2 Then\nElse\nEnd If\n",
            EvalExpr(False),
            [],
            [ElseStmt(is_else=True)],
        ),
        (
            # if statement (BlockStmtList), else with block statement
            "If 1 = 2 Then\nElse\nDim my_var\nEnd If\n",
            EvalExpr(False),
            [],
            [
                ElseStmt(
                    [VarDecl([VarName(ExtendedID("my_var"))])],
                    is_else=True,
                )
            ],
        ),
        (
            # if statement (BlockStmtList), else with inline statement
            'If 1 = 2 Then\nElse Response.Write("Hello, world!")\nEnd If\n',
            EvalExpr(False),
            [],
            [
                ElseStmt(
                    [
                        SubCallStmt(
                            LeftExpr("response").get_subname("write")(
                                EvalExpr("Hello, world!")
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
            EvalExpr(True),
            [
                AssignStmt(
                    LeftExpr("a"),
                    EvalExpr(1),
                )
            ],
            [],
        ),
        (
            # if statement (InlineStmt), else
            "If 1 = 2 Then a = 1 Else a = 2\n",
            EvalExpr(False),
            [
                AssignStmt(
                    LeftExpr("a"),
                    EvalExpr(1),
                )
            ],
            [
                ElseStmt(
                    [
                        AssignStmt(
                            LeftExpr("a"),
                            EvalExpr(2),
                        )
                    ],
                    is_else=True,
                )
            ],
        ),
        (
            # if statement (InlineStmt), end if
            "If 1 = 1 Then a = 1 End If\n",
            EvalExpr(True),
            [
                AssignStmt(
                    LeftExpr("a"),
                    EvalExpr(1),
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
        tkzr.advance_pos()
        assert if_stmt.if_expr == exp_if_expr
        assert if_stmt.block_stmt_list == exp_block_stmt_list
        assert if_stmt.else_stmt_list == exp_else_stmt_list
