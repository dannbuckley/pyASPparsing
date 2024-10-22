"""expression_evaluator module"""

from collections.abc import Callable
from functools import wraps
import operator
import typing
from ... import EvaluatorError
from .base import Expr, CompareExprType
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
    UnarySign,
    UnaryExpr,
    ExpExpr,
    ConstExpr,
    Nothing,
)
from .optimize import EvalExpr, FoldableExpr, AddNegated, MultReciprocal


reg_expr_eval: typing.Dict[type[Expr], Callable[[Expr], EvalExpr]] = {}


def evaluate_expr(fld: Expr) -> EvalExpr:
    """
    Parameters
    ----------
    fld : Expr

    Returns
    -------
    EvalExpr
    """
    if isinstance(fld, EvalExpr):
        return fld
    return reg_expr_eval[
        type(fld.wrapped_expr) if isinstance(fld, FoldableExpr) else type(fld)
    ](fld)


def create_expr_eval_func(expr_type: type[Expr]):
    """
    Parameters
    ----------
    expr_type : type[Expr]
    """
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


@create_expr_eval_func(CompareExpr)
def eval_compare_expr(fld: CompareExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a comparison expression

    Parameters
    ----------
    fld : CompareExpr
        Foldable CompareExpr object

    Returns
    -------
    EvalExpr
    """
    left = evaluate_expr(fld.left)
    right = evaluate_expr(fld.right)
    match fld.cmp_type:
        case CompareExprType.COMPARE_IS:
            # TODO
            return EvalExpr(False)
        case CompareExprType.COMPARE_ISNOT:
            # TODO
            return EvalExpr(False)
        case CompareExprType.COMPARE_EQ:
            # '=': equality
            return operator.eq(left, right)
        case CompareExprType.COMPARE_LTGT:
            # '<>': inequality
            return operator.ne(left, right)
        case CompareExprType.COMPARE_GT:
            # '>': greater than
            return operator.gt(left, right)
        case CompareExprType.COMPARE_GTEQ:
            # '>=': greater than or equal to
            return operator.ge(left, right)
        case CompareExprType.COMPARE_LT:
            # '<': less than
            return operator.lt(left, right)
        case CompareExprType.COMPARE_LTEQ:
            # '<=': less than or equal to
            return operator.le(left, right)


@create_expr_eval_func(ConcatExpr)
def eval_concat_expr(fld: ConcatExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a string concatenation expression

    Parameters
    ----------
    fld : ConcatExpr
        Foldable ConcatExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.add(
        # reduce left subtree and cast to string
        evaluate_expr(fld.left).str_cast(),
        # reduce right subtree and cast to string
        evaluate_expr(fld.right).str_cast(),
    )


@create_expr_eval_func(AddExpr)
def eval_add_expr(fld: AddExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate an addition/subtraction expression

    Parameters
    ----------
    fld : AddExpr
        Foldable AddExpr object

    Returns
    -------
    EvalExpr
    """

    def _eval_add_term(term: Expr) -> EvalExpr:
        """
        Parameters
        ----------
        term : Expr
            Foldable subtree of an AddExpr object

        Returns
        -------
        EvalExpr
        """
        if isinstance(term, AddNegated):
            return operator.neg(evaluate_expr(term.wrapped_expr))
        return evaluate_expr(term)

    return operator.add(
        # reduce left subtree
        _eval_add_term(fld.left),
        # reduce right subtree
        _eval_add_term(fld.right),
    )


@create_expr_eval_func(ModExpr)
def eval_mod_expr(fld: ModExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a modulo expression

    Parameters
    ----------
    fld : ModExpr
        Foldable ModExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.mod(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
    )


@create_expr_eval_func(IntDivExpr)
def eval_int_div_expr(fld: IntDivExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate an integer division expression

    Parameters
    ----------
    fld : IntDivExpr
        Foldable IntDivExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.floordiv(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
    )


@create_expr_eval_func(MultExpr)
def eval_mult_expr(fld: MultExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a multiplcation/division expression

    Parameters
    ----------
    fld : MultExpr
        Foldable MultExpr object

    Returns
    -------
    EvalExpr
    """

    def _eval_mult_term(term: Expr) -> EvalExpr:
        """
        Parameters
        ----------
        term : Expr
            Foldable subtree of a MultExpr object

        Returns
        -------
        EvalExpr
        """
        if isinstance(term, MultReciprocal):
            return evaluate_expr(term.wrapped_expr).reciprocal()
        return evaluate_expr(term)

    return operator.mul(
        # reduce left subtree
        _eval_mult_term(fld.left),
        # reduce right subtree
        _eval_mult_term(fld.right),
    )


@create_expr_eval_func(UnaryExpr)
def eval_unary_expr(fld: UnaryExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a signed unary expression

    Parameters
    ----------
    fld : UnaryExpr
        Foldable UnaryExpr object

    Returns
    -------
    EvalExpr
    """
    term = evaluate_expr(fld.term)
    return operator.pos(term) if fld.sign == UnarySign.SIGN_POS else operator.neg(term)


@create_expr_eval_func(ExpExpr)
def eval_exp_expr(fld: ExpExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate an exponentiation expression

    Parameters
    ----------
    fld : ExpExpr
        Foldable ExpExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.pow(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
    )
