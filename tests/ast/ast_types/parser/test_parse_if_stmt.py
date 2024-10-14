import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.program import Program


def test_parse_if_stmt():
    pass


def test_nested_inline_if_stmt():
    # TODO: test this case, currently broken
    # affected code: iterative calls to parse_block_stmt() in the first while loop of parse_if_stmt()
    codeblock = (
        """<% if True then %><% if True then %>content<% end if %><% end if %>"""
    )
