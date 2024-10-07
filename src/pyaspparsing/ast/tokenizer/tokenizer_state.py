"""tokenizer_state module"""

import enum
import typing
import attrs


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class TokenizerState(enum.IntEnum):
    """"""

    # if iterator not exhausted, push CHECK_WHITESPACE
    # else, raise StopIteration
    CHECK_EXHAUSTED = enum.auto()
    # handle any whitespace or line continuation
    # update debug line info if necessary
    # pop this state
    # if current character == "'", push SKIP_COMMENT
    # elif current character in ":\r\n", push START_NEWLINE
    # else, push START_TERMINAL
    CHECK_WHITESPACE = enum.auto()

    # consume comment and pop this state
    # if end of comment == end of codeblock,
    #   continue to next iteration
    #   (CHECK_EXHAUSTED should be at bottom of stack)
    # if end of comment == newline character, push CHECK_NEWLINE
    SKIP_COMMENT = enum.auto()

    # if current character not ':', CR, or LF, pop this state and push HANDLE_TERMINAL
    # consume each successive instance of ':', CR, LF, or CR LF
    # update debug line info accordingly
    # pop this state and continue to next iteration
    HANDLE_NEWLINE = enum.auto()
    START_NEWLINE = enum.auto()
    END_NEWLINE = enum.auto()

    # set start_term = _pos_idx
    # pop this state
    # push END_TERMINAL
    # if current character == ".", push START_DOT
    # elif current character == LETTER, push START_ID
    # elif current character == "[", push START_ID_ESCAPE
    # elif current character == '"', push START_STRING
    # elif current character == DIGIT, push START_NUMBER
    # elif current character == "&", push START_AMP
    # elif current character == "#", push START_DATE
    # else, push CONSTRUCT_SYMBOL
    START_TERMINAL = enum.auto()
    # pop this state and return Token object
    END_TERMINAL = enum.auto()

    # construct SYMBOL Token object
    CONSTRUCT_SYMBOL = enum.auto()

    # pop this state
    # if current character == LETTER,
    #   set dot_start = True and push START_ID
    # elif current character == "[",
    #   set dot_start = True and push START_ID_ESCAPE
    # elif current character == DIGIT,
    #   push START_FLOAT_DEC_PT
    START_DOT = enum.auto()

    # consume "&"
    # pop this state
    # if current character == "H", push START_HEX
    # elif current character == OCT_DIGIT, push START_OCT
    # else, push CONSTRUCT_SYMBOL
    START_AMP = enum.auto()
    START_HEX = enum.auto()
    START_OCT = enum.auto()
    PROCESS_HEX = enum.auto()
    PROCESS_OCT = enum.auto()
    CHECK_END_AMP = enum.auto()
    CONSTRUCT_HEX = enum.auto()
    CONSTRUCT_OCT = enum.auto()

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

    START_NUMBER = enum.auto()
    PROCESS_NUMBER_CHUNK = enum.auto()
    VERIFY_INT = enum.auto()
    CHECK_FLOAT_DEC_PT = enum.auto()
    CHECK_FLOAT_SCI_E = enum.auto()
    CONSTRUCT_INT = enum.auto()
    CONSTRUCT_FLOAT = enum.auto()

    START_STRING = enum.auto()
    PROCESS_STRING = enum.auto()
    VERIFY_STRING_END = enum.auto()
    CONSTRUCT_STRING = enum.auto()

    # set tok_type = LITERAL_DATE
    # consume the first DATE_CHAR
    # pop this state and push PROCESS_DATE
    START_DATE = enum.auto()
    # if current character == DATE_CHAR, do nothing
    # otherwise, pop this state and push CONSTRUCT_DATE
    PROCESS_DATE = enum.auto()
    # construct LITERAL_DATE Token object
    CONSTRUCT_DATE = enum.auto()


@attrs.define
class TokenizerStateStack:
    """"""

    state_stack: typing.List[TokenizerState] = attrs.field(
        default=attrs.Factory(list), init=False
    )
    _prev_state: typing.Optional[int] = attrs.field(default=None, init=False)
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
    def current_state(self) -> typing.Optional[TokenizerState]:
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
        self, states: typing.Iterable[TokenizerState], top_first: bool = True
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
