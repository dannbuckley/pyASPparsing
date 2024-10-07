"""state_types module"""

import typing
from .token_types import Token, TokenType, DebugLineInfo

type TokenGen = typing.Generator[None, typing.Any, Token]
type TokenGenOpt = typing.Optional[TokenGen]
type TokenOpt = typing.Optional[Token]


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
    # start state
    slice_start: int = yield
    assert isinstance(slice_start, int)
    # construct state
    token_type: TokenType = yield
    assert isinstance(token_type, TokenType)
    # end state
    slice_end: int = yield
    assert isinstance(slice_end, int)
    debug_info: bool = yield
    assert isinstance(debug_info, bool)
    if debug_info:
        line_no: int = yield
        assert isinstance(line_no, int)
        line_start: int = yield
        assert isinstance(line_start, int)
    return Token(
        token_type,
        slice(slice_start, slice_end),
        line_info=(
            DebugLineInfo(line_no, slice_start - line_start) if debug_info else None
        ),
    )
