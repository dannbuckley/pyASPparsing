"""pyASPparsing"""

__version__ = "2024.9"


class CodetoolError(Exception):
    """Custom error class for this package. To be used as a catch-all"""


class TokenizerError(CodetoolError):
    """An error that occurs during Tokenizer iteration"""


class ParserError(CodetoolError):
    """An error that occurs during Parser iteration"""
