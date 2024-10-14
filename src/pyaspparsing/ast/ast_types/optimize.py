"""Parser-level optimizations"""

from typing import Any
import attrs
from .base import FormatterMixin, Expr
from .expressions import ConstExpr


@attrs.define(repr=False, slots=False)
class FoldedExpr(FormatterMixin, Expr):
    """An AST type to represent constant folding

    The expr_to_fold is composed entirely of constant terms
    and should be folded into a single constant for optimization

    Attributes
    ----------
    expr_to_fold : Expr
        An expression composed entirely of ConstExpr terms
    """

    expr_to_fold: Expr

    @staticmethod
    def try_fold(
        expr_left: Expr, expr_right: Expr, expr_type: type, *args: Any
    ) -> Expr:
        assert issubclass(expr_type, Expr)
        left_const = isinstance(expr_left, ConstExpr)
        right_const = isinstance(expr_right, ConstExpr)
        left_folded = isinstance(expr_left, FoldedExpr)
        right_folded = isinstance(expr_right, FoldedExpr)
        if left_const and right_const:
            return FoldedExpr(expr_type(expr_left, expr_right, *args))
        # unwrap folded child expression and wrap combined expression
        if left_const and right_folded:
            return FoldedExpr(expr_type(expr_left, expr_right.expr_to_fold, *args))
        if left_folded and right_const:
            return FoldedExpr(expr_type(expr_left.expr_to_fold, expr_right, *args))
        # unwrap both child expressions and wrap combined expression
        if left_folded and right_folded:
            return FoldedExpr(
                expr_type(expr_left.expr_to_fold, expr_right.expr_to_fold, *args)
            )
        # cannot fold the two expressions
        return expr_type(expr_left, expr_right, *args)
