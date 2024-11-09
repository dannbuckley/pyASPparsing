"""state_handlers module"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Optional, Any, Generator

from .codewrapper import CharacterType, CodeWrapper
from .tokenizer_state import TokenizerState, TokenizerStateStack
from .token_types import TokenType, Token

type TokenGen = Generator[None, Any, Token]
type TokenGenOpt = Optional[TokenGen]
type TokenOpt = Optional[Token]

# states that use curr_token_gen
reg_state_starts_token: list[TokenizerState] = []

# states that return a token
reg_state_returns_token: list[TokenizerState] = []

# states that need to cleanup curr_token_gen
reg_state_cleans_token: list[TokenizerState] = []

# map state enum to handler function
reg_state_handlers: dict[
    TokenizerState,
    Callable[[CodeWrapper, TokenizerStateStack, TokenGenOpt], TokenOpt],
] = {}


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


def create_tokenizer_state(
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

    def wrap_func(func: Callable[[StateArgs], TokenOpt]):
        @wraps(func)
        def add_state_args(
            cwrap: CodeWrapper,
            state_stack: TokenizerStateStack,
            curr_token_gen: TokenGenOpt = None,
        ) -> TokenOpt:
            return func(StateArgs(cwrap, state_stack, curr_token_gen))

        reg_state_handlers[state] = add_state_args
        return add_state_args

    return wrap_func


# ======== TOKENIZER STATE HANDLERS ========
# THESE ARE NOT CALLED DIRECTLY
# Instead, the create_tokenizer_state decorator registers them in the reg_state_handlers global dict
# States are exited automatically unless state_stack.persist_state() is called


@create_tokenizer_state(TokenizerState.CHECK_DELIM_START)
def state_check_delim_start(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_DELIM_START tokenizer state"""
    # ASP starting delimiter
    if sargs.cwrap.try_next(next_char="<"):
        if sargs.cwrap.try_next(next_char="%"):
            # determine delimiter type
            if sargs.cwrap.try_next(next_char="="):
                sargs.state_stack.enter_multiple(
                    [
                        TokenizerState.CONSTRUCT_DELIM_OUTPUT,
                        TokenizerState.CHECK_DELIM_END,
                    ]
                )
            elif sargs.cwrap.try_next(next_char="@"):
                # one whitespace character required after '@'
                sargs.cwrap.assert_next(next_type=CharacterType.WS)
                sargs.state_stack.enter_multiple(
                    [
                        TokenizerState.CONSTRUCT_DELIM_PROCESSING,
                        TokenizerState.CHECK_DELIM_END,
                    ]
                )
            else:
                sargs.state_stack.enter_multiple(
                    [
                        TokenizerState.CONSTRUCT_DELIM_SCRIPT,
                        TokenizerState.CHECK_DELIM_END,
                    ]
                )
        elif sargs.cwrap.try_next(next_char="!"):
            # HTML comment
            if sargs.cwrap.current_char.casefold() == "d":
                # <!DOCTYPE ...>
                sargs.cwrap.advance_pos()
                sargs.state_stack.enter_state(TokenizerState.CHECK_HTML_DOCTYPE)
            else:
                sargs.cwrap.assert_next(next_char="-")
                sargs.cwrap.assert_next(next_char="-")
                sargs.state_stack.enter_state(TokenizerState.CHECK_HTML_COMMENT)
        else:
            sargs.state_stack.enter_state(TokenizerState.START_FILE_TEXT_DELAYED)
    else:
        sargs.state_stack.enter_state(TokenizerState.START_FILE_TEXT)


@create_tokenizer_state(TokenizerState.CHECK_DELIM_END)
def state_check_delim_end(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_DELIM_END tokenizer state"""
    if sargs.cwrap.try_next(next_char="%"):
        if sargs.cwrap.try_next(next_char=">"):
            sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_DELIM_END)
        else:
            sargs.state_stack.persist_state()
            sargs.state_stack.enter_state(TokenizerState.RETURN_PERC_SYMBOL)
    else:
        if not sargs.cwrap.check_for_end():
            sargs.state_stack.enter_state(TokenizerState.CHECK_WHITESPACE)


@create_tokenizer_state(
    TokenizerState.RETURN_PERC_SYMBOL, starts=True, returns=True, cleans=True
)
def state_return_perc_symbol(sargs: StateArgs) -> TokenOpt:
    """Handler for RETURN_PERC_SYMBOL tokenizer state

    Found a '%' symbol during CHECK_DELIM_END,
    but it did not belong to an ending delimiter

    Returns
    -------
    Token
    """
    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx - 1)  # slice_start
        sargs.curr_token_gen.send(TokenType.SYMBOL)  # token_type
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(True)  # debug_info
        sargs.curr_token_gen.send(sargs.cwrap.line_no)  # line_no
        sargs.curr_token_gen.send(sargs.cwrap.line_start)  # line_start
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"


@create_tokenizer_state(TokenizerState.CONSTRUCT_DELIM_SCRIPT, starts=True)
def state_construct_delim_script(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_DELIM_SCRIPT tokenizer state"""
    # script delimiter is '<%', doesn't require whitespace
    sargs.cwrap.update_line_code_start()
    sargs.curr_token_gen.send(sargs.cwrap.current_idx - 2)  # slice_start
    sargs.curr_token_gen.send(TokenType.DELIM_START_SCRIPT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_DELIM)


@create_tokenizer_state(TokenizerState.CONSTRUCT_DELIM_PROCESSING, starts=True)
def state_construct_delim_processing(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_DELIM_PROCESSING tokenizer state"""
    # processing delimiter is '<%@ ', requires whitespace
    sargs.curr_token_gen.send(sargs.cwrap.current_idx - 4)  # slice_start
    sargs.curr_token_gen.send(TokenType.DELIM_START_PROCESSING)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_DELIM)


@create_tokenizer_state(TokenizerState.CONSTRUCT_DELIM_OUTPUT, starts=True)
def state_construct_delim_output(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_DELIM_OUTPUT tokenizer state"""
    # output delimiter is '<%=', doesn't require whitespace
    sargs.curr_token_gen.send(sargs.cwrap.current_idx - 3)  # slice_start
    sargs.curr_token_gen.send(TokenType.DELIM_START_OUTPUT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_DELIM)


@create_tokenizer_state(TokenizerState.CONSTRUCT_DELIM_END, starts=True)
def state_construct_delim_end(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_DELIM_END tokenizer state"""
    # end delimiter is '%>'
    sargs.curr_token_gen.send(sargs.cwrap.current_idx - 2)  # slice_start
    sargs.curr_token_gen.send(TokenType.DELIM_END)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_DELIM)


@create_tokenizer_state(TokenizerState.END_DELIM, returns=True, cleans=True)
def state_end_delim(sargs: StateArgs) -> TokenOpt:
    """Handler for END_DELIM tokenizer state

    Returns
    -------
    Token
    """
    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
    return ret_token


@create_tokenizer_state(TokenizerState.START_FILE_TEXT, starts=True)
def state_start_file_text(sargs: StateArgs) -> TokenOpt:
    """Handler for START_FILE_TEXT tokenizer state"""
    sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_start
    sargs.curr_token_gen.send(TokenType.FILE_TEXT)  # token_type
    sargs.state_stack.enter_multiple(
        [TokenizerState.CONSUME_FILE_TEXT, TokenizerState.VERIFY_FILE_TEXT_END]
    )


@create_tokenizer_state(TokenizerState.START_FILE_TEXT_DELAYED, starts=True)
def state_start_file_text_delayed(sargs: StateArgs) -> TokenOpt:
    """Handler for START_FILE_TEXT_DELAYED tokenizer state"""
    # previous character was consumed when checking for a delimiter
    sargs.curr_token_gen.send(sargs.cwrap.current_idx - 1)  # slice_start
    sargs.curr_token_gen.send(TokenType.FILE_TEXT)  # token_type
    sargs.state_stack.enter_multiple(
        [TokenizerState.CONSUME_FILE_TEXT, TokenizerState.VERIFY_FILE_TEXT_END]
    )


@create_tokenizer_state(TokenizerState.CONSUME_FILE_TEXT)
def state_consume_file_text(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSUME_FILE_TEXT tokenizer state"""
    while not sargs.cwrap.check_for_end() and sargs.cwrap.current_char != "<":
        sargs.cwrap.advance_pos()


@create_tokenizer_state(TokenizerState.VERIFY_FILE_TEXT_END)
def state_verify_file_text_end(sargs: StateArgs) -> TokenOpt:
    """Handler for VERIFY_FILE_TEXT_END tokenizer state"""
    # reached end of codeblock?
    file_text_end = sargs.cwrap.current_idx
    if sargs.cwrap.check_for_end():
        sargs.curr_token_gen.send(file_text_end)  # slice_end
        sargs.state_stack.enter_state(TokenizerState.END_FILE_TEXT)
        return

    # confirm that the '<' belongs to a starting delimiter
    sargs.cwrap.assert_next(next_char="<")
    if sargs.cwrap.try_next(next_char="%"):
        # send slice_end here instead of in END_FILE_TEXT
        # to avoid including the start delimiter in the FILE_TEXT token source
        sargs.curr_token_gen.send(file_text_end)  # slice_end
        if sargs.cwrap.try_next(next_char="="):
            sargs.state_stack.enter_multiple(
                [
                    TokenizerState.END_FILE_TEXT,
                    TokenizerState.CONSTRUCT_DELIM_OUTPUT,
                    TokenizerState.CHECK_DELIM_END,
                ]
            )
        elif sargs.cwrap.try_next(next_char="@"):
            # one whitespace character required after '@'
            sargs.cwrap.assert_next(next_type=CharacterType.WS)
            sargs.state_stack.enter_multiple(
                [
                    TokenizerState.END_FILE_TEXT,
                    TokenizerState.CONSTRUCT_DELIM_PROCESSING,
                    TokenizerState.CHECK_DELIM_END,
                ]
            )
        else:
            sargs.state_stack.enter_multiple(
                [
                    TokenizerState.END_FILE_TEXT,
                    TokenizerState.CONSTRUCT_DELIM_SCRIPT,
                    TokenizerState.CHECK_DELIM_END,
                ]
            )
    elif sargs.cwrap.try_next(next_char="!"):
        # HTML comment
        sargs.curr_token_gen.send(file_text_end)  # slice_end
        if sargs.cwrap.current_char.casefold() == "d":
            # <!DOCTYPE ...>
            sargs.cwrap.advance_pos()
            sargs.state_stack.enter_multiple(
                [TokenizerState.END_FILE_TEXT, TokenizerState.CHECK_HTML_DOCTYPE]
            )
        else:
            sargs.cwrap.assert_next(next_char="-")
            sargs.cwrap.assert_next(next_char="-")
            sargs.state_stack.enter_multiple(
                [TokenizerState.END_FILE_TEXT, TokenizerState.CHECK_HTML_COMMENT]
            )
    else:
        # not a starting delimiter, keep consuming file text
        sargs.state_stack.persist_state()
        sargs.state_stack.enter_state(TokenizerState.CONSUME_FILE_TEXT)


@create_tokenizer_state(TokenizerState.END_FILE_TEXT, returns=True, cleans=True)
def state_end_file_text(sargs: StateArgs) -> TokenOpt:
    """Handler for END_FILE_TEXT tokenizer state

    Returns
    -------
    Token
    """
    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
    return ret_token


@create_tokenizer_state(
    TokenizerState.CHECK_HTML_COMMENT, starts=True, returns=True, cleans=True
)
def state_check_html_comment(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_HTML_COMMENT tokenizer state

    Returns
    -------
    Token
    """
    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx - 4)  # slice_start
        sargs.curr_token_gen.send(TokenType.HTML_START_COMMENT)  # token_type
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
        sargs.state_stack.enter_state(TokenizerState.CHECK_INCLUDE_KW)
    return ret_token


@create_tokenizer_state(
    TokenizerState.CHECK_END_HTML_COMMENT, starts=True, returns=True, cleans=True
)
def state_check_end_html_comment(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_END_HTML_COMMENT tokenizer state

    Returns
    -------
    Token
    """
    ret_token: Optional[Token] = None
    while not sargs.cwrap.check_for_end():
        while sargs.cwrap.current_char != "-":
            sargs.cwrap.advance_pos()
        tok_start = sargs.cwrap.current_idx
        if (
            sargs.cwrap.try_next(next_char="-")
            and sargs.cwrap.try_next(next_char="-")
            and sargs.cwrap.try_next(next_char=">")
        ):
            try:
                sargs.curr_token_gen.send(tok_start)  # slice_start
                sargs.curr_token_gen.send(TokenType.HTML_END_COMMENT)  # token_type
                sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
                sargs.curr_token_gen.send(False)  # debug_info
            except StopIteration as ex:
                ret_token = ex.value
                break
        else:
            del tok_start
    assert ret_token is not None, "Expected token generator to return a Token"
    return ret_token


@create_tokenizer_state(
    TokenizerState.CHECK_HTML_DOCTYPE, starts=True, returns=True, cleans=True
)
def state_check_html_doctype(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_HTML_DOCTYPE tokenizer state

    Returns
    -------
    Token
    """
    # already consumed '<!D'
    tok_start = sargs.cwrap.current_idx - 3
    while not (sargs.cwrap.check_for_end() or sargs.cwrap.current_char == ">"):
        sargs.cwrap.advance_pos()
    sargs.cwrap.assert_next(next_char=">")

    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(tok_start)  # slice_start
        sargs.curr_token_gen.send(TokenType.FILE_TEXT)  # token_type
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
    return ret_token


@create_tokenizer_state(TokenizerState.CHECK_INCLUDE_KW, starts=True)
def state_check_include_kw(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_INCLUDE_KW tokenizer state"""
    sargs.state_stack.enter_state(TokenizerState.CHECK_END_HTML_COMMENT)
    while not sargs.cwrap.check_for_end() and sargs.cwrap.validate_type(
        CharacterType.WS
    ):
        sargs.cwrap.advance_pos()

    inc_start = sargs.cwrap.current_idx
    if (
        sargs.cwrap.try_next(next_char="#")
        and sargs.cwrap.try_next(next_char="i")
        and sargs.cwrap.try_next(next_char="n")
        and sargs.cwrap.try_next(next_char="c")
        and sargs.cwrap.try_next(next_char="l")
        and sargs.cwrap.try_next(next_char="u")
        and sargs.cwrap.try_next(next_char="d")
        and sargs.cwrap.try_next(next_char="e")
    ):
        sargs.curr_token_gen.send(inc_start)  # slice_start
        sargs.curr_token_gen.send(TokenType.INCLUDE_KW)  # token_type
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.state_stack.enter_state(TokenizerState.RETURN_INCLUDE_KW)
    else:
        sargs.state_stack.enter_state(TokenizerState.CANCEL_INCLUDE_KW)


@create_tokenizer_state(TokenizerState.RETURN_INCLUDE_KW, returns=True)
def state_return_include_kw(sargs: StateArgs) -> TokenOpt:
    """Handler for RETURN_INCLUDE_KW tokenizer state

    Returns
    -------
    Token
    """
    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
        sargs.state_stack.enter_state(TokenizerState.CHECK_INCLUDE_TYPE)
    return ret_token


@create_tokenizer_state(TokenizerState.CANCEL_INCLUDE_KW, cleans=True)
def state_cancel_include_kw(sargs: StateArgs) -> TokenOpt:
    """Handler for CANCEL_INCLUDE_KW tokenizer state"""
    sargs.curr_token_gen.close()


@create_tokenizer_state(
    TokenizerState.CHECK_INCLUDE_TYPE, starts=True, returns=True, cleans=True
)
def state_check_include_type(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_INCLUDE_TYPE tokenizer state

    Returns
    -------
    Token
    """
    while not sargs.cwrap.check_for_end() and sargs.cwrap.validate_type(
        CharacterType.WS
    ):
        sargs.cwrap.advance_pos()

    inc_type_kws = {"f": "file", "v": "virtual"}
    assert sargs.cwrap.current_char in inc_type_kws, "Invalid include type"
    kw_start = sargs.cwrap.current_idx
    for kw_char in inc_type_kws[sargs.cwrap.current_char]:
        sargs.cwrap.assert_next(next_char=kw_char)

    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(kw_start)  # slice_start
        sargs.curr_token_gen.send(TokenType.INCLUDE_TYPE)  # token_type
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
        sargs.state_stack.enter_multiple(
            [TokenizerState.RETURN_EQ_SYMBOL, TokenizerState.CHECK_INCLUDE_PATH]
        )
    return ret_token


@create_tokenizer_state(
    TokenizerState.RETURN_EQ_SYMBOL, starts=True, returns=True, cleans=True
)
def state_return_eq_symbol(sargs: StateArgs) -> TokenOpt:
    """Handler for RETURN_EQ_SYMBOL tokenizer state

    Returns
    -------
    Token
    """
    while not sargs.cwrap.check_for_end() and sargs.cwrap.validate_type(
        CharacterType.WS
    ):
        sargs.cwrap.advance_pos()

    eq_start = sargs.cwrap.current_idx
    sargs.cwrap.assert_next(next_char="=")

    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(eq_start)  # slice_start
        sargs.curr_token_gen.send(TokenType.SYMBOL)  # token_type
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
    return ret_token


@create_tokenizer_state(
    TokenizerState.CHECK_INCLUDE_PATH, starts=True, returns=True, cleans=True
)
def state_check_include_path(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_INCLUDE_PATH tokenizer state

    Returns
    -------
    Token
    """
    while not sargs.cwrap.check_for_end() and sargs.cwrap.validate_type(
        CharacterType.WS
    ):
        sargs.cwrap.advance_pos()

    path_start = sargs.cwrap.current_idx
    sargs.cwrap.assert_next(next_char='"')
    while not sargs.cwrap.check_for_end() and sargs.cwrap.current_char != '"':
        # consume path, validate in parser
        sargs.cwrap.advance_pos()
    sargs.cwrap.assert_next(next_char='"')

    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(path_start)  # slice_start
        sargs.curr_token_gen.send(TokenType.INCLUDE_PATH)  # token_type
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
    return ret_token


@create_tokenizer_state(TokenizerState.CHECK_EXHAUSTED)
def state_check_exhausted(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_EXHAUSTED tokenizer state

    If CodeWrapper has not reached the end of the codeblock,
    keep this state on the stack and push CHECK_WHITESPACE
    """
    if not sargs.cwrap.check_for_end():
        sargs.state_stack.persist_state()
        sargs.state_stack.enter_state(TokenizerState.CHECK_DELIM_START)


@create_tokenizer_state(TokenizerState.CHECK_WHITESPACE)
def state_check_whitespace(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_WHITESPACE tokenizer state

    Consumes whitespace and checks for a line continuation

    If CodeWrapper has not reached the end of the codeblock,
    check for either a comment, a newline, or the start of a terminal
    """
    # is this leading whitespace at the beginning of a line?
    whitespace_start = (sargs.cwrap.current_idx - sargs.cwrap.line_start) == 0
    # consume whitespace
    while sargs.cwrap.try_next(next_type=CharacterType.WS):
        pass
    if whitespace_start:
        # code doesn't start until after whitespace
        sargs.cwrap.update_line_code_start()

    # check for line continuation
    if sargs.cwrap.try_next(next_char="_"):
        while sargs.cwrap.try_next(next_type=CharacterType.WS):
            pass
        # optional newline characters
        carriage_return = sargs.cwrap.try_next(next_char="\r")
        line_feed = sargs.cwrap.try_next(next_char="\n")
        # update debug line info
        if carriage_return or line_feed:
            sargs.cwrap.advance_line()
        # check for leading whitespace after line continuation
        sargs.state_stack.persist_state()
        return

    # if check_for_end(), return to CHECK_EXHAUSTED
    # else, check for comments, newlines, or terminals
    if not sargs.cwrap.check_for_end():
        if sargs.cwrap.try_next(next_char="'"):
            # need to consume "'" so that SKIP_COMMENT works the same for 'Rem' comments as well
            sargs.state_stack.enter_state(TokenizerState.SKIP_QUOTE_COMMENT)
        elif sargs.cwrap.current_char in ":\r\n":
            # don't return NEWLINE token if line is all whitespace
            sargs.state_stack.enter_multiple(
                [
                    (
                        TokenizerState.HANDLE_NEWLINE
                        if whitespace_start
                        else TokenizerState.START_NEWLINE
                    ),
                    TokenizerState.CHECK_DELIM_END,
                ]
            )
        elif sargs.cwrap.current_char == "%":
            # let CHECK_DELIM_END handle percent symbol
            sargs.state_stack.enter_state(TokenizerState.CHECK_DELIM_END)
        else:
            sargs.state_stack.enter_state(TokenizerState.START_TERMINAL)


@create_tokenizer_state(TokenizerState.SKIP_QUOTE_COMMENT)
def state_skip_quote_comment(sargs: StateArgs) -> TokenOpt:
    """Handler for SKIP_COMMENT tokenizer state

    Consume the body of a comment

    If CodeWrapper has not reached the end of the codeblock,
    check for a newline
    """
    # does this comment take up the whole line?
    comment_starts_line = (
        sargs.cwrap.current_idx - sargs.cwrap.line_code_start - 1
    ) == 0
    # consume comment
    while not sargs.cwrap.check_for_end() and sargs.cwrap.current_char not in "\r\n":
        sargs.cwrap.advance_pos()
        if sargs.cwrap.try_next(next_char="%") and sargs.cwrap.try_next(next_char=">"):
            sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_DELIM_END)
            return

    # if check_for_end(), return to CHECK_EXHAUSTED
    # else, check for newline
    if not sargs.cwrap.check_for_end():
        if sargs.cwrap.current_char in "\r\n":
            sargs.state_stack.enter_multiple(
                [
                    (
                        TokenizerState.HANDLE_NEWLINE
                        if comment_starts_line
                        else TokenizerState.START_NEWLINE
                    ),
                    TokenizerState.CHECK_DELIM_END,
                ]
            )
        else:
            sargs.state_stack.enter_state(TokenizerState.CHECK_WHITESPACE)


@create_tokenizer_state(TokenizerState.SKIP_REM_COMMENT)
def state_skip_rem_comment(sargs: StateArgs) -> TokenOpt:
    """Handler for SKIP_REM_COMMENT tokenizer state

    Consume the body of a 'Rem' comment
    """
    # does this comment take up the whole line?
    comment_starts_line = (
        sargs.cwrap.current_idx - sargs.cwrap.line_code_start - 3
    ) == 0
    # consume comment
    while not sargs.cwrap.check_for_end() and sargs.cwrap.current_char not in "\r\n":
        sargs.cwrap.advance_pos()
        if sargs.cwrap.try_next(next_char="%") and sargs.cwrap.try_next(next_char="%"):
            sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_DELIM_END)
            return

    # if check_for_end(), return to CHECK_EXHAUSTED
    # else, check for newline
    if not sargs.cwrap.check_for_end():
        if sargs.cwrap.current_char in "\r\n":
            sargs.state_stack.enter_multiple(
                [
                    (
                        TokenizerState.HANDLE_NEWLINE
                        if comment_starts_line
                        else TokenizerState.START_NEWLINE
                    ),
                    TokenizerState.CHECK_DELIM_END,
                ]
            )
        else:
            sargs.state_stack.enter_state(TokenizerState.CHECK_WHITESPACE)


@create_tokenizer_state(TokenizerState.START_NEWLINE, starts=True)
def state_start_newline(sargs: StateArgs) -> TokenOpt:
    """Handler for START_NEWLINE tokenizer state

    Send the NEWLINE token type to the current active token generator,
    and push the following states onto the stack (top to bottom);
    - HANDLE_NEWLINE
    - END_NEWLINE
    """
    sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_start
    sargs.curr_token_gen.send(TokenType.NEWLINE)  # token_type
    sargs.state_stack.enter_multiple(
        [TokenizerState.HANDLE_NEWLINE, TokenizerState.END_NEWLINE]
    )


@create_tokenizer_state(TokenizerState.HANDLE_NEWLINE)
def state_handle_newline(sargs: StateArgs) -> TokenOpt:
    """Handler for HANDLE_NEWLINE tokenizer state

    Consume each successive newline and update debug line info
    """
    while not sargs.cwrap.check_for_end() and sargs.cwrap.current_char in ":\r\n":
        carriage_return = sargs.cwrap.current_char == "\r"
        sargs.cwrap.advance_pos()
        if carriage_return and (sargs.cwrap.current_char == "\n"):
            # "\r\n" should be treated as a single newline
            sargs.cwrap.advance_pos()
        sargs.cwrap.advance_line()


@create_tokenizer_state(TokenizerState.END_NEWLINE, returns=True, cleans=True)
def state_end_newline(sargs: StateArgs) -> TokenOpt:
    """Handler for END_NEWLINE tokenizer state

    Send the end position of the processed NEWLINE token to the current active token generator
    and disable debug line info output

    Returns
    -------
    Token

    Raises
    ------
    AssertionError
    """
    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(False)  # debug_info
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
    return ret_token


@create_tokenizer_state(TokenizerState.START_TERMINAL, starts=True)
def state_start_terminal(sargs: StateArgs) -> TokenOpt:
    """Handler for START_TERMINAL tokenizer state

    Determine the current token type by examining the current character

    If the token type cannot be determined, the current character is treated as a SYMBOL token
    """
    sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_start

    # terminals with known starting characters
    terminal_begin: dict[str, TokenizerState] = {
        ".": TokenizerState.START_DOT,
        "[": TokenizerState.START_ID_ESCAPE,
        '"': TokenizerState.START_STRING,
        "&": TokenizerState.START_AMP,
        "#": TokenizerState.START_DATE,
    }

    # try to determine token type, first compare against character sets
    if sargs.cwrap.validate_type(CharacterType.LETTER):
        sargs.state_stack.enter_state(TokenizerState.START_ID)
    elif sargs.cwrap.validate_type(CharacterType.DIGIT):
        sargs.state_stack.enter_state(TokenizerState.START_NUMBER)
    else:
        try:
            # try to do an exact match
            sargs.state_stack.enter_state(terminal_begin[sargs.cwrap.current_char])
        except KeyError:
            # return as symbol
            sargs.cwrap.advance_pos()  # consume symbol
            sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_SYMBOL)


@create_tokenizer_state(TokenizerState.END_TERMINAL, returns=True, cleans=True)
def state_end_terminal(sargs: StateArgs) -> TokenOpt:
    """Handler for END_TERMINAL tokenizer state

    Send the end position of the processed token to the current active token generator
    along with debug line info

    Returns
    -------
    Token

    Raises
    ------
    AssertionError
    """
    ret_token: Optional[Token] = None
    try:
        sargs.curr_token_gen.send(sargs.cwrap.current_idx)  # slice_end
        sargs.curr_token_gen.send(True)  # debug_info
        sargs.curr_token_gen.send(sargs.cwrap.line_no)  # line_no
        sargs.curr_token_gen.send(sargs.cwrap.line_start)  # line_start
    except StopIteration as ex:
        ret_token = ex.value
    finally:
        assert ret_token is not None, "Expected token generator to return a Token"
        sargs.state_stack.enter_state(TokenizerState.CHECK_DELIM_END)
    return ret_token


@create_tokenizer_state(TokenizerState.CONSTRUCT_SYMBOL)
def state_construct_symbol(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_SYMBOL tokenizer state

    Send the SYMBOL token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.SYMBOL)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.START_DOT)
def state_start_dot(sargs: StateArgs) -> TokenOpt:
    """Handler for START_DOT tokenizer state

    Consume a '.' character and determine the appropriate token type

    If the type is not a dotted IDENTIFIER or a LITERAL_FLOAT,
    the '.' character is treated as a SYMBOL token
    """
    sargs.cwrap.assert_next(next_char=".")
    if sargs.cwrap.current_char == "[":
        sargs.state_stack.enter_state(TokenizerState.START_DOT_ID_ESCAPE)
    elif sargs.cwrap.validate_type(CharacterType.LETTER):
        sargs.state_stack.enter_state(TokenizerState.START_DOT_ID)
    elif sargs.cwrap.validate_type(CharacterType.DIGIT):
        sargs.state_stack.enter_multiple(
            [
                # already consumed '.'
                # send directly to PROCESS_NUMBER_CHUNK instead of CHECK_FLOAT_DEC_PT
                TokenizerState.PROCESS_NUMBER_CHUNK,
                TokenizerState.CHECK_FLOAT_SCI_E,
                TokenizerState.CONSTRUCT_FLOAT,
            ]
        )
    else:
        # return as symbol
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_SYMBOL)


@create_tokenizer_state(TokenizerState.START_AMP)
def state_start_amp(sargs: StateArgs) -> TokenOpt:
    """Handler for START_AMP tokenizer state

    Consume a '&' character and determine the appropriate token type

    If the type is not a LITERAL_HEX or a LITERAL_OCT,
    the '&' character is treated as a SYMBOL token
    """
    sargs.cwrap.assert_next(next_char="&")
    if sargs.cwrap.try_next(next_char="H"):
        sargs.state_stack.enter_state(TokenizerState.START_HEX)
    elif sargs.cwrap.validate_type(CharacterType.OCT_DIGIT):
        sargs.state_stack.enter_state(TokenizerState.START_OCT)
    else:
        # return as symbol
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_SYMBOL)


@create_tokenizer_state(TokenizerState.START_HEX)
def state_start_hex(sargs: StateArgs) -> TokenOpt:
    """Handler for START_HEX tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_HEX
    - CHECK_END_AMP
    - CONSTRUCT_HEX
    """
    # leading 'H' already consumed by START_AMP
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_HEX,
            TokenizerState.CHECK_END_AMP,
            TokenizerState.CONSTRUCT_HEX,
        ]
    )


@create_tokenizer_state(TokenizerState.START_OCT)
def state_start_oct(sargs: StateArgs) -> TokenOpt:
    """Handler for START_OCT tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_HEX
    - CHECK_END_AMP
    - CONSTRUCT_OCT
    """
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_OCT,
            TokenizerState.CHECK_END_AMP,
            TokenizerState.CONSTRUCT_OCT,
        ]
    )


@create_tokenizer_state(TokenizerState.PROCESS_HEX)
def state_process_hex(sargs: StateArgs) -> TokenOpt:
    """Handler for PROCESS_HEX tokenizer state

    Consume a block of one or more HEX_DIGIT characters
    """
    # need at least one hex digit
    if sargs.cwrap.assert_next(next_type=CharacterType.HEX_DIGIT):
        # not at end of codeblock
        while sargs.cwrap.try_next(next_type=CharacterType.HEX_DIGIT):
            pass


@create_tokenizer_state(TokenizerState.PROCESS_OCT)
def state_process_oct(sargs: StateArgs) -> TokenOpt:
    """Handler for PROCESS_OCT tokenizer state

    Consume a block of one or more OCT_DIGIT characters
    """
    # need at least one oct digit
    if sargs.cwrap.assert_next(next_type=CharacterType.OCT_DIGIT):
        # not at end of codeblock
        while sargs.cwrap.try_next(next_type=CharacterType.OCT_DIGIT):
            pass


@create_tokenizer_state(TokenizerState.CHECK_END_AMP)
def state_check_end_amp(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_END_AMP tokenizer state

    Consume an optional '&' character at the end of a LITERAL_HEX or LITERAL_OCT token
    """
    sargs.cwrap.try_next(next_char="&")


@create_tokenizer_state(TokenizerState.CONSTRUCT_HEX)
def state_construct_hex(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_HEX tokenizer state

    Send the LITERAL_HEX token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.LITERAL_HEX)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.CONSTRUCT_OCT)
def state_construct_oct(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_OCT tokenizer state

    Send the LITERAL_OCT token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.LITERAL_OCT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.START_ID)
def state_start_id(sargs: StateArgs) -> TokenOpt:
    """Handler for START_ID tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_ID
    - CHECK_ID_REM
    """
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_ID,
            TokenizerState.CHECK_ID_REM,
        ]
    )


@create_tokenizer_state(TokenizerState.START_DOT_ID)
def state_start_dot_id(sargs: StateArgs) -> TokenOpt:
    """Handler for START_DOT_ID tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_ID
    - CHECK_DOT_ID_REM
    """
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_ID, TokenizerState.CHECK_DOT_ID_REM]
    )


@create_tokenizer_state(TokenizerState.START_ID_ESCAPE)
def state_start_id_escape(sargs: StateArgs) -> TokenOpt:
    """Handler for START_ID_ESCAPE tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_ID_ESCAPE
    - CHECK_END_DOT
    """
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_ID_ESCAPE, TokenizerState.CHECK_END_DOT]
    )


@create_tokenizer_state(TokenizerState.START_DOT_ID_ESCAPE)
def state_start_dot_id_escape(sargs: StateArgs) -> TokenOpt:
    """Handler for START_DOT_ID_ESCAPE tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_ID_ESCAPE
    - CHECK_DOT_END_DOT
    """
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_ID_ESCAPE, TokenizerState.CHECK_DOT_END_DOT]
    )


@create_tokenizer_state(TokenizerState.PROCESS_ID)
def state_process_id(sargs: StateArgs) -> TokenOpt:
    """Handler for PROCESS_ID tokenizer state

    Consume a LETTER and an optional block of ID_TAIL characters
    """
    sargs.cwrap.assert_next(next_type=CharacterType.LETTER)
    while sargs.cwrap.try_next(next_type=CharacterType.ID_TAIL):
        pass


@create_tokenizer_state(TokenizerState.PROCESS_ID_ESCAPE)
def state_process_id_escape(sargs: StateArgs) -> TokenOpt:
    """Handler for PROCESS_ID_ESCAPE tokenizer state

    Consume a '[' character, an optional block of ID_NAME_CHAR characters, and a ']' character
    """
    sargs.cwrap.assert_next(next_char="[")
    while sargs.cwrap.try_next(next_type=CharacterType.ID_NAME_CHAR):
        pass
    sargs.cwrap.assert_next(next_char="]")


@create_tokenizer_state(TokenizerState.CHECK_END_DOT)
def state_check_end_dot(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_END_DOT tokenizer state

    If the current character is a '.',
    consume it and push the CONSTRUCT_ID_DOT state onto the stack;
    otherwise, push CONSTRUCT_ID
    """
    if sargs.cwrap.try_next(next_char="."):
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_ID_DOT)
    else:
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_ID)


@create_tokenizer_state(TokenizerState.CHECK_DOT_END_DOT)
def state_check_dot_end_dot(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_DOT_END_DOT tokenizer state

    If the current character is a '.',
    consume it and push the CONSTRUCT_DOT_ID_DOT state onto the stack;
    otherwise, push CONSTRUCT_DOT_ID
    """
    if sargs.cwrap.try_next(next_char="."):
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_DOT_ID_DOT)
    else:
        sargs.state_stack.enter_state(TokenizerState.CONSTRUCT_DOT_ID)


@create_tokenizer_state(TokenizerState.CHECK_ID_REM)
def state_check_id_rem(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_ID_REM tokenizer state

    If the processed normal identifier is a case-insensitive variant of 'Rem',
    treat the current section of the code as a comment
    and push the following states onto the stack (top to bottom):
    - CANCEL_ID
    - SKIP_COMMENT

    Otherwise, push CHECK_END_DOT
    """
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
                TokenizerState.SKIP_REM_COMMENT,
            ]
        )
    else:
        sargs.state_stack.enter_state(TokenizerState.CHECK_END_DOT)


@create_tokenizer_state(TokenizerState.CHECK_DOT_ID_REM)
def state_check_dot_id_rem(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_DOT_ID_REM tokenizer state

    Verify that the current dotted identifier is not a case-insensitive variant of '.Rem'
    and push the CHECK_DOT_END_DOT state onto the stack

    Raises
    ------
    AssertionError
    """
    rem_end = sargs.cwrap.current_idx
    rem_start = rem_end - 3
    assert not (
        (rem_start > 0)
        and ("rem" in sargs.cwrap.codeblock[rem_start:rem_end].casefold())
    ), "Illegal use of '.' symbol; cannot appear before Rem"
    sargs.state_stack.enter_state(TokenizerState.CHECK_DOT_END_DOT)


@create_tokenizer_state(TokenizerState.CANCEL_ID, cleans=True)
def state_cancel_id(sargs: StateArgs) -> TokenOpt:
    """Handler for CANCEL_ID tokenizer state

    The current identifier was actually a 'Rem' comment,
    so close the current active token generator early
    """
    sargs.curr_token_gen.close()


@create_tokenizer_state(TokenizerState.CONSTRUCT_ID)
def state_construct_id(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_ID tokenizer state

    Send the IDENTIFIER token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.IDENTIFIER)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.CONSTRUCT_DOT_ID)
def state_construct_dot_id(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_DOT_ID tokenizer state

    Send the IDENTIFIER_DOTID token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.IDENTIFIER_DOTID)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.CONSTRUCT_ID_DOT)
def state_construct_id_dot(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_ID_DOT tokenizer state

    Send the IDENTIFIER_IDDOT token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.IDENTIFIER_IDDOT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.CONSTRUCT_DOT_ID_DOT)
def state_construct_dot_id_dot(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_DOT_ID_DOT tokenizer state

    Send the IDENTIFIER_DOTIDDOT token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.IDENTIFIER_DOTIDDOT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.START_NUMBER)
def state_start_number(sargs: StateArgs) -> TokenOpt:
    """Handler for START_NUMBER tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_NUMBER_CHUNK
    - VERIFY_INT
    """
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_NUMBER_CHUNK, TokenizerState.VERIFY_INT]
    )


@create_tokenizer_state(TokenizerState.PROCESS_NUMBER_CHUNK)
def state_process_number_chunk(sargs: StateArgs) -> TokenOpt:
    """Handler for PROCESS_NUMBER_CHUNK tokenizer state

    Consume a block of one or more DIGIT characters
    """
    # need at least one digit
    if sargs.cwrap.assert_next(next_type=CharacterType.DIGIT):
        while sargs.cwrap.try_next(next_type=CharacterType.DIGIT):
            pass


@create_tokenizer_state(TokenizerState.VERIFY_INT)
def state_verify_int(sargs: StateArgs) -> TokenOpt:
    """Handler for VERIFY_INT tokenizer state

    Check for any indication that the current token might be a LITERAL_FLOAT

    If not, push the CONSTRUCT_INT state onto the stack
    """
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


@create_tokenizer_state(TokenizerState.CHECK_FLOAT_DEC_PT)
def state_check_float_dec_pt(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_FLOAT_DEC_PT tokenizer state

    If the current character is a '.',
    consume it and push the PROCESS_NUMBER_CHUNK onto the stack
    """
    if sargs.cwrap.try_next(next_char="."):
        sargs.state_stack.enter_state(TokenizerState.PROCESS_NUMBER_CHUNK)


@create_tokenizer_state(TokenizerState.CHECK_FLOAT_SCI_E)
def state_check_float_sci_e(sargs: StateArgs) -> TokenOpt:
    """Handler for CHECK_FLOAT_SCI_E tokenizer state

    If the current character is a '.',
    consume it and an optional '-' or '+' that might follow,
    and push the PROCESS_NUMBER_CHUNK state onto the stack
    """
    if sargs.cwrap.try_next(next_char="E"):
        if not sargs.cwrap.check_for_end() and sargs.cwrap.current_char in "+-":
            sargs.cwrap.advance_pos()  # consume '-' or '+'
        sargs.state_stack.enter_state(TokenizerState.PROCESS_NUMBER_CHUNK)


@create_tokenizer_state(TokenizerState.CONSTRUCT_INT)
def state_construct_int(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_INT tokenizer state

    Send the LITERAL_INT token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.LITERAL_INT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.CONSTRUCT_FLOAT)
def state_construct_float(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_FLOAT tokenizer state

    Send the LITERAL_FLOAT token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.LITERAL_FLOAT)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.START_STRING)
def state_start_string(sargs: StateArgs) -> TokenOpt:
    """Handler for START_STRING tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_STRING
    - VERIFY_STRING_END
    - CONSTRUCT_STRING
    """
    sargs.state_stack.enter_multiple(
        [
            TokenizerState.PROCESS_STRING,
            TokenizerState.VERIFY_STRING_END,
            TokenizerState.CONSTRUCT_STRING,
        ]
    )


@create_tokenizer_state(TokenizerState.PROCESS_STRING)
def state_process_string(sargs: StateArgs) -> TokenOpt:
    """Handler for PROCESS_STRING tokenizer state

    Consume a '"' character, and optional block of STRING_CHAR, and another '"' character
    """
    sargs.cwrap.assert_next(next_char='"')
    while sargs.cwrap.try_next(next_type=CharacterType.STRING_CHAR):
        pass
    sargs.cwrap.assert_next(next_char='"')


@create_tokenizer_state(TokenizerState.VERIFY_STRING_END)
def state_verify_string_end(sargs: StateArgs) -> TokenOpt:
    """Handler for VERIFY_STRING_END tokenizer state

    Verify that the previous '"' is not escaped by another '"'

    If it is escaped, keep this state on the stack and push PROCESS_STRING
    """
    if sargs.cwrap.current_char == '"':
        # double quote is escaped
        sargs.state_stack.persist_state()
        sargs.state_stack.enter_state(TokenizerState.PROCESS_STRING)


@create_tokenizer_state(TokenizerState.CONSTRUCT_STRING)
def state_construct_string(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_STRING tokenizer state

    Send the LITERAL_STRING token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.LITERAL_STRING)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)


@create_tokenizer_state(TokenizerState.START_DATE)
def state_start_date(sargs: StateArgs) -> TokenOpt:
    """Handler for START_DATE tokenizer state

    Push the following states onto the stack (top to bottom):
    - PROCESS_DATE
    - CONSTRUCT_DATE
    """
    sargs.state_stack.enter_multiple(
        [TokenizerState.PROCESS_DATE, TokenizerState.CONSTRUCT_DATE]
    )


@create_tokenizer_state(TokenizerState.PROCESS_DATE)
def state_process_date(sargs: StateArgs) -> TokenOpt:
    """Handler for PROCESS_DATE tokenizer state

    Consume a '#' character, a block of one or more DATE_CHAR, and another '#' character
    """
    sargs.cwrap.assert_next(next_char="#")
    # need at least one DATE_CHAR
    sargs.cwrap.assert_next(next_type=CharacterType.DATE_CHAR)
    while sargs.cwrap.try_next(next_type=CharacterType.DATE_CHAR):
        pass
    sargs.cwrap.assert_next(next_char="#")


@create_tokenizer_state(TokenizerState.CONSTRUCT_DATE)
def state_construct_date(sargs: StateArgs) -> TokenOpt:
    """Handler for CONSTRUCT_DATE tokenizer state

    Send the LITERAL_DATE token type to the current active token generator
    and push the END_TERMINAL state onto the stack
    """
    sargs.curr_token_gen.send(TokenType.LITERAL_DATE)  # token_type
    sargs.state_stack.enter_state(TokenizerState.END_TERMINAL)
