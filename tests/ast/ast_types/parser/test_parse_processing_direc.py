import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.program import Program


def test_parse_processing_direc():
    with Tokenizer('<%@ Language="VBScript" %>', False) as tkzr:
        prog = Program.from_tokenizer(tkzr)
        assert isinstance(prog.global_stmt_list[0], ProcessingDirective)
        assert len(prog.global_stmt_list[0].settings) == 1
        match prog.global_stmt_list[0].settings[0]:
            case ProcessingSetting(kw, val):
                assert kw == Token.identifier(4, 12)
                assert val == Token.string_literal(13, 23)
            case _:
                pytest.fail(
                    "ProcessingDirective should have one instance of ProcessingSetting"
                )
