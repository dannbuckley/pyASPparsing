import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    "codeblock,exp_block_stmt_list,exp_loop_type,exp_loop_expr",
    [
        (
            # empty do loop
            "Do\nLoop\n",
            [],
            None,
            None,
        ),
        (
            # do loop
            "Do\nSet a = a + 1\nLoop\n",
            [
                AssignStmt(
                    LeftExpr(QualifiedID([Token.identifier(9, 10)])),
                    AddExpr(
                        IntLiteral(Token.int_literal(17, 18)),
                        LeftExpr(QualifiedID([Token.identifier(13, 14)])),
                    ),
                )
            ],
            None,
            None,
        ),
        (
            # empty do while loop - beginning
            "Do While True\nLoop\n",
            [],
            Token.identifier(5, 10),
            BoolLiteral(Token.identifier(11, 15)),
        ),
        (
            # empty do until loop - beginning
            "Do Until True\nLoop\n",
            [],
            Token.identifier(5, 10),
            BoolLiteral(Token.identifier(11, 15)),
        ),
        (
            # empty do while loop - end
            "Do\nLoop While True\n",
            [],
            Token.identifier(10, 15),
            BoolLiteral(Token.identifier(16, 20)),
        ),
        (
            # empty do until loop - end
            "Do\nLoop Until True\n",
            [],
            Token.identifier(10, 15),
            BoolLiteral(Token.identifier(16, 20)),
        ),
        (
            # empty while loop
            "While True\nWEnd\n",
            [],
            Token.identifier(2, 7),
            BoolLiteral(Token.identifier(8, 12)),
        ),
        (
            # while loop
            "While True\nSet a = a + 1\nWEnd\n",
            [
                AssignStmt(
                    LeftExpr(QualifiedID([Token.identifier(17, 18)])),
                    AddExpr(
                        IntLiteral(Token.int_literal(25, 26)),
                        LeftExpr(QualifiedID([Token.identifier(21, 22)])),
                    ),
                )
            ],
            Token.identifier(2, 7),
            BoolLiteral(Token.identifier(8, 12)),
        ),
    ],
)
def test_parse_loop_stmt(
    codeblock: str,
    exp_block_stmt_list: typing.List[BlockStmt],
    exp_loop_type: typing.Optional[Token],
    exp_loop_expr: typing.Optional[Expr],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        loop_stmt = Parser.parse_loop_stmt(tkzr)
        assert loop_stmt.block_stmt_list == exp_block_stmt_list
        assert loop_stmt.loop_type == exp_loop_type
        assert loop_stmt.loop_expr == exp_loop_expr
        tkzr.advance_pos()
