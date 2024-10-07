"""state_machine module"""

import typing

from ... import TokenizerError
from .codewrapper import CodeWrapper
from .tokenizer_state import TokenizerStateStack
from .token_types import Token
from .state_types import TokenGenOpt, token_generator
from .state_handlers import (
    reg_state_handlers,
    reg_state_starts_token,
    reg_state_returns_token,
    reg_state_cleans_token,
)


def tokenize(codeblock: str) -> typing.Generator[Token, None, None]:
    state_stack = TokenizerStateStack()
    try:
        with CodeWrapper(codeblock, False) as cwrap:
            curr_token_gen: TokenGenOpt = None

            # iterate until the stack is empty
            for state in state_stack:
                if state in reg_state_starts_token:
                    curr_token_gen = token_generator()
                    next(curr_token_gen)  # start generator

                if state in reg_state_returns_token:
                    yield reg_state_handlers[state](cwrap, state_stack, curr_token_gen)
                else:
                    reg_state_handlers[state](cwrap, state_stack, curr_token_gen)

                if state in reg_state_cleans_token:
                    curr_token_gen = None
    except Exception as ex:
        raise TokenizerError("An error occurred during tokenization") from ex
