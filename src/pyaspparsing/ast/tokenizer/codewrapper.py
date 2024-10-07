"""codewrapper module"""

# pylint: disable=R0911

import enum
import sys
import traceback
import typing

import attrs

__all__ = ["CharacterType", "CodeWrapper"]


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class CharacterType(enum.IntEnum):
    """Enumeration of valid character types"""

    LETTER = enum.auto()
    DIGIT = enum.auto()
    STRING_CHAR = enum.auto()
    DATE_CHAR = enum.auto()
    ID_NAME_CHAR = enum.auto()
    HEX_DIGIT = enum.auto()
    OCT_DIGIT = enum.auto()
    WS = enum.auto()
    ID_TAIL = enum.auto()


@attrs.define
class CodeWrapper:
    """
    Attributes
    ----------
    codeblock : str
    suppress_error : bool, default=True
    output_file : IO, default=sys.stdout

    Methods
    -------
    check_for_end()
    try_next(*, next_char, next_type)
    assert_next(*, next_char, next_type)
    """

    codeblock: str
    suppress_error: bool = attrs.field(default=True)
    output_file: typing.IO = attrs.field(default=sys.stdout)

    # iterating through codeblock
    _code_iter: typing.Optional[typing.Iterator[str]] = attrs.field(
        default=None, init=False
    )
    _pos_char: typing.Optional[str] = attrs.field(default=None, init=False)
    _pos_idx: typing.Optional[int] = attrs.field(default=None, init=False)

    # debug line info
    line_no: typing.Optional[int] = attrs.field(default=None, init=False)
    line_start: typing.Optional[int] = attrs.field(default=None, init=False)

    @property
    def current_char(self):
        """The current character in the codeblock"""
        return self._pos_char

    @property
    def current_idx(self):
        """The index of the current character in the codeblock"""
        return self._pos_idx

    def check_for_end(self) -> bool:
        """
        Returns
        -------
        bool

        Raises
        ------
        RuntimeError
        """
        if self._code_iter is None:
            raise RuntimeError(
                "check_for_end() cannot be used outside of a runtime context"
            )
        return (self._pos_char is None) and (self._pos_idx is not None)

    def __enter__(self) -> typing.Self:
        if not (
            self._code_iter is None and self._pos_char is None and self._pos_idx is None
        ):
            raise RuntimeError(
                "CodeWrapper instance has already been entered, must exit first"
            )
        self._code_iter = iter(self.codeblock)
        # preload first character
        self._pos_char = next(self._code_iter, None)
        self._pos_idx = 0

        # initialize debug line info
        self.line_no = 1
        self.line_start = 0
        return self

    def __exit__(self, exc_type, exc_val: BaseException, tb) -> bool:
        if not (exc_type is None and exc_val is None and tb is None):
            print("CodeWrapper encountered an error!", file=self.output_file)
            print("Current character:", repr(self._pos_char), file=self.output_file)
            print("Exception type:", exc_type, file=self.output_file)
            print("Exception value:", str(exc_val), file=self.output_file)
            print("Traceback:", file=self.output_file)
            traceback.print_tb(tb, file=self.output_file)
        self._code_iter = None
        self._pos_char = None
        self._pos_idx = None
        self.line_no = None
        self.line_start = None
        return self.suppress_error

    def advance_pos(self) -> bool:
        """
        Returns
        -------
        bool
        """
        if self.check_for_end():
            # codeblock already exhausted
            return False
        self._pos_char = next(self._code_iter, None)
        self._pos_idx += 1
        return self._pos_char is not None

    def advance_line(self):
        """Update debug line info"""
        if self.line_no is not None and self.line_start is not None:
            self.line_no += 1
            self.line_start = self._pos_idx

    def validate_type(self, char_type: CharacterType) -> bool:
        """
        Parameters
        ----------
        char_type : CharacterType

        Returns
        -------
        bool

        Raises
        ------
        RuntimeError
        """
        if (
            (self._code_iter is None)
            and (self._pos_char is None)
            and (self._pos_idx is None)
        ):
            raise RuntimeError(
                "validate_type() cannot be used outside of a runtime context"
            )
        if self.check_for_end():
            return False
        # http://www.goldparser.org/doc/grammars/index.htm
        # predefined character sets -> "Printable"
        printable: typing.Set[int] = set([0xA0, *range(0x20, 0x7F)])
        match char_type:
            case CharacterType.LETTER:
                return self._pos_char.isalpha()
            case CharacterType.DIGIT:
                return self._pos_char.isnumeric()
            case CharacterType.STRING_CHAR:
                return self._pos_char != '"'
            case CharacterType.DATE_CHAR:
                return ord(self._pos_char) in printable and self._pos_char != "#"
            case CharacterType.ID_NAME_CHAR:
                return ord(self._pos_char) in printable and self._pos_char not in "[]"
            case CharacterType.HEX_DIGIT:
                return (
                    self._pos_char.isnumeric() or self._pos_char.casefold() in "abcdef"
                )
            case CharacterType.OCT_DIGIT:
                return self._pos_char in "01234567"
            case CharacterType.WS:
                return self._pos_char.isspace() and self._pos_char not in "\r\n"
            case CharacterType.ID_TAIL:
                return self._pos_char.isalnum() or self._pos_char == "_"

    def try_next(
        self,
        *,
        next_char: typing.Optional[str] = None,
        next_type: typing.Optional[CharacterType] = None,
    ) -> bool:
        """
        Parameters
        ----------
        next_char : str | None, default=None
        next_type : CharacterType | None, default=None

        Returns
        -------
        bool
            True if character consumed

        Raises
        ------
        RuntimeError
        ValueError
        """
        if (
            (self._code_iter is None)
            and (self._pos_char is None)
            and (self._pos_idx is None)
        ):
            raise RuntimeError("try_next() cannot be used outside of a runtime context")
        if self.check_for_end():
            return False
        if (next_char is not None) and (next_type is not None):
            raise ValueError("Cannot specify both next_char and next_type")
        if (next_char is None) and (next_type is None):
            raise ValueError("Must specify either next_char or next_type, but not both")

        if (next_char is not None and self._pos_char == next_char) or (
            next_type is not None and self.validate_type(next_type)
        ):
            self.advance_pos()
            return True
        return False

    def assert_next(
        self,
        *,
        next_char: typing.Optional[str] = None,
        next_type: typing.Optional[CharacterType] = None,
    ) -> bool:
        """
        Parameters
        ----------
        next_char : str | None, default=None
        next_type : CharacterType | None, default=None

        Returns
        -------
        bool
            Result of `self._advance_pos()`;
            True if next character is not None

        Raises
        ------
        RuntimeError
        ValueError
        AssertionError
        """
        if (
            (self._code_iter is None)
            and (self._pos_char is None)
            and (self._pos_idx is None)
        ):
            raise RuntimeError(
                "assert_next() cannot be used outside of a runtime context"
            )
        if self.check_for_end():
            raise RuntimeError(
                "Expected character, but codeblock iterator is exhausted"
            )
        if (next_char is not None) and (next_type is not None):
            raise ValueError("Cannot specify both next_char and next_type")
        if (next_char is None) and (next_type is None):
            raise ValueError("Must specify either next_char or next_type, but not both")

        if next_char is not None:
            assert self._pos_char == next_char, ""

        elif next_type is not None:
            assert_msg: typing.Dict[CharacterType, str] = {
                CharacterType.LETTER: "Expected an alphabet character",
                CharacterType.DIGIT: "Expected a digit",
                CharacterType.STRING_CHAR: "Expected a valid character, not including '\"'",
                CharacterType.DATE_CHAR: "Expected a printable character, not including '#'",
                CharacterType.ID_NAME_CHAR: "Expected a printable character (w/o '[' or ']')",
                CharacterType.HEX_DIGIT: "Expected a hexadecimal digit",
                CharacterType.OCT_DIGIT: "Expected an octal digit",
                CharacterType.WS: "Expected a valid whitespace character (w/o '\\r' or '\\n')",
                CharacterType.ID_TAIL: "Expected either an alphanumeric character or '_'",
            }
            assert self.validate_type(next_type), assert_msg[next_type]

        # character valid, advance to next position
        return self.advance_pos()
