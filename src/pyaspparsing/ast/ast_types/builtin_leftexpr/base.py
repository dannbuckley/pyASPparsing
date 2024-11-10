"""Validation mix-in for AST built-in left expressions"""

from abc import ABCMeta, abstractmethod


class ValidateBuiltinLeftExpr(metaclass=ABCMeta):
    """
    Methods
    -------
    validate_response_expr()
    """

    @abstractmethod
    def validate_builtin_expr(self, is_subcall: bool = False):
        """Validate the response expression structure after
        initialization from an existing left expression object"""
