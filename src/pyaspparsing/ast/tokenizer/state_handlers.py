"""state_handlers module"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
import typing

from .codewrapper import CharacterType, CodeWrapper
from .tokenizer_state import TokenizerState, TokenizerStateStack
from .token_types import TokenType, Token
from .state_types import TokenGenOpt, TokenOpt

state_handlers: typing.Dict[
    TokenizerState,
    Callable[[CodeWrapper, TokenizerStateStack, TokenGenOpt], typing.Optional[Token]],
] = {}


def create_state(state: TokenizerState):
    """Decorator function that adds state arguments
    to handler functions"""

    def wrap_func(func: Callable):
        @wraps(func)
        def add_state_args(
            cwrap: CodeWrapper,
            state_stack: TokenizerStateStack,
            curr_token_gen: TokenGenOpt = None,
        ) -> TokenOpt:
            return func(cwrap, state_stack, curr_token_gen)

        global state_handlers
        state_handlers[state] = add_state_args

        return add_state_args

    return wrap_func


@dataclass
class StateArgs:
    cwrap: CodeWrapper
    state_stack: TokenizerStateStack
    curr_token_gen: TokenGenOpt = None


def process_whitespace(cwrap: CodeWrapper) -> bool:
    """
    Returns
    -------
    bool
        True if newline consumed
    """
    while cwrap.try_next(next_type=CharacterType.WS):
        pass

    # check for line continuation
    if cwrap.try_next(next_char="_"):
        while cwrap.try_next(next_type=CharacterType.WS):
            pass
        # optional newline characters
        carriage_return = cwrap.try_next(next_char="\r")
        line_feed = cwrap.try_next(next_char="\n")
        # signal to caller if debug line info out of date
        return carriage_return or line_feed
    # don't update debug line info
    return False


def process_comment(cwrap: CodeWrapper):
    """Skip the body of a comment"""
    while not cwrap.check_for_end() and cwrap.current_char not in ":\r\n":
        cwrap.advance_pos()


def process_newline(cwrap: CodeWrapper) -> int:
    """Consume successive newline characters (':', '\\r', '\\n')

    A "\\r\\n" pair is treated as a single newline

    Returns
    -------
    line_processed : int
        Number of newlines processed
    """
    lines_processed: int = 0
    while not cwrap.check_for_end() and cwrap.current_char in ":\r\n":
        carriage_return = cwrap.current_char == "\r"
        cwrap.advance_pos()
        if carriage_return and (cwrap.current_char == "\n"):
            # "\r\n" should be treated as a single newline
            cwrap.advance_pos()
        lines_processed += 1
    return lines_processed


# ======== TOKENIZER STATE HANDLERS ========
# These are not called directly
# Instead, create_state registers them in the state_handlers global dict


@create_state(TokenizerState.CHECK_EXHAUSTED)
def state_check_exhausted(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.check_for_end():
        sargs.state_stack.leave_state()
    else:
        sargs.state_stack.enter_state(TokenizerState.CHECK_WHITESPACE)


@create_state(TokenizerState.CHECK_WHITESPACE)
def state_check_whitespace(*args):
    """"""
    sargs = StateArgs(*args)
    if process_whitespace(sargs.cwrap):
        sargs.cwrap.advance_line()
    if sargs.cwrap.check_for_end():
        # CHECK_EXHAUSTED should be below this state
        return
    if sargs.cwrap.current_char == "'":
        sargs.state_stack.enter_state(TokenizerState.SKIP_COMMENT)
    elif sargs.cwrap.current_char in ":\r\n":
        sargs.state_stack.enter_state(TokenizerState.START_NEWLINE)
    else:
        sargs.state_stack.enter_state(TokenizerState.START_TERMINAL)


@create_state(TokenizerState.SKIP_COMMENT)
def state_skip_comment(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.try_next(next_char="'"):
        process_comment(sargs.cwrap)
    sargs.state_stack.leave_state()
    if sargs.cwrap.check_for_end():
        # CHECK_EXHAUSTED should be below this state
        return
    if sargs.cwrap.current_char in ":\r\n":
        sargs.state_stack.enter_state(TokenizerState.START_NEWLINE)


@create_state(TokenizerState.START_NEWLINE)
def state_start_newline(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_start
    sargs.curr_token_gen.send(TokenType.NEWLINE)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_multiple(
        [TokenizerState.HANDLE_NEWLINE, TokenizerState.END_NEWLINE]
    )


@create_state(TokenizerState.HANDLE_NEWLINE)
def state_handle_newline(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.advance_line(process_newline(sargs.cwrap))
    sargs.state_stack.leave_state()


@create_state(TokenizerState.END_NEWLINE)
def state_end_newline(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        return ex.value


@create_state(TokenizerState.START_TERMINAL)
def state_start_terminal(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.END_TERMINAL)
def state_end_terminal(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_SYMBOL)
def state_construct_symbol(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_DOT)
def state_start_dot(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_AMP)
def state_start_amp(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_HEX)
def state_start_hex(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_OCT)
def state_start_oct(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.PROCESS_HEX)
def state_process_hex(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.PROCESS_OCT)
def state_process_oct(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CHECK_END_AMP)
def state_check_end_amp(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_HEX)
def state_construct_hex(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_OCT)
def state_construct_oct(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_ID)
def state_start_id(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_ID_ESCAPE)
def state_start_id_escape(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.PROCESS_ID)
def state_process_id(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CHECK_ID_REM)
def state_check_id_rem(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.PROCESS_ID_ESCAPE)
def state_process_id_escape(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CHECK_END_DOT)
def state_check_end_dot(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_ID)
def state_construct_id(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_NUMBER)
def state_start_number(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.PROCESS_NUMBER_CHUNK)
def state_process_number_chunk(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CHECK_FLOAT_DEC_PT)
def state_check_float_dec_pt(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CHECK_FLOAT_SCI_E)
def state_check_float_sci_e(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_FLOAT_DEC_PT)
def state_start_float_dec_pt(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_FLOAT_SCI_E)
def state_start_float_sci_e(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_INT)
def state_construct_int(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_FLOAT)
def state_construct_float(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_STRING)
def state_start_string(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.PROCESS_STRING)
def state_process_string(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.VERIFY_STRING_END)
def state_verify_string_end(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_STRING)
def state_construct_string(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.START_DATE)
def state_start_date(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.PROCESS_DATE)
def state_process_date(*args):
    """"""
    sargs = StateArgs(*args)


@create_state(TokenizerState.CONSTRUCT_DATE)
def state_construct_date(*args):
    """"""
    sargs = StateArgs(*args)
