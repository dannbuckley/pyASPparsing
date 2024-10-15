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
        )
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
