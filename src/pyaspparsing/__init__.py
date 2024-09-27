"""pyASPparsing"""

__version__ = "2024.9"


class CodetoolError(Exception):
    """Custom error class for this package. To be used as a catch-all"""

    pass


class TokenizerError(CodetoolError):
    """An error that occurs in Tokenizer.process()"""

    pass
