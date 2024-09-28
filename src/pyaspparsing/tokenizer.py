"""Tokenizer for classic ASP code"""

from dataclasses import dataclass
import enum
import typing

import attrs

from . import TokenizerError


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class TokenType(enum.Enum):
    """Enumeration containing supported token types"""

    SYMBOL = 1
    IDENTIFIER = 2
    LITERAL_STRING = 3
    LITERAL_INT = 4
    LITERAL_HEX = 5
    LITERAL_OCT = 6
    LITERAL_FLOAT = 7
    LITERAL_DATE = 8


@dataclass
class Token:
    """Represents an individual token.

    Attributes
    ----------
    token_type : TokenType
        Enumerated token type
    token_src : slice, default=slice(None, None, None)
        Section of original code associated with this token
    """

    token_type: TokenType
    token_src: slice = slice(None, None, None)  # default: entire string


@attrs.define()
class Tokenizer:
    """Identify tokens within a codeblock

    Attributes
    ----------
    codeblock : str
    """

    codeblock: str
    _code_iter: typing.Iterator[str] = attrs.field(default=None, repr=False, init=False)
    # keep track of position within codeblock
    _pos_char: typing.Optional[str] = attrs.field(default=None, repr=False, init=False)
    _pos_idx: typing.Optional[str] = attrs.field(default=None, repr=False, init=False)

    def __iter__(self) -> typing.Self:
        """Setup state variables for iteration

        Returns
        -------
        Self
        """
        self._code_iter = iter(self.codeblock)
        # preload first character
        self._pos_char = next(
            self._code_iter, None
        )  # use next(..., None) instead of handling StopIteration
        self._pos_idx = 0
        return self

    def _advance_pos(self) -> bool:
        """Advance to the next position in the codeblock

        Returns
        -------
        bool
            True if codeblock iterator not exhausted
        """
        if self._pos_char is None:
            # iterator already exhausted, or __iter__() not called yet
            return False
        self._pos_char = next(self._code_iter, None)
        self._pos_idx += 1
        return self._pos_char is not None

    def _check_for_end(self):
        """If tokenizer reached the end of the codeblock,
        signal to the consumer that iteration should stop

        The StopIteration exception will bubble up through __next__()"""
        if self._pos_char is None:
            self._code_iter = None
            self._pos_idx = None
            raise StopIteration

    def _skip_whitespace(self):
        """Consume and ignore extraneous whitespace"""
        if self._pos_char.isspace():
            while self._advance_pos() and self._pos_char.isspace():
                pass
            self._check_for_end()

    def _handle_identifier(self) -> Token:
        """"""
        return Token(TokenType.IDENTIFIER)

    def _handle_string_literal(self) -> Token:
        """"""
        # save starting index of string literal for later
        start_str: int = self._pos_idx
        # helper variables to keep track of state
        found_dbl_quote = False  # was previous character a double quote?
        terminated = False  # reached end of string literal

        # goto end of string literal
        while self._advance_pos():
            if self._pos_char == '"' and not found_dbl_quote:
                found_dbl_quote = True
                # check next character to see if this is really the end of the string literal
                continue
            if found_dbl_quote:
                if self._pos_char == '"':
                    # quote is escaped ('""'), keep looping
                    found_dbl_quote = False
                    continue
                # string literal ends before codeblock does, stop looping
                terminated = True
                break

        if not found_dbl_quote and not terminated:
            raise TokenizerError(
                "Expected ending '\"' for string literal, but reached end of codeblock"
            )

        return Token(TokenType.LITERAL_STRING, slice(start_str, self._pos_idx))

    def _handle_number_literal(self) -> Token:
        """"""
        start_num: int = (
            self._pos_idx
        )  # don't know token type, but save starting position for later
        # goto end of current number chunk
        while self._advance_pos() and self._pos_char.isnumeric():
            pass

        # TODO: handle float that starts with '.' (no leading digits)

        # does the token have a decimal point?
        float_dec_pt = self._pos_char == "."
        if float_dec_pt:
            self._advance_pos()  # consume '.'
            # there should be one or more digits after '.'
            if self._pos_char is None or not self._pos_char.isnumeric():
                raise TokenizerError("Expected digit after '.' in float literal")
            # goto end of number chunk
            while self._advance_pos() and self._pos_char.isnumeric():
                pass

        # does the token have the scientific notation indicator?
        float_sci_e = self._pos_char == "E"
        if float_sci_e:
            self._advance_pos()  # consume 'E'
            # optional '+' or '-'
            if self._pos_char is not None and self._pos_char in "+-":
                self._advance_pos()  # consume
            # there should be one or more digits after 'E'
            # (or after '+'/'-' if present)
            if self._pos_char is None or not self._pos_char.isnumeric():
                raise TokenizerError("Expected digit after 'E' in float literal")
            # goto end of current number chunk
            while self._advance_pos() and self._pos_char.isnumeric():
                pass

        return Token(
            # is this an int or a float?
            (
                TokenType.LITERAL_FLOAT
                if float_dec_pt or float_sci_e
                else TokenType.LITERAL_INT
            ),
            slice(start_num, self._pos_idx),
        )

    def _handle_amp_literal(self) -> Token:
        """"""
        start_amp: int = (
            self._pos_idx
        )  # don't know token type, but save starting position for later
        self._advance_pos()  # consume '&'

        if self._pos_char == "H":
            # ======== HEX LITERAL ========
            self._advance_pos()  # consume 'H'
            # need at least one hexadecimal digit
            if self._pos_char is None or not (
                self._pos_char.isnumeric() or self._pos_char.casefold() in "abcdef"
            ):
                raise TokenizerError(
                    "Expected at least one hexadecimal digit after '&H', "
                    f"but found {repr(self._pos_char)} instead"
                )
            # goto end of hex literal
            while self._advance_pos() and (
                self._pos_char.isnumeric() or self._pos_char.casefold() in "abcdef"
            ):
                pass
            # check for optional '&' at end
            if self._pos_char == "&":
                self._advance_pos()  # consume
            return Token(TokenType.LITERAL_HEX, slice(start_amp, self._pos_idx))

        # ======== OCT LITERAL ========
        # need at least one octal digit
        if self._pos_char is None or not self._pos_char in "01234567":
            raise TokenizerError(
                "Expected at least one octal digit after '&', "
                f"but found {repr(self._pos_char)} instead"
            )
        # goto end of oct literal
        while self._advance_pos() and self._pos_char in "01234567":
            pass
        # check for optional '&' at end
        if self._pos_char == "&":
            self._advance_pos()  # consume
        return Token(TokenType.LITERAL_OCT, slice(start_amp, self._pos_idx))

    def _handle_date_literal(self) -> Token:
        """"""
        return Token(TokenType.LITERAL_DATE)

    def __next__(self) -> Token:
        """Advance to next token

        Returns
        -------
        Token
            The next available token in the codeblock

        Raises
        ------
        StopIteration
            When the tokenizer reaches the end of the codeblock
        TokenizerError
            When the tokenizer encounters an invalid token
        RuntimeError
            If __next__() is called before __iter__()
        """
        if self._pos_char is None and self._pos_idx is None:
            raise RuntimeError("Must call __iter__() before calling __next__()")

        # stop if currently at end of codeblock
        self._check_for_end()

        # extraneous whitespace != code
        self._skip_whitespace()

        # determine token type
        if self._pos_char.isalpha():
            return self._handle_identifier()
        if self._pos_char == '"':
            return self._handle_string_literal()
        if self._pos_char.isnumeric():
            return self._handle_number_literal()
        if self._pos_char == "&":
            return self._handle_amp_literal()
        if self._pos_char == "#":
            return self._handle_date_literal()

        # other token type, return symbol
        self._advance_pos()  # consume symbol
        return Token(TokenType.SYMBOL, slice(self._pos_idx - 1, self._pos_idx))
