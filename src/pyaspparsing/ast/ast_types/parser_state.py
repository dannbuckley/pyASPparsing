"""parser_state module"""

import enum
import typing
import attrs


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class GlobalState(enum.IntEnum):
    """Enumeration of valid global statement parser states"""

    CHECK_EXHAUSTED = enum.auto()

    # === GLOBAL STATEMENTS
    START_GLOBAL_STMT = enum.auto()
    END_GLOBAL_STMT = enum.auto()

    START_OPTION_EXPLICIT = enum.auto()

    CHECK_ACCESS_MODIFIER = enum.auto()
    SET_ACCESS_NONE = enum.auto()
    SET_ACCESS_PRIVATE = enum.auto()
    SET_ACCESS_PUBLIC = enum.auto()
    SET_ACCESS_PUBLIC_DEFAULT = enum.auto()

    START_CLASS_DECL = enum.auto()
    START_FIELD_DECL = enum.auto()
    START_CONST_DECL = enum.auto()
    START_SUB_DECL = enum.auto()
    START_FUNCTION_DECL = enum.auto()

    # === BLOCK STATEMENTS
    START_BLOCK_STMT = enum.auto()
    CHECK_BLOCK_INLINE_NEWLINE = enum.auto()

    START_VAR_DECL = enum.auto()
    START_REDIM_STMT = enum.auto()
    START_IF_STMT = enum.auto()
    START_WITH_STMT = enum.auto()
    START_SELECT_STMT = enum.auto()
    START_LOOP_STMT = enum.auto()
    START_FOR_STMT = enum.auto()

    # === INLINE STATEMENTS
    START_INLINE_STMT = enum.auto()

    START_ASSIGN_STMT = enum.auto()
    START_CALL_STMT = enum.auto()
    START_ERROR_STMT = enum.auto()
    START_EXIT_STMT = enum.auto()
    START_ERASE_STMT = enum.auto()
    START_SUBCALL_STMT = enum.auto()


@attrs.define
class GlobalStateStack:
    """Stack implementation to handle transitioning between parser states"""

    state_stack: typing.List[GlobalState] = attrs.field(
        default=attrs.Factory(list), init=False
    )
    _prev_state: typing.Optional[int] = attrs.field(default=None, init=False)
    _leave_on_next: bool = attrs.field(default=False, init=False)

    def __iter__(self):
        if len(self.state_stack) > 0:
            raise RuntimeError(
                "Called GlobalStateStack.__iter__() but stack is not empty"
            )
        self.state_stack.append(GlobalState.CHECK_EXHAUSTED)
        self._prev_state = None
        # _prev_state does not exist until first __next__() call
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
    def current_state(self) -> typing.Optional[GlobalState]:
        """If the stack is empty, returns None;
        otherwise, returns the state at the top of the stack"""
        try:
            return self.state_stack[-1]
        except IndexError:
            return None

    def enter_state(self, state: GlobalState):
        """Push a new state onto the stack

        Parameters
        ----------
        state : GlobalState
        """
        self.state_stack.append(state)

    def enter_multiple(
        self, states: typing.Iterable[GlobalState], top_first: bool = True
    ):
        """Push multiple new states onto the stack

        Parameters
        ----------
        states : Iterable[GlobalState]
        top_first : bool, default=True
            If True, states are pushed in reverse order
        """
        self.state_stack.extend(states[:: -1 if top_first else 1])

    def persist_state(self):
        """Disable `_leave_on_next` flag for the next iteration

        This keeps the current state on the stack
        """
        self._leave_on_next = False
