import pytest
from pyaspparsing.ast.tokenizer.token_types import TokenType
from pyaspparsing.ast.tokenizer.state_machine import tokenize


def test_tokenize():
    tkzr = iter(tokenize("\n"))
    tok = next(tkzr, None)
    assert tok is not None
    assert tok.token_type == TokenType.NEWLINE
