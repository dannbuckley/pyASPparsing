import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    "codeblock,exp_with_expr,exp_block_stmt_list",
    [
        (
            # empty with statement
            "With my_var\nEnd With\n",
            LeftExpr(QualifiedID([Token.identifier(7, 13)])),
            [],
        ),
        (
            # with statement, one assignment statement
            'With my_var\n.Name = "This is a name"\nEnd With\n',
            LeftExpr(QualifiedID([Token.identifier(7, 13)])),
            [
                AssignStmt(
                    LeftExpr(QualifiedID([Token.identifier(14, 19, dot_start=True)])),
                    EvalExpr("This is a name"),
                )
            ],
        ),
    ],
)
def test_parse_with_stmt(
    codeblock: str, exp_with_expr: Expr, exp_block_stmt_list: typing.List[BlockStmt]
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        with_stmt = Parser.parse_with_stmt(tkzr)
        tkzr.advance_pos()
        assert with_stmt.with_expr == exp_with_expr
        assert with_stmt.block_stmt_list == exp_block_stmt_list
