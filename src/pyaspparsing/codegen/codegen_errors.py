"""Special error types for code generation"""

from .. import CodetoolError


class ExitDoLoop(CodetoolError):
    """Error implementation for an 'Exit Do' statement"""


class ExitForLoop(CodetoolError):
    """Error implementation for an 'Exit For' statement"""


class ExitFunction(CodetoolError):
    """Error implementation for an 'Exit Function' statement"""


class ExitProperty(CodetoolError):
    """Error implementation for an 'Exit Property' statement"""


class ExitSub(CodetoolError):
    """Error implementation for an 'Exit Sub' statement"""


class EndResponse(CodetoolError):
    """Error implementation for Response.End"""
