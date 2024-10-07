"""state_machine module"""

import typing

import attrs

from ... import TokenizerError
from .codewrapper import CodeWrapper
from .tokenizer_state import TokenizerStateStack
from .token_types import Token, TokenType, KeywordType, DebugLineInfo
from .state_handlers import (
    reg_state_handlers,
    reg_state_starts_token,
    reg_state_returns_token,
    reg_state_cleans_token,
    TokenGen,
    TokenGenOpt,
)


def token_generator() -> TokenGen:
    """Parameters received by `send()` must be provided
    in the order described below

    The generator will return early if `debug_info` is False

    Returns
    -------
    Token

    Receives
    --------
    slice_start : int
    token_type : TokenType
    slice_end : int
    debug_info : bool
    line_no : int
    line_start : int
    """
    # START_* state
    slice_start: int = yield
    assert isinstance(
        slice_start, int
    ), f"slice_start must receive an int; got {type(slice_start)}"

    # CONSTRUCT_* state
    token_type: TokenType = yield
    assert isinstance(
        token_type, TokenType
    ), f"token_type must receive a TokenType; got {type(token_type)}"

    # END_* state
    slice_end: int = yield
    assert isinstance(
        slice_end, int
    ), f"slice_end must receive an int; got {type(slice_end)}"
    debug_info: bool = yield
    assert isinstance(
        debug_info, bool
    ), f"debug_info must receive a bool; got {type(debug_info)}"
    if debug_info:
        line_no: int = yield
        assert isinstance(
            line_no, int
        ), f"line_no must receive an int; got {type(line_no)}"
        line_start: int = yield
        assert isinstance(
            line_start, int
        ), f"line_start must receive an int; got {type(line_start)}"
    return Token(
        token_type,
        slice(slice_start, slice_end),
        line_info=(
            DebugLineInfo(line_no, slice_start - line_start) if debug_info else None
        ),
    )


def tokenize(codeblock: str) -> typing.Generator[Token, None, None]:
    """
    Parameters
    ----------
    codeblock : str

    Yields
    ------
    Token
    """
    state_stack = TokenizerStateStack()
    try:
        with CodeWrapper(codeblock, False) as cwrap:
            curr_token_gen: TokenGenOpt = None

            # iterate until the stack is empty
            for state in state_stack:
                if state in reg_state_starts_token:
                    curr_token_gen = token_generator()
                    # next(..., None) is a fix for pylint R1708
                    # don't raise StopIteration in a generator
                    next(curr_token_gen, None)  # start generator

                if state in reg_state_returns_token:
                    yield reg_state_handlers[state](cwrap, state_stack, curr_token_gen)
                else:
                    reg_state_handlers[state](cwrap, state_stack, curr_token_gen)

                if state in reg_state_cleans_token:
                    curr_token_gen = None
    except Exception as ex:
        raise TokenizerError("An error occurred during tokenization") from ex


@attrs.define
class Tokenizer:
    """
    Attributes
    ----------
    codeblock : str

    Methods
    -------
    advance_pos()

    get_token_code(casefold=True)

    try_token_type(tok_type)

    assert_consume(tok_type, tok_code, *, casefold=True)

    try_consume(tok_type, tok_code, *, casefold=True, use_in=False)

    try_safe_keyword_id()

    try_keyword_id()
    """

    codeblock: str
    _tok_iter: typing.Optional[typing.Generator[Token, None, None]] = attrs.field(
        default=None, repr=False, init=False
    )
    _pos_tok: typing.Optional[Token] = attrs.field(default=None, repr=False, init=False)

    def __enter__(self) -> typing.Self:
        """"""
        self._tok_iter = tokenize(self.codeblock)
        # preload first token
        self._pos_tok = next(
            self._tok_iter, None
        )  # use next(..., None) instead of handling StopIteration
        return self

    def __exit__(self, exc_type, exc_val: BaseException, tb) -> bool:
        """"""
        self._pos_tok = None
        self._tok_iter.close()
        self._tok_iter = None
        # don't suppress exception
        return False

    def advance_pos(self) -> bool:
        """
        Returns
        -------
        bool
            True if tokenizer is not exhausted

        Raises
        ------
        RuntimeError
            If this method is used outside of a runtime context
        """
        if self._tok_iter is None:
            raise RuntimeError("Cannot use advance_pos() outside of a runtime context")
        if self._pos_tok is None:
            # iterator already exhausted
            return False
        self._pos_tok = next(self._tok_iter, None)
        return self._pos_tok is not None

    def get_token_code(self, casefold: bool = True) -> str:
        """
        Parameters
        ----------
        casefold : bool, default=True
            Whether token code should be returned as a casefolded string

        Returns
        -------
        str

        Raises
        ------
        RuntimeError
            If this method is used outside of a runtime context or
            if the current token is None
        """
        if self._tok_iter is None:
            raise RuntimeError(
                "Cannot use get_token_code() outside of a runtime context"
            )
        if self._pos_tok is None:
            raise RuntimeError("Tried to load code string for None token")
        tok_code = self.codeblock[self._pos_tok.token_src]
        return tok_code.casefold() if casefold else tok_code

    def try_token_type(self, tok_type: TokenType) -> bool:
        """Compare the given token type against
        the token type of the current token

        Returns
        -------
        bool
            False if the current token is None or
            the token types do not match

        Raises
        ------
        RuntimeError
            If this method is used outside of a runtime context
        """
        if self._tok_iter is None:
            raise RuntimeError(
                "Cannot use try_token_type() outside of a runtime context"
            )
        if self._pos_tok is None:
            return False
        return self._pos_tok.token_type == tok_type

    def assert_consume(
        self,
        tok_type: TokenType,
        tok_code: typing.Optional[str] = None,
        *,
        casefold: bool = True,
    ):
        """Attempt to consume a specific token.
        Raises on failure

        Parameters
        ----------
        tok_type : TokenType
        tok_code : str | None
            Source code to use when comparing against current token
        casefold : bool, default=True
            Whether tok_code is casefolded. Passed to `get_token_code()`

        Raises
        ------
        RuntimeError
            If this method is used outside of a runtime context
        ValueError
            If tok_type is None
        AssertionError
        """
        if self._tok_iter is None:
            raise RuntimeError(
                "Cannot use assert_consume() outside of a runtime context"
            )
        if tok_type is None:
            raise ValueError("tok_type must be a valid TokenType, not None")
        # try_token_type() is also an existence check, will return False if token is None
        if tok_code is None:
            assert self.try_token_type(
                tok_type
            ), f"Expected token of type {repr(tok_type)}"
        else:
            assert self.try_token_type(tok_type) and (
                self.get_token_code(casefold) == tok_code
            ), f"Expected token of type {repr(tok_type)} and value {repr(tok_code)}"
        self.advance_pos()  # consume

    def try_consume(
        self,
        tok_type: TokenType,
        tok_code: str,
        *,
        casefold: bool = True,
        use_in: bool = False,
    ) -> bool:
        """Attempt to consume a specific optional token.
        Does not raise on failure

        Parameters
        ----------
        tok_type : TokenType
        tok_code : str
            Source code to use when comparing against current token
        casefold : bool, default=True
            Whether tok_code is casefolded. Passed to `get_token_code()`
        use_in : bool, default=False
            If True, will use `get_token_code() in tok_code`;
            otherwise, `get_token_code() == tok_code`

        Returns
        -------
        bool
            True if token was consumed

        Raises
        ------
        RuntimeError
            If this method is used outside of a runtime context
        """
        if self._tok_iter is None:
            raise RuntimeError("Cannot use try_consume() outside of a runtime context")
        try:
            curr_code: str = self.get_token_code(casefold)
        except RuntimeError:
            return False
        if not (
            self.try_token_type(tok_type)
            and (
                (not use_in and (curr_code == tok_code))
                or (use_in and (curr_code in tok_code))
            )
        ):
            return False
        self.advance_pos()  # consume
        return True

    def try_safe_keyword_id(self) -> typing.Optional[Token]:
        """
        Returns
        -------
        str | None

        Raises
        ------
        RuntimeError
            If this method is used outside of a runtime context
        """
        if self._tok_iter is None:
            raise RuntimeError(
                "Cannot use try_safe_keyword_id() outside of a runtime context"
            )
        if self.try_token_type(TokenType.IDENTIFIER) and self.get_token_code() in [
            KeywordType.SAFE_KW_DEFAULT,
            KeywordType.SAFE_KW_ERASE,
            KeywordType.SAFE_KW_ERROR,
            KeywordType.SAFE_KW_EXPLICIT,
            KeywordType.SAFE_KW_PROPERTY,
            KeywordType.SAFE_KW_STEP,
        ]:
            return self._pos_tok
        return None

    def try_keyword_id(self) -> typing.Optional[Token]:
        """
        Returns
        -------
        str | None

        Raises
        ------
        RuntimeError
            If this method is used outside of a runtime context
        """
        if self._tok_iter is None:
            raise RuntimeError(
                "Cannot use try_keyword_id() outside of a runtime context"
            )
        if (safe_kw := self.try_safe_keyword_id()) is not None:
            return safe_kw
        if self.try_token_type(TokenType.IDENTIFIER) and self.get_token_code() in [
            KeywordType.KW_AND,
            KeywordType.KW_BYREF,
            KeywordType.KW_BYVAL,
            KeywordType.KW_CALL,
            KeywordType.KW_CASE,
            KeywordType.KW_CLASS,
            KeywordType.KW_CONST,
            KeywordType.KW_DIM,
            KeywordType.KW_DO,
            KeywordType.KW_EACH,
            KeywordType.KW_ELSE,
            KeywordType.KW_ELSEIF,
            KeywordType.KW_EMPTY,
            KeywordType.KW_END,
            KeywordType.KW_EQV,
            KeywordType.KW_EXIT,
            KeywordType.KW_FALSE,
            KeywordType.KW_FOR,
            KeywordType.KW_FUNCTION,
            KeywordType.KW_GET,
            KeywordType.KW_GOTO,
            KeywordType.KW_IF,
            KeywordType.KW_IMP,
            KeywordType.KW_IN,
            KeywordType.KW_IS,
            KeywordType.KW_LET,
            KeywordType.KW_LOOP,
            KeywordType.KW_MOD,
            KeywordType.KW_NEW,
            KeywordType.KW_NEXT,
            KeywordType.KW_NOT,
            KeywordType.KW_NOTHING,
            KeywordType.KW_NULL,
            KeywordType.KW_ON,
            KeywordType.KW_OPTION,
            KeywordType.KW_OR,
            KeywordType.KW_PRESERVE,
            KeywordType.KW_PRIVATE,
            KeywordType.KW_PUBLIC,
            KeywordType.KW_REDIM,
            KeywordType.KW_RESUME,
            KeywordType.KW_SELECT,
            KeywordType.KW_SET,
            KeywordType.KW_SUB,
            KeywordType.KW_THEN,
            KeywordType.KW_TO,
            KeywordType.KW_TRUE,
            KeywordType.KW_UNTIL,
            KeywordType.KW_WEND,
            KeywordType.KW_WITH,
            KeywordType.KW_XOR,
        ]:
            return self._pos_tok
        return None
