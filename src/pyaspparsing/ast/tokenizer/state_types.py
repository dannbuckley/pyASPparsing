"""state_types module"""

import typing
from .tokenizer_state import TokenizerState
from .token_types import Token, TokenType, DebugLineInfo

type TokenGen = typing.Generator[None, typing.Any, Token]
type TokenGenOpt = typing.Optional[TokenGen]
type TokenOpt = typing.Optional[Token]


# states that use curr_token_gen
state_starts_token: typing.List[TokenizerState] = [
    TokenizerState.START_NEWLINE,
    TokenizerState.START_TERMINAL,
]

# states that return a token and need to cleanup curr_token_gen
state_ends_token: typing.List[TokenizerState] = [
    TokenizerState.END_NEWLINE,
    TokenizerState.END_TERMINAL,
]


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
    # construct state
    token_type: TokenType = yield
    # end state
    slice_end: int = yield
    debug_info: bool = yield
    if debug_info:
        line_no: int = yield
        line_start: int = yield
    return Token(
        token_type,
        slice(slice_start, slice_end),
        line_info=DebugLineInfo(line_no, line_start) if debug_info else None,
    )
