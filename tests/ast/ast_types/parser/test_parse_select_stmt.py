import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    "codeblock,exp_select_case_expr,exp_case_stmt_list",
    [
        (
            # select statement, empty case list
            "Select Case a\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [],
        ),
        (
            # select statement, one empty case without newline
            "Select Case a\nCase 1 End Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [CaseStmt(case_expr_list=[EvalExpr(1)])],
        ),
        (
            # select statement, one empty case with newline
            "Select Case a\nCase 1\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [CaseStmt(case_expr_list=[EvalExpr(1)])],
        ),
        (
            # select statement, one case without newline
            "Select Case a\nCase 1 Dim my_var\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [
                CaseStmt(
                    [VarDecl([VarName(ExtendedID(Token.identifier(27, 33)))])],
                    [EvalExpr(1)],
                )
            ],
        ),
        (
            # select statement, one case without newline
            "Select Case a\nCase 1 Dim my_var\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [
                CaseStmt(
                    [VarDecl([VarName(ExtendedID(Token.identifier(27, 33)))])],
                    [EvalExpr(1)],
                )
            ],
        ),
        (
            # select statement, one case without newline
            "Select Case a\nCase 1\nDim my_var\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [
                CaseStmt(
                    [VarDecl([VarName(ExtendedID(Token.identifier(27, 33)))])],
                    [EvalExpr(1)],
                )
            ],
        ),
        (
            # select statement, empty case else without newline
            "Select Case a\nCase Else End Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [CaseStmt(is_else=True)],
        ),
        (
            # select statement, empty case else with newline
            "Select Case a\nCase Else\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [CaseStmt(is_else=True)],
        ),
        (
            # select statement, one empty case and empty case else
            "Select Case a\nCase 1 Case Else End Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [
                CaseStmt(case_expr_list=[EvalExpr(1)]),
                CaseStmt(is_else=True),
            ],
        ),
        (
            # select statement, case else without newline
            "Select Case a\nCase Else Dim my_var\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [
                CaseStmt(
                    [VarDecl([VarName(ExtendedID(Token.identifier(30, 36)))])],
                    is_else=True,
                )
            ],
        ),
        (
            # select statement, case else with newline
            "Select Case a\nCase Else\nDim my_var\nEnd Select\n",
            LeftExpr(QualifiedID([Token.identifier(14, 15)])),
            [
                CaseStmt(
                    [VarDecl([VarName(ExtendedID(Token.identifier(30, 36)))])],
                    is_else=True,
                )
            ],
        ),
    ],
)
def test_parse_select_stmt(
    codeblock: str,
    exp_select_case_expr: Expr,
    exp_case_stmt_list: typing.List[CaseStmt],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        select_stmt = Parser.parse_select_stmt(tkzr)
        tkzr.advance_pos()
        assert select_stmt.select_case_expr == exp_select_case_expr
        assert select_stmt.case_stmt_list == exp_case_stmt_list
