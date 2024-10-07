import pytest
from pyaspparsing import TokenizerError
from pyaspparsing.ast.tokenizer.token_types import Token, TokenType
from pyaspparsing.ast.tokenizer.state_machine import tokenize


@pytest.mark.parametrize(
    "codeblock,exp_type",
    [
        ("\n", TokenType.NEWLINE),
        ("(", TokenType.SYMBOL),
        (".", TokenType.SYMBOL),
        ("&", TokenType.SYMBOL),
        ("#1970/01/01#", TokenType.LITERAL_DATE),
        ('"This is a valid string"', TokenType.LITERAL_STRING),
        ('"This is also a ""valid"" string"', TokenType.LITERAL_STRING),
        ("&H7f", TokenType.LITERAL_HEX),
        ("&HAB", TokenType.LITERAL_HEX),
        ("&HFA&", TokenType.LITERAL_HEX),
        ("&123", TokenType.LITERAL_OCT),
        ("&777&", TokenType.LITERAL_OCT),
        ("1000", TokenType.LITERAL_INT),
        ("1000.0", TokenType.LITERAL_FLOAT),
        ("1000.01", TokenType.LITERAL_FLOAT),
        ("1E3", TokenType.LITERAL_FLOAT),
        ("1E10", TokenType.LITERAL_FLOAT),
        ("1.0E3", TokenType.LITERAL_FLOAT),
        ("1.0E+3", TokenType.LITERAL_FLOAT),
        (".01", TokenType.LITERAL_FLOAT),
        (".01E5", TokenType.LITERAL_FLOAT),
        ("Normal_Identifier1", TokenType.IDENTIFIER),
        ("NormalID", TokenType.IDENTIFIER),
        (".NormalID", TokenType.IDENTIFIER_DOTID),
        ("NormalID.", TokenType.IDENTIFIER_IDDOT),
        (".NormalID.", TokenType.IDENTIFIER_DOTIDDOT),
        ("[_$% :-) @]", TokenType.IDENTIFIER),
        ("[Escaped ID]", TokenType.IDENTIFIER),
        (".[Escaped ID]", TokenType.IDENTIFIER_DOTID),
        ("[Escaped ID].", TokenType.IDENTIFIER_IDDOT),
        (".[Escaped ID].", TokenType.IDENTIFIER_DOTIDDOT),
    ],
)
def test_tokenize(codeblock: str, exp_type: TokenType):
    tkzr = iter(tokenize(codeblock))
    tok = next(tkzr, None)
    assert tok is not None
    assert tok.token_type == exp_type


@pytest.mark.parametrize(
    "codeblock",
    [
        ("[Invalid Escape Identifier"),
        ('"This string does not have an end'),
        ("&H"),
        ("&HG"),
        ("1."),
        ("1E"),
        ("#"),
        ("#1970/01/01"),
        (".Rem"),
    ],
)
def test_tokenize_invalid(codeblock: str):
    with pytest.raises(TokenizerError):
        for _ in tokenize(codeblock):
            pass


def test_empty_code():
    empty_iter = iter(tokenize(""))
    assert next(empty_iter, None) is None


@pytest.mark.parametrize("comment_delim", [("'"), ("Rem")])
def test_comment(comment_delim: str):
    comment_iter = iter(tokenize(f"{comment_delim} This is a comment"))
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
    comment_iter = tokenize(f"{comment_delim} This is a terminated comment{newline}")
    # next(comment_iter)
    match next(comment_iter, None):
        case Token(x):
            assert x == TokenType.NEWLINE
        case None:
            pytest.fail("First token was None, should be a NEWLINE Token")


def test_line_continuation():
    for tok, etok in zip(
        tokenize('"Hello, " & _  \r\n" world!"'),
        [TokenType.LITERAL_STRING, TokenType.SYMBOL, TokenType.LITERAL_STRING],
    ):
        assert tok.token_type == etok


@pytest.mark.parametrize("delim", [("\r"), ("\n"), ("\r\n"), (":")])
def test_newline(delim: str):
    for tok, etok in zip(
        tokenize(f'"First line"{delim}"Second write"'),
        [TokenType.LITERAL_STRING, TokenType.NEWLINE, TokenType.LITERAL_STRING],
    ):
        assert tok.token_type == etok
