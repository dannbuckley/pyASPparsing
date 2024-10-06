import pytest
from pyaspparsing.ast.tokenizer.token_types import TokenType
from pyaspparsing.ast.tokenizer.state_machine import tokenize


@pytest.mark.parametrize(
    "codeblock,exp_type",
    [
        ("\n", TokenType.NEWLINE),
        ("(", TokenType.SYMBOL),
        (".", TokenType.SYMBOL),
        ("NormalID", TokenType.IDENTIFIER),
        (".NormalID", TokenType.IDENTIFIER_DOTID),
        ("NormalID.", TokenType.IDENTIFIER_IDDOT),
        (".NormalID.", TokenType.IDENTIFIER_DOTIDDOT),
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
