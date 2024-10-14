"""Classic ASP tokens"""

import enum
import typing

import attrs

__all__ = ["TokenType", "KeywordType", "DebugLineInfo", "Token"]


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class TokenType(enum.IntEnum):
    """Enumeration containing supported token types

    Used to construct tokens
    """

    NEWLINE = enum.auto()
    SYMBOL = enum.auto()

    # generic text outside of any ASP delimiter
    FILE_TEXT = enum.auto()

    # high-level ASP delimiters
    DELIM_START_SCRIPT = enum.auto()
    DELIM_START_PROCESSING = enum.auto()
    DELIM_START_OUTPUT = enum.auto()
    DELIM_END = enum.auto()

    # HTML comments
    HTML_START_COMMENT = enum.auto()
    HTML_END_COMMENT = enum.auto()

    # file inclusion
    INCLUDE_KW = enum.auto()
    INCLUDE_TYPE = enum.auto()
    INCLUDE_PATH = enum.auto()

    # identifier
    IDENTIFIER = enum.auto()
    IDENTIFIER_IDDOT = enum.auto()
    IDENTIFIER_DOTID = enum.auto()
    IDENTIFIER_DOTIDDOT = enum.auto()

    # literals
    LITERAL_STRING = enum.auto()
    LITERAL_INT = enum.auto()
    LITERAL_HEX = enum.auto()
    LITERAL_OCT = enum.auto()
    LITERAL_FLOAT = enum.auto()
    LITERAL_DATE = enum.auto()


@enum.verify(enum.UNIQUE)
class KeywordType(enum.StrEnum):
    """Enumeration of casefolded keywords and safe keywords

    Used for comparison when consuming tokens
    """

    # safe keywords
    SAFE_KW_DEFAULT = "default"
    SAFE_KW_ERASE = "erase"
    SAFE_KW_ERROR = "error"
    SAFE_KW_EXPLICIT = "explicit"
    SAFE_KW_PROPERTY = "property"
    SAFE_KW_STEP = "step"

    # keywords
    KW_AND = "and"
    KW_BYREF = "byref"
    KW_BYVAL = "byval"
    KW_CALL = "call"
    KW_CASE = "case"
    KW_CLASS = "class"
    KW_CONST = "const"
    KW_DIM = "dim"
    KW_DO = "do"
    KW_EACH = "each"
    KW_ELSE = "else"
    KW_ELSEIF = "elseif"
    KW_EMPTY = "empty"
    KW_END = "end"
    KW_EQV = "eqv"
    KW_EXIT = "exit"
    KW_FALSE = "false"
    KW_FOR = "for"
    KW_FUNCTION = "function"
    KW_GET = "get"
    KW_GOTO = "goto"
    KW_IF = "if"
    KW_IMP = "imp"
    KW_IN = "in"
    KW_IS = "is"
    KW_LET = "let"
    KW_LOOP = "loop"
    KW_MOD = "mod"
    KW_NEW = "new"
    KW_NEXT = "next"
    KW_NOT = "not"
    KW_NOTHING = "nothing"
    KW_NULL = "null"
    KW_ON = "on"
    KW_OPTION = "option"
    KW_OR = "or"
    KW_PRESERVE = "preserve"
    KW_PRIVATE = "private"
    KW_PUBLIC = "public"
    KW_REDIM = "redim"
    KW_RESUME = "resume"
    KW_SELECT = "select"
    KW_SET = "set"
    KW_SUB = "sub"
    KW_THEN = "then"
    KW_TO = "to"
    KW_TRUE = "true"
    KW_UNTIL = "until"
    KW_WEND = "wend"
    KW_WITH = "with"
    KW_XOR = "xor"


@attrs.define
class DebugLineInfo:
    """Line number and starting index of token"""

    # line number that token is on
    line_no: int
    # starting index of token in line
    # = [starting index of token in code string] - [starting index of line]
    line_start_pos: int


@attrs.define(repr=False)
class Token:
    """Represents an individual token"""

    token_type: TokenType
    # default: entire code string
    token_src: slice = attrs.field(default=slice(None, None, None))

    # don't include in equality comparison
    line_info: typing.Optional[DebugLineInfo] = attrs.field(
        default=None, eq=False, kw_only=True
    )

    def __repr__(self) -> str:
        return "\n".join(
            [
                "Token(",
                f"  token_type={repr(self.token_type)},",
                f"  token_src={repr(self.token_src)},",
                f"  line_info={repr(self.line_info)}",
                ")",
            ]
        )

    @staticmethod
    def _factory(
        tok_type: TokenType,
        start: int,
        stop: int,
        *,
        line_info: typing.Optional[DebugLineInfo] = None,
    ):
        """Base factory method, constructs token_src argument from start and stop"""
        if start is None or stop is None:
            raise ValueError("Must specify both start and stop parameters")
        return Token(tok_type, slice(start, stop), line_info=line_info)

    @staticmethod
    def newline(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type NEWLINE"""
        return Token._factory(TokenType.NEWLINE, start, stop, line_info=line_info)

    @staticmethod
    def symbol(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type SYMBOL"""
        return Token._factory(TokenType.SYMBOL, start, stop, line_info=line_info)

    @staticmethod
    def file_text(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type FILE_TEXT"""
        return Token._factory(TokenType.FILE_TEXT, start, stop, line_info=line_info)

    @staticmethod
    def identifier(
        start: int,
        stop: int,
        *,
        dot_start: bool = False,
        dot_end: bool = False,
        line_info: typing.Optional[DebugLineInfo] = None,
    ):
        """Factory method for Tokens of types IDENTIFIER, IDENTIFIER_DOTID,
        IDENTIFIER_IDDOT, or IDENTIFIER_DOTIDDOT"""
        if dot_start and dot_end:
            tok_type = TokenType.IDENTIFIER_DOTIDDOT
        elif dot_start and not dot_end:
            tok_type = TokenType.IDENTIFIER_DOTID
        elif not dot_start and dot_end:
            tok_type = TokenType.IDENTIFIER_IDDOT
        else:
            tok_type = TokenType.IDENTIFIER
        return Token._factory(tok_type, start, stop, line_info=line_info)

    @staticmethod
    def string_literal(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type LITERAL_STRING"""
        return Token._factory(
            TokenType.LITERAL_STRING, start, stop, line_info=line_info
        )

    @staticmethod
    def int_literal(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type LITERAL_INT"""
        return Token._factory(TokenType.LITERAL_INT, start, stop, line_info=line_info)

    @staticmethod
    def hex_literal(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type LITERAL_HEX"""
        return Token._factory(TokenType.LITERAL_HEX, start, stop, line_info=line_info)

    @staticmethod
    def oct_literal(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type LITERAL_OCT"""
        return Token._factory(TokenType.LITERAL_OCT, start, stop, line_info=line_info)

    @staticmethod
    def float_literal(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type LITERAL_FLOAT"""
        return Token._factory(TokenType.LITERAL_FLOAT, start, stop, line_info=line_info)

    @staticmethod
    def date_literal(
        start: int, stop: int, *, line_info: typing.Optional[DebugLineInfo] = None
    ):
        """Factory method for Token of type LITERAL_DATE"""
        return Token._factory(TokenType.LITERAL_DATE, start, stop, line_info=line_info)
