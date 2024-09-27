"""Tokenizer for classic ASP code"""

from dataclasses import dataclass
import enum
import typing

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


@dataclass
class Tokenizer:
    """Tokenizer object.

    Attributes
    ----------
    codeblock : str

    Methods
    -------
    process()
        Tokenize the codeblock
    """

    codeblock: str

    def process(self) -> typing.Generator[Token, None, None]:
        """Iteratively tokenize the codeblock

        Yields
        ------
        Token
            The next available token in the codeblock
        """
        # setup iteration
        code_iter: typing.Iterator[str] = iter(self.codeblock)
        # variables to keep track of position within codeblock
        # preload first character
        pos_char: typing.Optional[str] = next(
            code_iter, None
        )  # use next(..., None) instead of handling StopIteration
        pos_idx: int = 0

        def _advance_pos() -> bool:
            """Advance to the next position in the codeblock

            Returns
            -------
            bool
                True if codeblock iterator not exhausted
            """
            # modify state of enclosing function
            nonlocal code_iter, pos_char, pos_idx
            pos_char = next(code_iter, None)
            pos_idx += 1
            return pos_char is not None

        # main tokenizer loop
        # base case: exit at end of string (i.e., when iterator exhausted)
        while pos_char is not None:
            # determine token type
            if pos_char.isspace():
                # ======== WHITESPACE ========
                # consume and ignore whitespace
                while _advance_pos() and pos_char.isspace():
                    pass
                # already at next character, don't advance further
            elif pos_char.isalpha():
                # ======== IDENTIFIER ========
                # basic example identifier: [a-zA-Z][a-zA-Z0-9]*
                start_iden: int = pos_idx  # save starting index of identifier for later
                # goto end of identifier
                while _advance_pos() and pos_char.isalnum():
                    pass
                yield Token(TokenType.IDENTIFIER, slice(start_iden, pos_idx))
                del start_iden
                # already at next character, don't advance further
            elif pos_char == '"':
                # ======== STRING LITERAL ========
                start_str: int = (
                    pos_idx  # save starting index of string literal for later
                )
                # helper variables to keep track of state
                found_dbl_quote = False  # was previous character a double quote?
                terminated = False  # reached end of string literal
                # goto end of string literal
                while _advance_pos():
                    if pos_char == '"' and not found_dbl_quote:
                        found_dbl_quote = True
                        # check next character to see if this is really the end of the string literal
                        continue
                    if found_dbl_quote:
                        if pos_char == '"':
                            # quote is escaped ('""'), keep looping
                            found_dbl_quote = False
                            continue
                        # string literal ends before codeblock does, stop looping
                        terminated = True
                        break
                if not found_dbl_quote and not terminated:
                    raise TokenizerError(
                        "Expected ending '\"' for string literal, but reached end of code string"
                    )
                yield Token(TokenType.LITERAL_STRING, slice(start_str, pos_idx))
                del start_str, found_dbl_quote, terminated
                # already at next character, don't advance further
            elif pos_char.isnumeric():
                # ======== INT OR FLOAT LITERAL ========
                start_num: int = (
                    pos_idx  # don't know token type, but save starting position for later
                )
                # goto end of current number chunk
                while _advance_pos() and pos_char.isnumeric():
                    pass

                # TODO: handle float that starts with '.' (no leading digits)
                # does the token have a decimal point?
                float_dec_pt = pos_char == "."
                if float_dec_pt:
                    _advance_pos()  # consume '.'
                    # there should be one or more digits after '.'
                    if pos_char is None or not pos_char.isnumeric():
                        raise TokenizerError(
                            "Expected digit after '.' in float literal"
                        )
                    # goto end of current number chunk
                    while _advance_pos() and pos_char.isnumeric():
                        pass

                # does the token have the scientific notation indicator?
                float_sci_e = pos_char == "E"
                if float_sci_e:
                    _advance_pos()  # consume 'E'
                    # optional '+' or '-'
                    if pos_char is not None and pos_char in "+-":
                        _advance_pos()  # consume
                    # there should be one or more digits after 'E' (or after '+'/'-')
                    if pos_char is None or not pos_char.isnumeric():
                        raise TokenizerError(
                            "Expected digit after 'E' in float literal"
                        )
                    # goto end of current number chunk
                    while _advance_pos() and pos_char.isnumeric():
                        pass

                yield Token(
                    # is this an int or a float?
                    (
                        TokenType.LITERAL_FLOAT
                        if float_dec_pt or float_sci_e
                        else TokenType.LITERAL_INT
                    ),
                    slice(start_num, pos_idx),
                )
                del start_num, float_dec_pt, float_sci_e
                # already at next character, don't advance further
            elif pos_char == "&":
                # hex or oct literal
                _advance_pos()  # consume '&'
                if pos_char == "H":
                    # ======== HEX LITERAL ========
                    _advance_pos()  # consume 'H'
                    # need at least one hexadecimal digit
                    if pos_char is None or not (
                        pos_char.isnumeric() or pos_char.casefold() in "abcdef"
                    ):
                        raise TokenizerError(
                            f"Expected at least one hexadecimal digit after '&H', but found '{pos_char}' instead"
                        )
                    start_hex: int = pos_idx - 2  # include '&H' in Token object
                    # goto end of hex literal
                    while _advance_pos() and (
                        pos_char.isnumeric() or pos_char.casefold() in "abcdef"
                    ):
                        pass
                    # check for optional '&' at end
                    if pos_char == "&":
                        _advance_pos()  # consume
                    yield Token(TokenType.LITERAL_HEX, slice(start_hex, pos_idx))
                    del start_hex
                    # already at next character, don't advance further
                else:
                    # ======== OCT LITERAL ========
                    # need at least one octal digit
                    if pos_char is None or not pos_char in "01234567":
                        raise TokenizerError(
                            f"Expected at least one octal digit after '&', but found '{pos_char}' instead"
                        )
                    start_oct: int = pos_idx - 1  # include '&' in Token object
                    # goto end of oct literal
                    while _advance_pos() and pos_char in "01234567":
                        pass
                    # check for optional '&' at end
                    if pos_char == "&":
                        _advance_pos()  # consume
                    yield Token(TokenType.LITERAL_OCT, slice(start_oct, pos_idx))
                    del start_oct
                    # already at next character, don't advance further
            elif pos_char == "#":
                # date literal
                pass
            else:
                # other token type, return symbol
                yield Token(TokenType.SYMBOL, slice(pos_idx, pos_idx + 1))
                _advance_pos()  # move past current token
