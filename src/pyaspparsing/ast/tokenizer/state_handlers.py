"""state_handlers module"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
import typing

from ... import TokenizerError
from .codewrapper import CharacterType, CodeWrapper
from .tokenizer_state import TokenizerState, TokenizerStateStack
from .token_types import TokenType, Token
from .state_types import TokenGenOpt, TokenOpt

# states that use curr_token_gen
reg_state_starts_token: typing.List[TokenizerState] = []

# states that return a token
reg_state_returns_token: typing.List[TokenizerState] = []

# states that need to cleanup curr_token_gen
reg_state_cleans_token: typing.List[TokenizerState] = []

# map state enum to handler function
reg_state_handlers: typing.Dict[
    TokenizerState,
    Callable[[CodeWrapper, TokenizerStateStack, TokenGenOpt], typing.Optional[Token]],
] = {}


def create_state(
    state: TokenizerState,
    *,
    starts: bool = False,
    returns: bool = False,
    cleans: bool = False,
):
    """Decorator function that adds state arguments
    to handler functions

    State handler is registered in `reg_state_handlers`

    Parameters
    ----------
    state : TokenizerState
    starts : bool, default=False
        If True, register state in `reg_state_starts_token`
    returns : bool, default=False
        If True, register state in `reg_state_returns_token`
    cleans : bool, default=False
        If True, register state in `reg_state_cleans_token`
    """

    if starts:
        reg_state_starts_token.append(state)
    if returns:
        reg_state_returns_token.append(state)
    if cleans:
        reg_state_cleans_token.append(state)

    def wrap_func(func: Callable):
        @wraps(func)
        def add_state_args(
            cwrap: CodeWrapper,
            state_stack: TokenizerStateStack,
            curr_token_gen: TokenGenOpt = None,
        ) -> TokenOpt:
            return func(cwrap, state_stack, curr_token_gen)

        reg_state_handlers[state] = add_state_args
        return add_state_args

    return wrap_func


@dataclass
class StateArgs:
    """
    Attributes
    ----------
    cwrap : CodeWrapper
    state_stack : TokenizerStateStack
    curr_token_gen : TokenGenOpt, default=None
    """

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
# Instead, create_state registers them in the reg_state_handlers global dict


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
    sargs.state_stack.leave_state()
    if sargs.cwrap.check_for_end():
        # CHECK_EXHAUSTED should be below this state
        return
    if sargs.cwrap.try_next(next_char="'"):
        sargs.state_stack.enter_state(TokenizerState.SKIP_COMMENT)
    elif sargs.cwrap.current_char in ":\r\n":
        sargs.state_stack.enter_state(TokenizerState.START_NEWLINE)
    else:
        sargs.state_stack.enter_state(TokenizerState.START_TERMINAL)


@create_state(TokenizerState.SKIP_COMMENT)
def state_skip_comment(*args):
    """"""
    sargs = StateArgs(*args)
    process_comment(sargs.cwrap)
    sargs.state_stack.leave_state()
    if sargs.cwrap.check_for_end():
        # CHECK_EXHAUSTED should be below this state
        return
    if sargs.cwrap.current_char in ":\r\n":
        sargs.state_stack.enter_state(TokenizerState.START_NEWLINE)


@create_state(TokenizerState.START_NEWLINE, starts=True)
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


@create_state(TokenizerState.END_NEWLINE, returns=True, cleans=True)
def state_end_newline(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        return ex.value


@create_state(TokenizerState.START_TERMINAL, starts=True)
def state_start_terminal(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_start
    sargs.state_stack.leave_state()

    # terminals with known starting characters
    terminal_begin: typing.Dict[str, TokenizerState] = {
        ".": TokenizerState.START_DOT,
        "[": TokenizerState.START_ID_ESCAPE,
        '"': TokenizerState.START_STRING,
        "&": TokenizerState.START_AMP,
        "#": TokenizerState.START_DATE,
    }

    # try to determine token type
    if sargs.cwrap.validate_type(CharacterType.LETTER):
        sargs.state_stack.enter_state(TokenizerState.START_ID)
    elif sargs.cwrap.validate_type(CharacterType.DIGIT):
        sargs.state_stack.enter_state(TokenizerState.START_NUMBER)
    else:
        try:
            sargs.state_stack.enter_state(terminal_begin[sargs.cwrap.current_char])
        except KeyError:
            # return as symbol
            sargs.cwrap.advance_pos()  # consume symbol
            sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_SYMBOL)


@create_state(TokenizerState.END_TERMINAL, returns=True, cleans=True)
def state_end_terminal(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(True)  # debug_info
        sargs.curr_token_gen.send(sargs.cwrap.line_no)  # line_no
        sargs.curr_token_gen.send(sargs.cwrap.line_start)  # line_start
    except StopIteration as ex:
        return ex.value


@create_state(TokenizerState.CONSTRUCT_SYMBOL)
def state_construct_symbol(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(TokenType.SYMBOL)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.START_DOT)
def state_start_dot(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.assert_next(next_char=".")
    if sargs.cwrap.current_char == "[":
        sargs.state_stack.enter_state(TokenizerState.START_DOT_ID_ESCAPE)
    elif sargs.cwrap.validate_type(CharacterType.LETTER):
        sargs.state_stack.enter_state(TokenizerState.START_DOT_ID)
    elif sargs.cwrap.validate_type(CharacterType.DIGIT):
        sargs.state_stack.enter_multiple(
            [
                TokenizerState.CHECK_FLOAT_DEC_PT,
                TokenizerState.CHECK_FLOAT_SCI_E,
                TokenizerState.CONSTRUCT_FLOAT,
            ]
        )
    else:
        # return as symbol
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_SYMBOL)
    sargs.state_stack.leave_state()


@create_state(TokenizerState.START_AMP)
def state_start_amp(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.assert_next(next_char="&")
    if sargs.cwrap.try_next(next_char="H"):
        sargs.state_stack.enter_state(TokenizerState.START_HEX)
    elif sargs.cwrap.validate_type(CharacterType.OCT_DIGIT):
        sargs.state_stack.enter_state(TokenizerState.START_OCT)
    else:
        # return as symbol
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_SYMBOL)
    sargs.state_stack.leave_state()


@create_state(TokenizerState.START_HEX)
def state_start_hex(*args):
    """"""
    sargs = StateArgs(*args)
    # leading 'H' already consumed by START_AMP
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_HEX,
            TokenizerState.CHECK_END_AMP,
            TokenizerState.CONSTRUCT_HEX,
        ]
    )


@create_state(TokenizerState.START_OCT)
def state_start_oct(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_OCT,
            TokenizerState.CHECK_END_AMP,
            TokenizerState.CONSTRUCT_OCT,
        ]
    )


@create_state(TokenizerState.PROCESS_HEX)
def state_process_hex(*args):
    """"""
    sargs = StateArgs(*args)
    # need at least one hex digit
    if sargs.cwrap.assert_next(next_type=CharacterType.HEX_DIGIT):
        # not at end of codeblock
        while sargs.cwrap.try_next(next_type=CharacterType.HEX_DIGIT):
            pass
    sargs.state_stack.leave_state()


@create_state(TokenizerState.PROCESS_OCT)
def state_process_oct(*args):
    """"""
    sargs = StateArgs(*args)
    # need at least one oct digit
    if sargs.cwrap.assert_next(next_type=CharacterType.OCT_DIGIT):
        # not at end of codeblock
        while sargs.cwrap.try_next(next_type=CharacterType.OCT_DIGIT):
            pass
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CHECK_END_AMP)
def state_check_end_amp(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.try_next(next_char="&")
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CONSTRUCT_HEX)
def state_construct_hex(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(TokenType.LITERAL_HEX)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.CONSTRUCT_OCT)
def state_construct_oct(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(TokenType.LITERAL_OCT)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.START_ID)
def state_start_id(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_ID,
            TokenizerState.CHECK_ID_REM,
        ]
    )


@create_state(TokenizerState.START_DOT_ID)
def state_start_dot_id(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_ID, TokenizerState.CHECK_DOT_ID_REM]
    )


@create_state(TokenizerState.START_ID_ESCAPE)
def state_start_id_escape(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_ID_ESCAPE, TokenizerState.CHECK_END_DOT]
    )


@create_state(TokenizerState.START_DOT_ID_ESCAPE)
def state_start_dot_id_escape(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_ID_ESCAPE, TokenizerState.CHECK_DOT_END_DOT]
    )


@create_state(TokenizerState.PROCESS_ID)
def state_process_id(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.assert_next(next_type=CharacterType.LETTER)
    while sargs.cwrap.try_next(next_type=CharacterType.ID_TAIL):
        pass
    sargs.state_stack.leave_state()


@create_state(TokenizerState.PROCESS_ID_ESCAPE)
def state_process_id_escape(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.assert_next(next_char="[")
    while sargs.cwrap.try_next(next_type=CharacterType.ID_NAME_CHAR):
        pass
    sargs.cwrap.assert_next(next_char="]")
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CHECK_END_DOT)
def state_check_end_dot(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.try_next(next_char="."):
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_ID_DOT)
    else:
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_ID)
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CHECK_DOT_END_DOT)
def state_check_dot_end_dot(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.try_next(next_char="."):
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_DOT_ID_DOT)
    else:
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_DOT_ID)
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CHECK_ID_REM)
def state_check_id_rem(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    rem_end = sargs.cwrap.current_idx
    rem_start = rem_end - 3
    if (rem_start >= 0) and (
        "rem" in sargs.cwrap.codeblock[rem_start:rem_end].casefold()
    ):
        sargs.state_stack.enter_multiple(
            [
                # SKIP_COMMENT might create a newline token,
                # so need to clean token first
                TokenizerState.CANCEL_ID,
                TokenizerState.SKIP_COMMENT,
            ]
        )
    else:
        sargs.state_stack.enter_state(TokenizerState.CHECK_END_DOT)


@create_state(TokenizerState.CHECK_DOT_ID_REM)
def state_check_dot_id_rem(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    rem_end = sargs.cwrap.current_idx
    rem_start = rem_end - 3
    if rem_start > 0 and ("rem" in sargs.cwrap.codeblock[rem_start:rem_end].casefold()):
        raise TokenizerError("Illegal use of '.' symbol; cannot appear before Rem")
    else:
        sargs.state_stack.enter_state(TokenizerState.CHECK_DOT_END_DOT)


@create_state(TokenizerState.CANCEL_ID, cleans=True)
def state_cancel_id(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.curr_token_gen.close()


@create_state(TokenizerState.CONSTRUCT_ID)
def state_construct_id(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.curr_token_gen.send(TokenType.IDENTIFIER)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.CONSTRUCT_DOT_ID)
def state_construct_dot_id(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.curr_token_gen.send(TokenType.IDENTIFIER_DOTID)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.CONSTRUCT_ID_DOT)
def state_construct_id_dot(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.curr_token_gen.send(TokenType.IDENTIFIER_IDDOT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.CONSTRUCT_DOT_ID_DOT)
def state_construct_dot_id_dot(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.leave_state()
    sargs.curr_token_gen.send(TokenType.IDENTIFIER_DOTIDDOT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.START_NUMBER)
def state_start_number(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_NUMBER_CHUNK, TokenizerState.VERIFY_INT]
    )
    sargs.state_stack.leave_state()


@create_state(TokenizerState.PROCESS_NUMBER_CHUNK)
def state_process_number_chunk(*args):
    """"""
    sargs = StateArgs(*args)
    # need at least one digit
    if sargs.cwrap.assert_next(next_type=CharacterType.DIGIT):
        while sargs.cwrap.try_next(next_type=CharacterType.DIGIT):
            pass
    sargs.state_stack.leave_state()


@create_state(TokenizerState.VERIFY_INT)
def state_verify_int(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.current_char == ".":
        # has '.', not an int!
        sargs.state_stack.enter_multiple(
            [
                TokenizerState.CHECK_FLOAT_DEC_PT,
                TokenizerState.CHECK_FLOAT_SCI_E,
                TokenizerState.CONSTRUCT_FLOAT,
            ]
        )
    elif sargs.cwrap.current_char == "E":
        # has 'E', not an int!
        sargs.state_stack.enter_multiple(
            [TokenizerState.CHECK_FLOAT_SCI_E, TokenizerState.CONSTRUCT_FLOAT]
        )
    else:
        # symbol is an int
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_INT)
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CHECK_FLOAT_DEC_PT)
def state_check_float_dec_pt(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.try_next(next_char="."):
        sargs.state_stack.enter_state(TokenizerState.PROCESS_NUMBER_CHUNK)
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CHECK_FLOAT_SCI_E)
def state_check_float_sci_e(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.try_next(next_char="E"):
        if not sargs.cwrap.check_for_end() and sargs.cwrap.current_char in "+-":
            sargs.cwrap.advance_pos()  # consume '-' or '+'
        sargs.state_stack.enter_state(TokenizerState.PROCESS_NUMBER_CHUNK)
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CONSTRUCT_INT)
def state_construct_int(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(TokenType.LITERAL_INT)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.CONSTRUCT_FLOAT)
def state_construct_float(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(TokenType.LITERAL_FLOAT)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.START_STRING)
def state_start_string(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_STRING,
            TokenizerState.VERIFY_STRING_END,
            TokenizerState.CONSTRUCT_STRING,
        ]
    )
    sargs.state_stack.leave_state()


@create_state(TokenizerState.PROCESS_STRING)
def state_process_string(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.assert_next(next_char='"')
    while sargs.cwrap.try_next(next_type=CharacterType.STRING_CHAR):
        pass
    sargs.cwrap.assert_next(next_char='"')
    sargs.state_stack.leave_state()


@create_state(TokenizerState.VERIFY_STRING_END)
def state_verify_string_end(*args):
    """"""
    sargs = StateArgs(*args)
    if sargs.cwrap.current_char == '"':
        # double quote is escaped
        sargs.state_stack.enter_state(TokenizerState.PROCESS_STRING)
    else:
        # reached end of string literal
        sargs.state_stack.leave_state()


@create_state(TokenizerState.CONSTRUCT_STRING)
def state_construct_string(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(TokenType.LITERAL_STRING)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_state(TokenizerState.START_DATE)
def state_start_date(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_DATE, TokenizerState.CONSTRUCT_DATE]
    )
    sargs.state_stack.leave_state()


@create_state(TokenizerState.PROCESS_DATE)
def state_process_date(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.cwrap.assert_next(next_char="#")
    while sargs.cwrap.try_next(next_type=CharacterType.DATE_CHAR):
        pass
    sargs.cwrap.assert_next(next_char="#")
    sargs.state_stack.leave_state()


@create_state(TokenizerState.CONSTRUCT_DATE)
def state_construct_date(*args):
    """"""
    sargs = StateArgs(*args)
    sargs.curr_token_gen.send(TokenType.LITERAL_DATE)  # token_type
    sargs.state_stack.leave_state()
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)
