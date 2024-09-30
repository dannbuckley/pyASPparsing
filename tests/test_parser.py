from contextlib import ExitStack
import typing
import pytest
from pyaspparsing import ParserError
from pyaspparsing.parser import *


@pytest.mark.parametrize("stmt_code,stmt_type", [("Option Explicit\n", OptionExplicit)])
def test_valid_global_stmt(stmt_code: str, stmt_type: typing.Type):
    with Parser(stmt_code) as prsr:
        prog = prsr.parse()
        assert len(prog.global_stmt_list) == 1
        assert isinstance(prog.global_stmt_list[0], stmt_type)


@pytest.mark.parametrize(
    "stmt_code",
    [
        ("Option"),  # missing 'Explicit' <NEWLINE>
        ("Option Explicit"),  # missing <NEWLINE>
    ],
)
def test_invalid_global_stmt(stmt_code: str):
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ParserError))
        # parse code (don't suppress exception)
        prsr = stack.enter_context(Parser(stmt_code, False))
        prsr.parse()
