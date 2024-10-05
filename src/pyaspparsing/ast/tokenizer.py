""""""

import typing

import attrs

from .. import TokenizerError
from .token_types import *


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

    # debug line info
    _line_no: int = attrs.field(default=1)
    _line_start_idx: int = attrs.field(default=0)

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

        The StopIteration exception will bubble up through __next__()

        Raises
        ------
        StopIteration
        """
        if self._pos_char is None:
            self._code_iter = None
            self._pos_idx = None
            raise StopIteration

    def _skip_whitespace(self):
        """Consume and ignore extraneous whitespace"""
        if self._pos_char.isspace() and not self._pos_char in "\r\n":
            while self._advance_pos() and (
                self._pos_char.isspace() and not self._pos_char in "\r\n"
            ):
                pass

            # check for line continuation
            if self._pos_char == "_":
                self._advance_pos()  # consume '_'
            if self._pos_char is not None and (
                self._pos_char.isspace() and not self._pos_char in "\r\n"
            ):
                while self._advance_pos() and (
                    self._pos_char.isspace() and not self._pos_char in "\r\n"
                ):
                    pass

            # optional newline characters in line continuation
            carriage_return = self._pos_char == "\r"
            if carriage_return:
                self._advance_pos()  # consume
            line_feed = self._pos_char == "\n"
            if line_feed:
                self._advance_pos()  # consume

            if carriage_return or line_feed:
                # update debug info
                self._line_no += 1
                self._line_start_idx = self._pos_idx

            self._check_for_end()

    def _handle_newline(self) -> Token:
        """Handles newline characters (':', carriage return, or line feed)

        Returns
        -------
        Token
            Token of type NEWLINE

        Raises
        ------
        RuntimeError
            When the character at the current position is not a newline character
        """
        if self._pos_char in ":\r\n":
            start_newline: int = self._pos_idx
            while (self._pos_char is not None) and (self._pos_char in ":\r\n"):
                carriage_return = self._pos_char == "\r"
                self._advance_pos()
                if carriage_return and self._pos_char == "\n":
                    # "\r\n" should be treated as a single newline
                    self._advance_pos()
                self._line_no += 1
                self._line_start_idx = self._pos_idx
            # since the "newline" token can represent multiple newlines,
            # don't include debug line info
            return Token.newline(start_newline, self._pos_idx)
        raise RuntimeError(
            "Newline token handler called, but no newline characters found"
        )

    def _skip_comment(self) -> Token:
        """Skip comments that start with either a single quote or "Rem"

        Calls _check_for_end(), which may raise StopIteration if
        the comment persists until the end of the codeblock

        Returns
        -------
        Token
            Token of type NEWLINE (if comment is terminated by a newline)
        """
        while self._advance_pos() and not self._pos_char in ":\r\n":
            pass
        self._check_for_end()
        # didn't throw StopIteration, check for newline
        return self._handle_newline()

    def _handle_identifier(self, dot_start: bool = False) -> Token:
        """Handles an identifier token

        Could be one of:
        - a normal identifier
        - an escaped identifier (i.e., wrapped in [square brackets])
        - an identifier preceded by a dot ('.')
        - an identiifer succeeded by a dot ('.')
        - an identifier both preceded and succeeded  by a dot ('.')

        Returns
        -------
        Token

        Raises
        ------
        TokenizerError
            When the final ']' is missing for an escaped identifier,
            or when the dot ('.') symbol appears before a "Rem" comment
        """
        # save starting position for later
        start_iden: int = self._pos_idx - 1 if dot_start else self._pos_idx
        if self._pos_char == "[":
            # escaped identifier
            # GOLD parser set of printable characters
            printable = set([0xA0, *range(0x20, 0x7F)]).difference(map(ord, "[]"))
            while self._advance_pos() and ord(self._pos_char) in printable:
                pass
            # there should be a closing ']'
            if self._pos_char is None or self._pos_char != "]":
                raise TokenizerError("Expected closing ']' for espaced identifier")
            self._advance_pos()  # consume ']'

            dot_end = self._pos_char == "."
            if dot_end:
                self._advance_pos()  # consume

            return Token.identifier(
                start_iden,
                self._pos_idx,
                dot_start=dot_start,
                dot_end=dot_end,
                line_info=DebugLineInfo(
                    self._line_no, start_iden - self._line_start_idx
                ),
                # line_no=self._line_no,
                # line_start_pos=start_iden - self._line_start_idx,
            )

        # normal identifier
        while self._advance_pos() and (
            self._pos_char.isalnum() or self._pos_char == "_"
        ):
            pass

        if "rem" in self.codeblock[start_iden : self._pos_idx].casefold():
            if dot_start:
                raise TokenizerError(
                    "Illegal use of '.' symbol; cannot appear before Rem"
                )
            return self._skip_comment()

        dot_end = self._pos_char == "."
        if dot_end:
            self._advance_pos()  # consume

        return Token.identifier(
            start_iden,
            self._pos_idx,
            dot_start=dot_start,
            dot_end=dot_end,
            line_info=DebugLineInfo(self._line_no, start_iden - self._line_start_idx),
            # line_no=self._line_no,
            # line_start_pos=start_iden - self._line_start_idx,
        )

    def _handle_string_literal(self) -> Token:
        """Handles a string literal token

        Returns
        -------
        Token
            Token of type LITERAL_STRING

        Raises
        ------
        TokenizerError
            When the final double quote ('"') is missing
        """
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

        return Token.string_literal(
            start_str,
            self._pos_idx,
            line_info=DebugLineInfo(self._line_no, start_str - self._line_start_idx),
            # line_no=self._line_no,
            # line_start_pos=start_str - self._line_start_idx,
        )

    def _handle_number_literal(self, dot_start: bool = False) -> Token:
        """Handles a number literal token

        Could be one of:
        - an integer literal token
        - a float literal token

        Returns
        -------
        Token

        Raises
        ------
        TokenizerError
            When something other than a digit appears after '.' in a float literal,
            or when something other than a digit appears after 'E' in a float literal
        """
        start_num: int = (
            self._pos_idx - 1 if dot_start else self._pos_idx
        )  # don't know token type, but save starting position for later
        # goto end of current number chunk
        while self._advance_pos() and self._pos_char.isnumeric():
            pass

        if not dot_start:
            # token did not start with a decimal point
            # is there a decimal point after the first number chunk?
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

        if dot_start or float_dec_pt or float_sci_e:
            return Token.float_literal(
                start_num,
                self._pos_idx,
                line_info=DebugLineInfo(
                    self._line_no, start_num - self._line_start_idx
                ),
                # line_no=self._line_no,
                # line_start_pos=start_num - self._line_start_idx,
            )
        # otherwise, int literal
        return Token.int_literal(
            start_num,
            self._pos_idx,
            line_info=DebugLineInfo(self._line_no, start_num - self._line_start_idx),
            # line_no=self._line_no,
            # line_start_pos=start_num - self._line_start_idx,
        )

    def _handle_amp(self) -> Token:
        """Handles tokens that begin with an ampersand ('&')

        Could be one of:
        - an ampersand ('&') symbol
        - a hexadecimal literal token
        - an octal literal token

        Returns
        -------
        Token

        Raises
        ------
        TokenizerError
            When something other than a hexadecimal digit appears after '&H'
        """
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
            return Token.hex_literal(
                start_amp,
                self._pos_idx,
                line_info=DebugLineInfo(
                    self._line_no, start_amp - self._line_start_idx
                ),
                # line_no=self._line_no,
                # line_start_pos=start_amp - self._line_start_idx,
            )

        # ======== OCT LITERAL ========
        # need at least one octal digit
        if self._pos_char is None or not self._pos_char in "01234567":
            # treat as concatenation operator, return as symbol
            return Token.symbol(
                start_amp,
                self._pos_idx,
                line_info=DebugLineInfo(
                    self._line_no, start_amp - self._line_start_idx
                ),
                # line_no=self._line_no,
                # line_start_pos=start_amp - self._line_start_idx,
            )
        # goto end of oct literal
        while self._advance_pos() and self._pos_char in "01234567":
            pass
        # check for optional '&' at end
        if self._pos_char == "&":
            self._advance_pos()  # consume
        return Token.oct_literal(
            start_amp,
            self._pos_idx,
            line_info=DebugLineInfo(self._line_no, start_amp - self._line_start_idx),
            # line_no=self._line_no,
            # line_start_pos=start_amp - self._line_start_idx,
        )

    def _handle_date_literal(self) -> Token:
        """Handles a date literal token

        Returns
        -------
        Token
            Token of type LITERAL_DATE

        Raises
        ------
        TokenizerError
            When something other than a printable character appears after the first '#',
            or when the final '#' is missing
        """
        start_date: int = self._pos_idx
        self._advance_pos()  # consume '#'
        printable = set([0xA0, *range(0x20, 0x7F)]).difference([ord("#")])
        if self._pos_char is None or not ord(self._pos_char) in printable:
            raise TokenizerError(
                "Expected printable character in date literal, "
                f"but found {repr(self._pos_char)} instead"
            )
        # goto end of date literal content
        while self._advance_pos() and ord(self._pos_char) in printable:
            pass
        if self._pos_char != "#":
            raise TokenizerError(
                f"Expected '#' at end of date literal, but found {repr(self._pos_char)} instead"
            )
        self._advance_pos()  # consume '#'
        return Token.date_literal(
            start_date,
            self._pos_idx,
            line_info=DebugLineInfo(self._line_no, start_date - self._line_start_idx),
            # line_no=self._line_no,
            # line_start_pos=start_date - self._line_start_idx,
        )

    def _handle_dot(self) -> Token:
        """Handles tokens that begin with a dot

        Could be either of:
        - an identifier
        - a float

        Returns
        -------
        Token

        Raises
        ------
        TokenizerError
            When the dot ('.') appears by itself
        RuntimeError
            When the character at the current position is not a dot ('.')
        """
        if self._pos_char == ".":
            # consume '.'
            start_dot: int = self._pos_idx
            self._advance_pos()  # consume '.'

            if self._pos_char is not None:
                if self._pos_char.isalpha() or self._pos_char == "[":
                    # dotted identifier
                    return self._handle_identifier(True)

                if self._pos_char.isnumeric():
                    # float literal with no leading digits
                    return self._handle_number_literal(True)

            # just return as symbol, let parser interpret meaning
            return Token.symbol(
                start_dot,
                self._pos_idx,
                line_info=DebugLineInfo(
                    self._line_no, start_dot - self._line_start_idx
                ),
                # line_no=self._line_no,
                # line_start_pos=start_dot - self._line_start_idx,
            )
        raise RuntimeError("Dot token handler called, but did not find dot symbol")

    def _handle_terminal(self) -> Token:
        """Determines which token type is appropriate given
        the current position in the codeblock

        Could be one of:
        - a dotted ('.') terminal
        - an identifier
        - a string literal
        - a number literal
        - an ampersand ('&') terminal
        - a date literal

        Returns
        -------
        Token

        Raises
        ------
        ValueError
            When token type cannot be determined
        """
        # determine token type
        if self._pos_char == ".":
            # could be float or identifier
            return self._handle_dot()
        if self._pos_char.isalpha() or self._pos_char == "[":
            # could be identifier or newline if "Rem" comment present
            return self._handle_identifier()
        if self._pos_char == '"':
            return self._handle_string_literal()
        if self._pos_char.isnumeric():
            # could be float or int
            return self._handle_number_literal()
        if self._pos_char == "&":
            # could be hex or oct literal, or just '&' symbol
            return self._handle_amp()
        if self._pos_char == "#":
            return self._handle_date_literal()
        raise ValueError("Could not determine token type")

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

        # comment != code
        if self._pos_char == "'":
            # will raise StopIteration if comment goes till end of codeblock
            return self._skip_comment()

        # treat newline as a token
        # condenses multiple contiguous newlines into a single token
        if self._pos_char in ":\r\n":
            return self._handle_newline()

        try:
            return self._handle_terminal()
        except StopIteration as stop_ex:
            raise StopIteration from stop_ex
        except TokenizerError as tok_ex:
            raise TokenizerError("Terminal tokenizer raised an error") from tok_ex
        except ValueError:
            # other token type, just return symbol
            self._advance_pos()  # consume symbol
            return Token.symbol(
                self._pos_idx - 1,
                self._pos_idx,
                line_info=DebugLineInfo(
                    self._line_no, self._pos_idx - self._line_start_idx - 1
                ),
                # line_no=self._line_no,
                # line_start_pos=self._pos_idx - self._line_start_idx - 1,
            )
