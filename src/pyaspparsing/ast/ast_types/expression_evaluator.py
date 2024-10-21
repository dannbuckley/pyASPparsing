"""expression_evaluator module"""

from collections.abc import Callable
from functools import wraps
import operator
import typing
from ... import EvaluatorError
from .base import Expr
from .expressions import (
    ImpExpr,
    EqvExpr,
    XorExpr,
    OrExpr,
    AndExpr,
    NotExpr,
    CompareExpr,
    ConcatExpr,
    AddExpr,
    ModExpr,
    IntDivExpr,
    MultExpr,
    UnaryExpr,
    ExpExpr,
    ConstExpr,
    Nothing,
)
from .optimize import EvalExpr, FoldableExpr, AddNegated, MultReciprocal


reg_expr_eval: typing.Dict[type[Expr], Callable[[Expr], EvalExpr]] = {}


def create_expr_eval_func(expr_type: type[Expr]):
    assert issubclass(expr_type, Expr), "expr_type must be a subclass of Expr"

    def wrap_func(func: Callable[[Expr], EvalExpr]):
        @wraps(func)
        def check_expr_type(fld: Expr) -> EvalExpr:
            if isinstance(fld, FoldableExpr):
                assert isinstance(
                    fld.wrapped_expr, expr_type
                ), f"Tried to evaluate an expression of type {expr_type.__name__}, got {type(fld.wrapped_expr).__name__} instead"
                return func(fld.wrapped_expr)
            assert isinstance(
                fld, expr_type
            ), f"Tried to evaluate an expression of type {expr_type.__name__}, got {type(fld).__name__} instead"
            return func(fld)

        reg_expr_eval[expr_type] = check_expr_type
        return check_expr_type

    return wrap_func


@create_expr_eval_func(UnaryExpr)
def eval_unary_expr(fld: UnaryExpr) -> EvalExpr:
    """Evaluate a unary signed expression

    Parameters
    ----------
    fld : UnaryExpr

    Returns
    -------
    EvalExpr
    """


@create_expr_eval_func(ExpExpr)
def eval_exp_expr(fld: ExpExpr) -> EvalExpr:
    """Evaluate an exponentiation expression

    Parameters
    ----------
    fld : ExpExpr

    Returns
    -------
    EvalExpr
    """
    left = fld.left
    if not isinstance(left, EvalExpr):
        # need to reduce left subtree
        left = reg_expr_eval[type(left)](left)
    right = fld.right
    if not isinstance(right, EvalExpr):
        # need to reduce right subtree
        right = reg_expr_eval[type(right)](right)
    return EvalExpr(operator.pow(left, right))
