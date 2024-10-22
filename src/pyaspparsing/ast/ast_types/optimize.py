"""Parser-level optimizations"""

from __future__ import annotations
import operator
import typing
import attrs
from .base import FormatterMixin, Expr
from .expressions import ConstExpr, Nothing


@attrs.define(repr=False, slots=False)
class ExprAnnotation(FormatterMixin, Expr):
    """AST annotation wrapper for expressions

    Attributes
    ----------
    wrapped_expr : Expr
    """

    wrapped_expr: Expr


@attrs.define(repr=False, slots=False)
class EvalExpr(FormatterMixin, Expr):
    """AST type for evaluated constant expressions

    Attributes
    ----------
    expr_value : int | float | bool | str
    """

    expr_value: typing.Union[int, float, bool, str]

    def str_cast(self):
        """Cast expression to string for concatenation operator"""
        if isinstance(self.expr_value, str):
            return self
        return EvalExpr(str(self.expr_value))

    def reciprocal(self):
        """Helper function for MultReciprocal wrapper"""
        return EvalExpr(operator.pow(self.expr_value, -1))

    def __pos__(self):
        return EvalExpr(operator.pos(self.expr_value))

    def __neg__(self):
        return EvalExpr(operator.neg(self.expr_value))

    def __invert__(self):
        if isinstance(self.expr_value, bool):
            return EvalExpr(operator.not_(self.expr_value))
        if isinstance(self.expr_value, int):
            return EvalExpr(operator.invert(self.expr_value))
        return NotImplemented

    def __floordiv__(self, other: EvalExpr):
        return EvalExpr(operator.floordiv(self.expr_value, other.expr_value))

    def __mod__(self, other: EvalExpr):
        return EvalExpr(operator.mod(self.expr_value, other.expr_value))

    def __pow__(self, other: EvalExpr):
        return EvalExpr(operator.pow(self.expr_value, other.expr_value))

    def __mul__(self, other: EvalExpr):
        return EvalExpr(operator.mul(self.expr_value, other.expr_value))

    def __add__(self, other: EvalExpr):
        return EvalExpr(operator.add(self.expr_value, other.expr_value))

    def __and__(self, other: EvalExpr):
        return EvalExpr(operator.and_(self.expr_value, other.expr_value))

    def __or__(self, other: EvalExpr):
        return EvalExpr(operator.or_(self.expr_value, other.expr_value))

    def __xor__(self, other: EvalExpr):
        return EvalExpr(operator.xor(self.expr_value, other.expr_value))

    def __lt__(self, other: EvalExpr):
        return EvalExpr(operator.lt(self.expr_value, other.expr_value))

    def __le__(self, other: EvalExpr):
        return EvalExpr(operator.le(self.expr_value, other.expr_value))

    def __eq__(self, other: EvalExpr):
        return EvalExpr(operator.eq(self.expr_value, other.expr_value))

    def __ne__(self, other: EvalExpr):
        return EvalExpr(operator.ne(self.expr_value, other.expr_value))

    def __gt__(self, other: EvalExpr):
        return EvalExpr(operator.gt(self.expr_value, other.expr_value))

    def __ge__(self, other: EvalExpr):
        return EvalExpr(operator.ge(self.expr_value, other.expr_value))


@attrs.define(repr=False, slots=False)
class FoldableExpr(ExprAnnotation):
    """AST annotation for constant folding

    The `wrapped_expr` is composed entirely of constant terms
    and should be folded into a single constant for optimization

    Attributes
    ----------
    wrapped_expr : Expr
        An expression composed entirely of ConstExpr terms
    """

    @staticmethod
    def can_fold(eval_expr: Expr) -> typing.Tuple[bool, bool]:
        """
        Parameters
        ----------
        eval_expr : Expr

        Returns
        -------
        (is_const, is_folded) : (bool, bool)
            is_const = eval_expr is an instance of ConstExpr or EvalExpr;
            is_folded = eval_expr is an instance of FoldedExpr
        """
        is_folded = isinstance(eval_expr, FoldableExpr)
        if isinstance(eval_expr, ExprAnnotation) and not is_folded:
            is_const = isinstance(
                eval_expr.wrapped_expr, (ConstExpr, EvalExpr)
            ) and not isinstance(eval_expr.wrapped_expr, Nothing)
        else:
            is_const = isinstance(eval_expr, (ConstExpr, EvalExpr)) and not isinstance(
                eval_expr, Nothing
            )
        return (is_const, is_folded)

    @staticmethod
    def try_fold(
        expr_left: Expr, expr_right: Expr, expr_type: type, *args: typing.Any
    ) -> Expr:
        """
        Parameters
        ----------
        expr_left : Expr
        expr_right : Expr
        expr_type : type
        *args
            Additional arguments passed to expr_type constructor

        Returns
        -------
        Expr

        Raises
        ------
        AssertionError
            If expr_type is not a subclass of Expr
        """
        assert issubclass(expr_type, Expr)
        # extract info from expressions
        left_const, left_folded = FoldableExpr.can_fold(expr_left)
        right_const, right_folded = FoldableExpr.can_fold(expr_right)
        # fold constant expressions
        if left_const and right_const:
            return FoldableExpr(expr_type(expr_left, expr_right, *args))
        # unwrap folded child expression and wrap combined expression
        if left_const and right_folded:
            return FoldableExpr(expr_type(expr_left, expr_right.wrapped_expr, *args))
        if left_folded and right_const:
            return FoldableExpr(expr_type(expr_left.wrapped_expr, expr_right, *args))
        # unwrap both child expressions and wrap combined expression
        if left_folded and right_folded:
            return FoldableExpr(
                expr_type(expr_left.wrapped_expr, expr_right.wrapped_expr, *args)
            )
        # cannot fold the two expressions
        return expr_type(expr_left, expr_right, *args)


@attrs.define(repr=False, slots=False)
class AddNegated(ExprAnnotation):
    """AST annotation for AddExpr subtraction

    To ignore `+` and `-` symbols after parsing,
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

        Returns
        -------
        FoldableExpr | AddNegated
        """
        if isinstance(orig_expr, FoldableExpr):
            # make sure FoldedExpr annotation is on the outside
            return FoldableExpr(AddNegated(orig_expr.wrapped_expr))
        return AddNegated(orig_expr)


@attrs.define(repr=False, slots=False)
class MultReciprocal(ExprAnnotation):
    """AST annotation for MultExpr division

    To ignore `*` and `/` symbols after parsing,
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

        Returns
        -------
        FoldableExpr | MultReciprocal
        """
        if isinstance(orig_expr, FoldableExpr):
            # make sure FoldedExpr annotation is on the outside
            return FoldableExpr(MultReciprocal(orig_expr.wrapped_expr))
        return MultReciprocal(orig_expr)
