import pytest
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.program import Program
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer


@pytest.mark.parametrize(
    "stmt_code,stmt_type", [("Option Explicit\n", OptionExplicit())]
)
def test_valid_global_stmt(stmt_code: str, stmt_type: GlobalStmt):
    with Tokenizer(stmt_code) as tkzr:
        prog = Program.from_tokenizer(tkzr)
        assert prog.global_stmt_list[0] == stmt_type
