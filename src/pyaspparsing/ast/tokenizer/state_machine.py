"""state_machine module"""

import typing

from ... import TokenizerError
from .codewrapper import CodeWrapper
from .tokenizer_state import TokenizerStateStack
from .token_types import Token, TokenType, DebugLineInfo
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
