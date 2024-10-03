import pytest
from pyaspparsing import TokenizerError
from pyaspparsing.tokenizer import *


def test_empty_code():
    empty_code = Tokenizer("")
    empty_iter = iter(empty_code)
    # there should not be any tokens in an empty codeblock
    assert next(empty_iter, None) is None


@pytest.mark.parametrize("comment_delim", [("'"), ("Rem")])
def test_comment(comment_delim: str):
    comment_code = Tokenizer(f"{comment_delim} This is a comment")
    comment_iter = iter(comment_code)
    assert next(comment_iter, None) is None


@pytest.mark.parametrize(
    "comment_delim,newline",
    [
        ("'", ":"),
        ("'", "\r"),
        ("'", "\n"),
        ("'", "\r\n"),
        ("Rem", ":"),
        ("Rem", "\r"),
        ("Rem", "\n"),
        ("Rem", "\r\n"),
    ],
)
def test_comment_newline(comment_delim: str, newline: str):
    comment_code = Tokenizer(f"{comment_delim} This is a terminated comment{newline}")
    comment_iter = iter(comment_code)
    match next(comment_iter, None):
        case Token(x):
            assert x == TokenType.NEWLINE
        case None:
            pytest.fail("First token was None, should be a NEWLINE Token")


@pytest.mark.parametrize(
    "codeblock,exp_type",
    [
        ("Normal_Identifier1", TokenType.IDENTIFIER),  # normal identifier
        ("[_$% :-) @]", TokenType.IDENTIFIER),  # escaped identifier
        ('"This is a valid string"', TokenType.LITERAL_STRING),
        ('"This is also a ""valid"" string"', TokenType.LITERAL_STRING), # escaped quote
        (".", TokenType.SYMBOL),  # dot symbol
        ("&", TokenType.SYMBOL),  # concatenation operator
        ("(", TokenType.SYMBOL), # should be returned at the very end of __next__()
        ("&H7f", TokenType.LITERAL_HEX),  # lowercase hex
        ("&HAB", TokenType.LITERAL_HEX),  # uppercase hex
        ("&HFA&", TokenType.LITERAL_HEX), # hex with optional ending '&'
        ("&123", TokenType.LITERAL_OCT),
        ("&777&", TokenType.LITERAL_OCT), # oct with optional ending '&'
        ("1000", TokenType.LITERAL_INT),
        ("1000.0", TokenType.LITERAL_FLOAT),  # only decimal point
        ("1000.01", TokenType.LITERAL_FLOAT),  # only decimal point
        ("1E3", TokenType.LITERAL_FLOAT),  # only scientific notation
        ("1E10", TokenType.LITERAL_FLOAT),  # only scientific notation
        ("1.0E3", TokenType.LITERAL_FLOAT),  # both decimal and scientific notation
        ("1.0E+3", TokenType.LITERAL_FLOAT),  # scientific notation with +/-
        (".01", TokenType.LITERAL_FLOAT),  # no leading digits
        (".01E5", TokenType.LITERAL_FLOAT),  # no leading digits w/ scientific notation
        ("#1970/01/01#", TokenType.LITERAL_DATE),
        ("And.", TokenType.IDENTIFIER_IDDOT),
        (".And", TokenType.IDENTIFIER_DOTID),
        (".And.", TokenType.IDENTIFIER_DOTIDDOT),
        ("[ID Dot].", TokenType.IDENTIFIER_IDDOT),
        (".[Dot ID]", TokenType.IDENTIFIER_DOTID),
        (".[Dot ID Dot].", TokenType.IDENTIFIER_DOTIDDOT),
    ],
)
def test_valid_token(codeblock: str, exp_type: TokenType):
    valid_code = Tokenizer(codeblock)
    valid_iter = iter(valid_code)
    match next(valid_iter, None):
        case Token(x, y):
            assert x == exp_type
            assert valid_code.codeblock[y] == codeblock
        case None:
            pytest.fail("First token was None, should be a Token instance")


@pytest.mark.parametrize(
    "codeblock",
    [
        ("[Invalid Escaped Identifier"),  # missing final ']'
        ('"This string does not have an end'),  # missing final '"'
        ("&H"),  # needs at least one hexadecimal digit
        ("&HG"),  # invalid hexadecimal digit
        ("1."),  # need at least one digit after '.'
        ("1E"),  # need at least one digit after 'E'
        ("#"),  # need at least one printable character
        ("#1970/01/01"),  # need ending '#'
        (".Rem"),  # '.' cannot appear right before a comment
    ],
)
def test_invalid_token(codeblock: str):
    with pytest.raises(TokenizerError):
        invalid_code = Tokenizer(codeblock)
        for _ in invalid_code:
            pass


def test_line_continuation():
    codeblock = '"Hello, " &  _  \r\n" world!"'
    test_code = Tokenizer(codeblock)
    exp_tok = [
        TokenType.LITERAL_STRING,
        TokenType.SYMBOL,
        TokenType.LITERAL_STRING,
    ]
    for tok, etok in zip(test_code, exp_tok):
        assert tok.token_type == etok


@pytest.mark.parametrize("delim", [("\r"), ("\n"), ("\r\n"), (":")])
def test_newline(delim: str):
    codeblock = f'"First line"{delim}"Second write"'
    test_code = Tokenizer(codeblock)
    exp_tok = [
        TokenType.LITERAL_STRING,
        TokenType.NEWLINE,
        TokenType.LITERAL_STRING,
    ]
    for tok, etok in zip(test_code, exp_tok):
        assert tok.token_type == etok
