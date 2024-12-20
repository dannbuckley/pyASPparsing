"""tokenizer_state module"""

import enum
from typing import Optional, Iterable
import attrs


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class TokenizerState(enum.IntEnum):
    """Enumeration of valid tokenizer states"""

    # directives
    # https://learn.microsoft.com/en-us/previous-versions/iis/6.0-sdk/ms524741(v=vs.90)#using-asp-directives
    # scripting <% %>
    # output directive <%= %>
    # processing directive <%@ %>
    CHECK_DELIM_START = enum.auto()
    CHECK_DELIM_END = enum.auto()
    RETURN_PERC_SYMBOL = enum.auto()
    CONSTRUCT_DELIM_SCRIPT = enum.auto()
    CONSTRUCT_DELIM_PROCESSING = enum.auto()
    CONSTRUCT_DELIM_OUTPUT = enum.auto()
    CONSTRUCT_DELIM_END = enum.auto()
    END_DELIM = enum.auto()

    # generic text not wrapped by ASP delimiters
    START_FILE_TEXT = enum.auto()
    START_FILE_TEXT_DELAYED = enum.auto()
    CONSUME_FILE_TEXT = enum.auto()
    VERIFY_FILE_TEXT_END = enum.auto()
    END_FILE_TEXT = enum.auto()

    # file inclusion
    # https://learn.microsoft.com/en-us/previous-versions/iis/6.0-sdk/ms524876(v=vs.90)
    CHECK_HTML_COMMENT = enum.auto()
    CHECK_END_HTML_COMMENT = enum.auto()
    CHECK_HTML_DOCTYPE = enum.auto()  # treat a <!DOCTYPE ...> as FILE_TEXT
    CHECK_INCLUDE_KW = enum.auto()
    RETURN_INCLUDE_KW = enum.auto()
    CANCEL_INCLUDE_KW = enum.auto()
    CHECK_INCLUDE_TYPE = enum.auto()
    RETURN_EQ_SYMBOL = enum.auto()
    CHECK_INCLUDE_PATH = enum.auto()

    # housekeeping states
    CHECK_EXHAUSTED = enum.auto()
    CHECK_WHITESPACE = enum.auto()
    SKIP_QUOTE_COMMENT = enum.auto()
    SKIP_REM_COMMENT = enum.auto()

    # NEWLINE token
    START_NEWLINE = enum.auto()
    HANDLE_NEWLINE = enum.auto()
    END_NEWLINE = enum.auto()

    # helper states for remaining token types
    START_TERMINAL = enum.auto()
    END_TERMINAL = enum.auto()

    # SYMBOL token
    CONSTRUCT_SYMBOL = enum.auto()

    # dotted IDENTIFIER_*, LITERAL_FLOAT, or SYMBOL
    START_DOT = enum.auto()

    # LITERAL_HEX, LITERAL_OCT, or SYMBOL
    START_AMP = enum.auto()
    START_HEX = enum.auto()
    START_OCT = enum.auto()
    PROCESS_HEX = enum.auto()
    PROCESS_OCT = enum.auto()
    CHECK_END_AMP = enum.auto()
    CONSTRUCT_HEX = enum.auto()
    CONSTRUCT_OCT = enum.auto()

    # IDENTIFIER_* tokens
    # if normal identifier == 'Rem', identifier is treated as a comment and skipped
    START_ID = enum.auto()
    START_DOT_ID = enum.auto()
    START_ID_ESCAPE = enum.auto()
    START_DOT_ID_ESCAPE = enum.auto()
    PROCESS_ID = enum.auto()
    PROCESS_ID_ESCAPE = enum.auto()
    CHECK_END_DOT = enum.auto()
    CHECK_DOT_END_DOT = enum.auto()
    CHECK_ID_REM = enum.auto()
    CHECK_DOT_ID_REM = enum.auto()
    CANCEL_ID = enum.auto()
    CONSTRUCT_ID = enum.auto()
    CONSTRUCT_DOT_ID = enum.auto()
    CONSTRUCT_ID_DOT = enum.auto()
    CONSTRUCT_DOT_ID_DOT = enum.auto()

    # LITERAL_INT and LITERAL_FLOAT tokens
    START_NUMBER = enum.auto()
    PROCESS_NUMBER_CHUNK = enum.auto()
    VERIFY_INT = enum.auto()
    CHECK_FLOAT_DEC_PT = enum.auto()
    CHECK_FLOAT_SCI_E = enum.auto()
    CONSTRUCT_INT = enum.auto()
    CONSTRUCT_FLOAT = enum.auto()

    # LITERAL_STRING token
    START_STRING = enum.auto()
    PROCESS_STRING = enum.auto()
    VERIFY_STRING_END = enum.auto()
    CONSTRUCT_STRING = enum.auto()

    # LITERAL_DATE token
    START_DATE = enum.auto()
    PROCESS_DATE = enum.auto()
    CONSTRUCT_DATE = enum.auto()


@attrs.define
class TokenizerStateStack:
    """Stack implementation to handle transitioning between tokenizer states"""

    state_stack: list[TokenizerState] = attrs.field(
        default=attrs.Factory(list), init=False
    )
    _prev_state: Optional[int] = attrs.field(default=None, init=False)
    _leave_on_next: bool = attrs.field(default=False, init=False)

    def __iter__(self):
        if len(self.state_stack) > 0:
            raise RuntimeError(
                "Called TokenizerStateStack.__iter__() but stack is not empty"
            )
        self.state_stack.append(TokenizerState.CHECK_EXHAUSTED)
        self._prev_state = None
        # _prev_state does not exist yet
        # use _leave_on_next=False for first iteration
        self._leave_on_next = False
        return self

    def __next__(self):
        if self._leave_on_next:
            try:
                self.state_stack.pop(self._prev_state)
            except IndexError as ex:
                raise StopIteration from ex
            finally:
                if len(self.state_stack) == 0:
                    raise StopIteration
        else:
            # reset to True to encourage use-once states and prevent infinite looping
            self._leave_on_next = True
        self._prev_state = len(self.state_stack) - 1
        return self.current_state

    @property
    def current_state(self) -> Optional[TokenizerState]:
        """If the stack is empty, returns None;
        otherwise, returns the state at the top of the stack"""
        try:
            return self.state_stack[-1]
        except IndexError:
            return None

    def enter_state(self, state: TokenizerState):
        """Push a new state onto the stack

        Parameters
        ----------
        state : TokenizerState
        """
        self.state_stack.append(state)

    def enter_multiple(
        self, states: Iterable[TokenizerState], top_first: bool = True
    ):
        """Push multiple new states onto the stack

        Parameters
        ----------
        states : Iterable[TokenizerState]
        top_first : bool, default=True
            If True, states are pushed in reverse order
        """
        self.state_stack.extend(states[:: -1 if top_first else 1])

    def persist_state(self):
        """Disable `_leave_on_next` flag for the next iteration

        This keeps the current state on the stack
        """
        self._leave_on_next = False
