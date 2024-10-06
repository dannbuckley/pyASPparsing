"""state_machine module"""

import typing

from .codewrapper import CodeWrapper
from .tokenizer_state import TokenizerStateStack
from .token_types import Token
from .state_types import (
    TokenGenOpt,
    token_generator,
    state_starts_token,
    state_ends_token,
)
from .state_handlers import state_handlers


def tokenize(codeblock: str) -> typing.Generator[Token, None, None]:
    state_stack = TokenizerStateStack()
    with CodeWrapper(codeblock, False) as cwrap:
        curr_token_gen: TokenGenOpt = None

        # iterate until the stack is empty
        for state in state_stack:
            if state in state_starts_token:
                curr_token_gen = token_generator()
                next(curr_token_gen)  # start generator

            if state in state_ends_token:
                yield state_handlers[state](cwrap, state_stack, curr_token_gen)
                curr_token_gen = None
            else:
                state_handlers[state](cwrap, state_stack, curr_token_gen)
