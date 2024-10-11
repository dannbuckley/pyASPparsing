import pytest
from pyaspparsing import TokenizerError
from pyaspparsing.ast.tokenizer.token_types import Token, TokenType
from pyaspparsing.ast.tokenizer.state_machine import tokenize


@pytest.mark.parametrize(
    "codeblock,exp_type",
    [
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
        ("["),  # missing last ']'
        ("[Invalid Escape Identifier"),  # missing last ']'
        ('"This string does not have an end'),  # missing last '"'
        ("&H"),  # need at least one hex digit
        ("&HG"),  # invalid hex digit
        ("1."),  # need at least one digit after '.'
        ("1E"),  # need at least one digit after '.'
        ("#"),  # need at least one date character
        ("##"),  # need at least one date character
        ("#1970/01/01"),  # missing last '#'
        (".Rem"),  # cannot have '.' immediately before Rem comment
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


def test_quote_comment_wholeline():
    # should not return NEWLINE token after comment
    comment_iter = tokenize("' Whole-line comment\n\ta")
    tok = next(comment_iter, None)
    assert tok is not None and tok.token_type == TokenType.IDENTIFIER
    assert next(comment_iter, None) is None


def test_quote_comment_endofline():
    # should return NEWLINE token after comment
    comment_iter = tokenize("a ' Comment at end of line\n\tb")

    def _try_token(tok_type: TokenType):
        nonlocal comment_iter
        tok = next(comment_iter, None)
        assert tok is not None and tok.token_type == tok_type

    _try_token(TokenType.IDENTIFIER)
    _try_token(TokenType.NEWLINE)
    _try_token(TokenType.IDENTIFIER)
    assert next(comment_iter, None) is None


def test_rem_comment_wholeline():
    # should not return NEWLINE token after comment
    comment_iter = tokenize("Rem Whole-line comment\n\tb")
    tok = next(comment_iter, None)
    assert tok is not None and tok.token_type == TokenType.IDENTIFIER
    assert next(comment_iter, None) is None


def test_rem_comment_endofline():
    # should return NEWLINE token after comment
    comment_iter = tokenize("a Rem End-of-line comment\n\tb")

    def _try_token(tok_type: TokenType):
        nonlocal comment_iter
        tok = next(comment_iter, None)
        assert tok is not None and tok.token_type == tok_type

    _try_token(TokenType.IDENTIFIER)
    _try_token(TokenType.NEWLINE)
    _try_token(TokenType.IDENTIFIER)
    assert next(comment_iter, None) is None


def test_trailing_whitespace():
    tkzr = tokenize('"Hello, world!"   ')
    tok = next(tkzr, None)
    assert tok.token_type == TokenType.LITERAL_STRING
    tok = next(tkzr, None)
    assert tok is None


def test_line_continuation():
    for tok, etok in zip(
        # should ignore leading whitespace on second line
        tokenize('"Hello, " & _  \r\n  " world!"'),
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
