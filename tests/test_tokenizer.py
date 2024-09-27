import pytest
from pyaspparsing import TokenizerError
from pyaspparsing.tokenizer import *


def test_empty_code():
    empty_code = Tokenizer("")
    empty_iter = iter(empty_code.process())
    # there should not be any tokens in an empty codeblock
    assert next(empty_iter, None) is None


@pytest.mark.parametrize(
    "codeblock,exp_type",
    [
        ('"This is a valid string"', TokenType.LITERAL_STRING),
        ("&H7f", TokenType.LITERAL_HEX),  # lowercase hex
        ("&HAB", TokenType.LITERAL_HEX),  # uppercase hex
        ("&123", TokenType.LITERAL_OCT),
        ("1000", TokenType.LITERAL_INT),
        ("1000.0", TokenType.LITERAL_FLOAT),  # only decimal point
        ("1E3", TokenType.LITERAL_FLOAT),  # only scientific notation
        ("1.0E3", TokenType.LITERAL_FLOAT),  # both decimal and scientific notation
        ("1.0E+3", TokenType.LITERAL_FLOAT),  # scientific notation with +/-
    ],
)
def test_valid_literal(codeblock: str, exp_type: TokenType):
    valid_code = Tokenizer(codeblock)
    valid_iter = iter(valid_code.process())
    match next(valid_iter, None):
        case Token(x, y):
            assert x == exp_type
            assert valid_code.codeblock[y] == codeblock
        case None:
            pytest.fail("First token was None, should be a Token instance")


@pytest.mark.parametrize(
    "codeblock",
    [
        ('"This string does not have an end'),  # missing final '"'
        ("&H"),  # needs at least one hexadecimal digit
        ("&HG"),  # invalid hexadecimal digit
        ("&"),  # needs at least one octal digit
        ("&8"),  # invalid octal digit
        ("1."), # need at least one digit after '.'
        ("1E"), # need at least one digit after 'E'
    ],
)
def test_invalid_literal(codeblock: str):
    with pytest.raises(TokenizerError):
        invalid_code = Tokenizer(codeblock)
        for _ in invalid_code.process():
            pass
