import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    [
        "codeblock",
        "exp_target_id",
        "exp_block_stmt_list",
        "exp_eq_expr",
        "exp_to_expr",
        "exp_step_expr",
        "exp_each_in_expr",
    ],
    [
        (
            # empty '=' 'To' type for loop without step
            "For target = 0 To 5\nNext\n",
            ExtendedID("target"),
            [],
            EvalExpr(0),
            EvalExpr(5),
            None,
            None,
        ),
        (
            # empty '=' 'To' type for loop with step
            "For target = 0 To 5 Step 2\nNext\n",
            ExtendedID("target"),
            [],
            EvalExpr(0),
            EvalExpr(5),
            EvalExpr(2),
            None,
        ),
        (
            # empty 'Each' 'In' type for loop
            "For Each target In array\nNext\n",
            ExtendedID("target"),
            [],
            None,
            None,
            None,
            LeftExpr("array"),
        ),
        (
            # '=' 'To' for loop
            "For target = 0 To 5\nSet a = target\nNext\n",
            ExtendedID("target"),
            [
                AssignStmt(
                    LeftExpr("a"),
                    LeftExpr("target"),
                )
            ],
            EvalExpr(0),
            EvalExpr(5),
            None,
            None,
        ),
    ],
)
def test_parse_for_stmt(
    codeblock: str,
    exp_target_id: ExtendedID,
    exp_block_stmt_list: typing.List[BlockStmt],
    exp_eq_expr: typing.Optional[Expr],
    exp_to_expr: typing.Optional[Expr],
    exp_step_expr: typing.Optional[Expr],
    exp_each_in_expr: typing.Optional[Expr],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        for_stmt = Parser.parse_for_stmt(tkzr)
        tkzr.advance_pos()
        assert for_stmt.target_id == exp_target_id
        assert for_stmt.block_stmt_list == exp_block_stmt_list
        assert for_stmt.eq_expr == exp_eq_expr
        assert for_stmt.to_expr == exp_to_expr
        assert for_stmt.step_expr == exp_step_expr
        assert for_stmt.each_in_expr == exp_each_in_expr
