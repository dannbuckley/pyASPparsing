import pytest
from pyaspparsing import TokenizerError
from pyaspparsing.ast.tokenizer.token_types import Token, TokenType
from pyaspparsing.ast.tokenizer.state_machine import tokenize


@pytest.mark.parametrize(
    "codeblock,delim_type",
    [
        ("<%", TokenType.DELIM_START_SCRIPT),
        ("<%=", TokenType.DELIM_START_OUTPUT),
        # need at least one whitespace character after '@'
        ("<%@ ", TokenType.DELIM_START_PROCESSING),
    ],
)
def test_start_delimiter(codeblock: str, delim_type: TokenType):
    tkzr = iter(tokenize(codeblock))
    tok = next(tkzr, None)
    assert tok is not None and tok.token_type == delim_type
    assert next(tkzr, None) is None


@pytest.mark.parametrize(
    "codeblock,delim_type",
    [
        ("<% %>", TokenType.DELIM_START_SCRIPT),
        ("<%= %>", TokenType.DELIM_START_OUTPUT),
        # need at least one whitespace character after '@'
        ("<%@ %>", TokenType.DELIM_START_PROCESSING),
    ],
)
def test_start_and_end_delimiter(codeblock: str, delim_type: TokenType):
    for tok, etok in zip(tokenize(codeblock), [delim_type, TokenType.DELIM_END]):
        assert tok.token_type == etok


def test_empty_html_comment():
    for tok, etok in zip(
        tokenize("<!---->"), [TokenType.HTML_START_COMMENT, TokenType.HTML_END_COMMENT]
    ):
        assert tok.token_type == etok


def test_regular_html_comment():
    for tok, etok in zip(
        tokenize("<!-- This is a regular HTML comment -->"),
        [TokenType.HTML_START_COMMENT, TokenType.HTML_END_COMMENT],
    ):
        assert tok.token_type == etok


@pytest.mark.parametrize(
    "doctype",
    [
        ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">'),
        ("<!doctype html>"),
    ],
)
def test_html_doctype(doctype: str):
    tkzr = iter(tokenize(doctype))
    tok = next(tkzr, None)
    assert tok is not None and tok.token_type == TokenType.FILE_TEXT
    assert next(tkzr, None) is None


@pytest.mark.parametrize(
    "codeblock",
    [
        ('<!-- #include virtual ="/myapp/footer.inc" -->'),
        ('<!-- #include file ="headers\\header1.inc" -->'),
    ],
)
def test_include_directive(codeblock: str):
    for tok, etok in zip(
        tokenize(codeblock),
        [
            TokenType.HTML_START_COMMENT,
            TokenType.INCLUDE_KW,
            TokenType.INCLUDE_TYPE,
            TokenType.SYMBOL,
            TokenType.INCLUDE_PATH,
            TokenType.HTML_END_COMMENT,
        ],
    ):
        assert tok.token_type == etok


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
    for tok, etok in zip(
        tokenize(f"<%{codeblock}%>"),
        [TokenType.DELIM_START_SCRIPT, exp_type, TokenType.DELIM_END],
    ):
        assert tok.token_type == etok


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
        for _ in tokenize(f"<%{codeblock}%>"):
            pass


def test_empty_code():
    empty_iter = iter(tokenize(""))
    assert next(empty_iter, None) is None


@pytest.mark.parametrize("comment_delim", [("'"), ("Rem")])
def test_comment(comment_delim: str):
    # should continue comment after first '%'
    for tok, etok in zip(
        tokenize(f"<%{comment_delim} This is a % comment%>"),
        [TokenType.DELIM_START_SCRIPT, TokenType.DELIM_END],
    ):
        assert tok.token_type, etok


def test_quote_comment_wholeline():
    # should not return NEWLINE token after comment
    for tok, etok in zip(
        tokenize("<%' Whole-line comment\n\ta%>"),
        [TokenType.DELIM_START_SCRIPT, TokenType.IDENTIFIER, TokenType.DELIM_END],
    ):
        assert tok.token_type == etok


def test_quote_comment_endofline():
    # should return NEWLINE token after comment
    for tok, etok in zip(
        tokenize("<%a ' Comment at end of line\n\tb%>"),
        [
            TokenType.DELIM_START_SCRIPT,
            TokenType.IDENTIFIER,
            TokenType.NEWLINE,
            TokenType.IDENTIFIER,
            TokenType.DELIM_END,
        ],
    ):
        assert tok.token_type == etok


def test_rem_comment_wholeline():
    # should not return NEWLINE token after comment
    for tok, etok in zip(
        tokenize("<%Rem Whole-line comment\n\tb%>"),
        [TokenType.DELIM_START_SCRIPT, TokenType.IDENTIFIER, TokenType.DELIM_END],
    ):
        assert tok.token_type == etok


def test_rem_comment_endofline():
    # should return NEWLINE token after comment
    for tok, etok in zip(
        tokenize("<%a Rem End-of-line comment\n\tb%>"),
        [
            TokenType.DELIM_START_SCRIPT,
            TokenType.IDENTIFIER,
            TokenType.NEWLINE,
            TokenType.IDENTIFIER,
            TokenType.DELIM_END,
        ],
    ):
        assert tok.token_type == etok


def test_trailing_whitespace():
    for tok, etok in zip(
        tokenize('<%"Hello, world!"   %>'),
        [TokenType.DELIM_START_SCRIPT, TokenType.LITERAL_STRING, TokenType.DELIM_END],
    ):
        assert tok.token_type == etok


def test_line_continuation():
    # should ignore leading whitespace on second line
    for tok, etok in zip(
        tokenize('<%"Hello, " & _  \r\n  " world!"%>'),
        [
            TokenType.DELIM_START_SCRIPT,
            TokenType.LITERAL_STRING,
            TokenType.SYMBOL,
            TokenType.LITERAL_STRING,
            TokenType.DELIM_END,
        ],
    ):
        assert tok.token_type == etok


@pytest.mark.parametrize("delim", [("\r"), ("\n"), ("\r\n"), (":")])
def test_newline(delim: str):
    for tok, etok in zip(
        tokenize(f'<%"First line"{delim}"Second write"%>'),
        [
            TokenType.DELIM_START_SCRIPT,
            TokenType.LITERAL_STRING,
            TokenType.NEWLINE,
            TokenType.LITERAL_STRING,
            TokenType.DELIM_END,
        ],
    ):
        assert tok.token_type == etok
