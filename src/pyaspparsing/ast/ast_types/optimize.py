"""Parser-level optimizations"""

import typing
import attrs
from .base import FormatterMixin, Expr
from .expressions import ConstExpr


@attrs.define(repr=False, slots=False)
class ExprAnnotation(FormatterMixin, Expr):
    """AST annotation wrapper for expressions

    Attributes
    ----------
    wrapped_expr : Expr
    """

    wrapped_expr: Expr


@attrs.define(repr=False, slots=False)
class FoldedExpr(ExprAnnotation):
    """AST annotation for constant folding

    The wrapped_expr is composed entirely of constant terms
    and should be folded into a single constant for optimization

    Attributes
    ----------
    wrapped_expr : Expr
        An expression composed entirely of ConstExpr terms
    """

    @staticmethod
    def try_fold(
        expr_left: Expr, expr_right: Expr, expr_type: type, *args: typing.Any
    ) -> Expr:
        assert issubclass(expr_type, Expr)

        def _check_type(eval_expr: Expr) -> typing.Tuple[bool, bool]:
            """"""
            is_folded = isinstance(eval_expr, FoldedExpr)
            if isinstance(eval_expr, ExprAnnotation) and not is_folded:
                is_const = isinstance(eval_expr.wrapped_expr, ConstExpr)
            else:
                is_const = isinstance(eval_expr, ConstExpr)
            return (is_const, is_folded)

        # extract info from expressions
        left_const, left_folded = _check_type(expr_left)
        right_const, right_folded = _check_type(expr_right)
        # fold constant expressions
        if left_const and right_const:
            return FoldedExpr(expr_type(expr_left, expr_right, *args))
        # unwrap folded child expression and wrap combined expression
        if left_const and right_folded:
            return FoldedExpr(expr_type(expr_left, expr_right.wrapped_expr, *args))
        if left_folded and right_const:
            return FoldedExpr(expr_type(expr_left.wrapped_expr, expr_right, *args))
        # unwrap both child expressions and wrap combined expression
        if left_folded and right_folded:
            return FoldedExpr(
                expr_type(expr_left.wrapped_expr, expr_right.wrapped_expr, *args)
            )
        # cannot fold the two expressions
        return expr_type(expr_left, expr_right, *args)


@attrs.define(repr=False, slots=False)
class AddNegated(ExprAnnotation):
    """AST annotation for AddExpr subtraction

    To ignore +/- symbols after parsing,
    transform subtraction into addition

    Example:
    `1 - 2` becomes `1 + (-2)`
    where `(-2)` is the original `2` wrapped with AddNegated

    Attributes
    ----------
    wrapped_expr : Expr
    """

    @staticmethod
    def wrap(orig_expr: Expr) -> Expr:
        """
        Parameters
        ----------
        orig_expr : Expr
        """
        if isinstance(orig_expr, FoldedExpr):
            # make sure FoldedExpr annotation is on the outside
            return FoldedExpr(AddNegated(orig_expr.wrapped_expr))
        return AddNegated(orig_expr)


@attrs.define(repr=False, slots=False)
class MultReciprocal(ExprAnnotation):
    """AST annotation for MultExpr division

    To ignore * and / symbols after parsing,
    transform float division into multiplication

    Example:
    `2 / 4` becomes `2 * (1/4)`
    where `(1/4)` is the original `4` wrapped with MultReciprocal

    Attributes
    ----------
    wrapped_expr : Expr
    """

    @staticmethod
    def wrap(orig_expr: Expr) -> Expr:
        """
        Parameters
        ----------
        orig_expr : Expr
        """
        if isinstance(orig_expr, FoldedExpr):
            # make sure FoldedExpr annotation is on the outside
            return FoldedExpr(MultReciprocal(orig_expr.wrapped_expr))
        return MultReciprocal(orig_expr)
