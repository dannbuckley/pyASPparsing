from contextlib import ExitStack
import typing
import pytest
from pyaspparsing import TokenizerError
from pyaspparsing.ast.tokenizer.token_types import Token, TokenType, KeywordType
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer


def test_exit_tokenize_error():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(TokenizerError))
        tkzr: Tokenizer = stack.enter_context(Tokenizer('<%"%>', False))
        while tkzr.current_token is not None:
            tkzr.advance_pos()


def test_empty_current_token():
    with Tokenizer("", False) as tkzr:
        assert tkzr.current_token is None


def test_token_current_token():
    with Tokenizer("<%a%>", False) as tkzr:
        assert tkzr.advance_pos()
        assert tkzr.current_token is not None
        assert tkzr.current_token.token_src == slice(2, 3)
        assert tkzr.current_token.token_type == TokenType.IDENTIFIER


def test_premature_advance_pos():
    with pytest.raises(RuntimeError):
        tkzr = Tokenizer("", False)
        tkzr.advance_pos()


def test_empty_advance_pos():
    with Tokenizer("", False) as tkzr:
        assert tkzr.advance_pos() is False


def test_one_token_advance_pos():
    with Tokenizer("a", False) as tkzr:
        # advance_pos() return an existence check
        # iterator should be exhausted after one step
        assert tkzr.advance_pos() is False


def test_multiple_token_advance_pos():
    with Tokenizer("<%a b%>", False) as tkzr:
        assert tkzr.advance_pos()
        assert tkzr.advance_pos()
        assert tkzr.advance_pos()
        assert tkzr.advance_pos() is False


def test_premature_get_token_code():
    with pytest.raises(RuntimeError):
        tkzr = Tokenizer("", False)
        tkzr.get_token_code()


def test_empty_get_token_code():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(RuntimeError))
        tkzr: Tokenizer = stack.enter_context(Tokenizer("", False))
        tkzr.get_token_code()


def test_lowercase_token_get_token_code():
    with Tokenizer("a", False) as tkzr:
        assert tkzr.get_token_code() == "a"


def test_uppercase_token_get_token_code():
    with Tokenizer("A", False) as tkzr:
        assert tkzr.get_token_code(True) == "a"
        assert tkzr.get_token_code(False) == "A"


def test_premature_try_token_type():
    with pytest.raises(RuntimeError):
        tkzr = Tokenizer("", False)
        tkzr.try_token_type(TokenType.NEWLINE)


def test_empty_try_token_type():
    with Tokenizer("", False) as tkzr:
        assert tkzr.try_token_type(TokenType.NEWLINE) is False


def test_token_try_token_type():
    with Tokenizer("<%\n%>", False) as tkzr:
        assert tkzr.advance_pos()
        assert tkzr.try_token_type(TokenType.NEWLINE) is True


def test_invalid_try_multiple_token_type():
    with Tokenizer("0", False) as tkzr:
        assert (
            tkzr.try_multiple_token_type([TokenType.LITERAL_HEX, TokenType.LITERAL_OCT])
            is False
        )


def test_valid_try_multiple_token_type():
    with Tokenizer("<%.add%>", False) as tkzr:
        assert tkzr.advance_pos()
        assert (
            tkzr.try_multiple_token_type(
                [
                    TokenType.IDENTIFIER,
                    TokenType.IDENTIFIER_IDDOT,
                    TokenType.IDENTIFIER_DOTID,
                    TokenType.IDENTIFIER_DOTIDDOT,
                ]
            )
            is True
        )


def test_premature_assert_consume():
    with pytest.raises(RuntimeError):
        tkzr = Tokenizer("", False)
        tkzr.assert_consume(TokenType.NEWLINE)


def test_invalid_assert_consume():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ValueError))
        tkzr: Tokenizer = stack.enter_context(Tokenizer("", False))
        tkzr.assert_consume(None)


def test_wrong_type_assert_consume():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(AssertionError))
        tkzr: Tokenizer = stack.enter_context(Tokenizer("a", False))
        tkzr.assert_consume(TokenType.NEWLINE)


def test_wrong_code_assert_consume():
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(AssertionError))
        tkzr: Tokenizer = stack.enter_context(Tokenizer("a", False))
        tkzr.assert_consume(TokenType.IDENTIFIER, "not_a")


def test_valid_assert_consume():
    with Tokenizer("<%&%>", False) as tkzr:
        assert tkzr.advance_pos()
        tkzr.assert_consume(TokenType.SYMBOL, "&")


def test_premature_try_consume():
    with pytest.raises(RuntimeError):
        tkzr = Tokenizer("", False)
        tkzr.try_consume(TokenType.IDENTIFIER, "a")


def test_empty_try_consume():
    with Tokenizer("", False) as tkzr:
        assert tkzr.try_consume(TokenType.IDENTIFIER, "a") is False


def test_wrong_type_try_consume():
    with Tokenizer("0", False) as tkzr:
        assert tkzr.try_consume(TokenType.IDENTIFIER, "a") is False


def test_wrong_code_try_consume():
    with Tokenizer("a", False) as tkzr:
        assert tkzr.try_consume(TokenType.IDENTIFIER, "not_a") is False


def test_wrong_code_use_in_try_consume():
    with Tokenizer("(", False) as tkzr:
        assert tkzr.try_consume(TokenType.SYMBOL, "-+", use_in=True) is False


def test_valid_try_consume():
    with Tokenizer("<%a%>", False) as tkzr:
        assert tkzr.advance_pos()
        assert tkzr.try_consume(TokenType.IDENTIFIER, "a") is True


def test_valid_use_in_try_consume():
    with Tokenizer("<%+%>", False) as tkzr:
        assert tkzr.advance_pos()
        assert tkzr.try_consume(TokenType.SYMBOL, "-+", use_in=True) is True


def test_premature_try_safe_keyword_id():
    with pytest.raises(RuntimeError):
        tkzr = Tokenizer("", False)
        tkzr.try_safe_keyword_id()


def test_empty_try_safe_keyword_id():
    with Tokenizer("", False) as tkzr:
        assert tkzr.try_safe_keyword_id() is None


def test_invalid_try_safe_keyword_id():
    with Tokenizer("a", False) as tkzr:
        assert tkzr.try_safe_keyword_id() is None


def test_valid_try_safe_keyword_id():
    with Tokenizer(f"<%{str(KeywordType.SAFE_KW_DEFAULT)}%>", False) as tkzr:
        assert tkzr.advance_pos()
        safe_kw: typing.Optional[Token] = tkzr.try_safe_keyword_id()
        assert safe_kw is not None
        assert safe_kw.token_src == slice(2, 9)
        assert safe_kw.token_type == TokenType.IDENTIFIER


def test_premature_try_keyword_id():
    with pytest.raises(RuntimeError):
        tkzr = Tokenizer("", False)
        tkzr.try_keyword_id()


def test_empty_try_keyword_id():
    with Tokenizer("", False) as tkzr:
        assert tkzr.try_keyword_id() is None


def test_invalid_try_keyword_id():
    with Tokenizer("a", False) as tkzr:
        assert tkzr.try_keyword_id() is None


def test_valid_try_keyword_id():
    with Tokenizer(f"<%{str(KeywordType.KW_AND)}%>", False) as tkzr:
        assert tkzr.advance_pos()
        kw_id: typing.Optional[Token] = tkzr.try_keyword_id()
        assert kw_id is not None
        assert kw_id.token_src == slice(2, 5)
        assert kw_id.token_type == TokenType.IDENTIFIER


def test_valid_safe_try_keyword_id():
    with Tokenizer(f"<%{str(KeywordType.SAFE_KW_DEFAULT)}%>", False) as tkzr:
        assert tkzr.advance_pos()
        kw_id: typing.Optional[Token] = tkzr.try_keyword_id()
        assert kw_id is not None
        assert kw_id.token_src == slice(2, 9)
        assert kw_id.token_type == TokenType.IDENTIFIER
