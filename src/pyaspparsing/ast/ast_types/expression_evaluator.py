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
                ), f"Expected {expr_type.__name__}, got {type(fld.wrapped_expr).__name__} instead"
                return func(fld.wrapped_expr)
            assert isinstance(
                fld, expr_type
            ), f"Expected {expr_type.__name__}, got {type(fld).__name__} instead"
            return func(fld)

        reg_expr_eval[expr_type] = check_expr_type
        return check_expr_type

    return wrap_func


@create_expr_eval_func(ImpExpr)
def eval_imp_expr(fld: ImpExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate an implication (Imp) expression

    Parameters
    ----------
    fld : ImpExpr
        Foldable ImpExpr object

    Returns
    -------
    EvalExpr
    """
    # Imp = (Not left) Or right
    return operator.or_(
        # reduce and invert left subtree
        operator.invert(evaluate_expr(fld.left)),
        # reduce right subtree
        evaluate_expr(fld.right),
    )


@create_expr_eval_func(EqvExpr)
def eval_eqv_expr(fld: EqvExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate an equivalence (Eqv) expression

    Parameters
    ----------
    fld : EqvExpr
        Foldable EqvExpr object

    Returns
    -------
    EvalExpr
    """
    # Eqv = Not (left Xor right)
    return operator.invert(
        operator.xor(
            # reduce left subtree
            evaluate_expr(fld.left),
            # reduce right subtree
            evaluate_expr(fld.right),
        )
    )


@create_expr_eval_func(XorExpr)
def eval_xor_expr(fld: XorExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate an exclusive disjunction (Xor) expression

    Parameters
    ----------
    fld : XorExpr
        Foldable XorExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.xor(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
    )


@create_expr_eval_func(OrExpr)
def eval_or_expr(fld: OrExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate an inclusive disjunction (Or) expression

    Parameters
    ----------
    fld : OrExpr
        Foldable OrExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.or_(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
    )


@create_expr_eval_func(AndExpr)
def eval_and_expr(fld: AndExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a conjunction (And) expression

    Parameters
    ----------
    fld : AndExpr
        Foldable AndExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.and_(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
    )


@create_expr_eval_func(NotExpr)
def eval_not_expr(fld: NotExpr) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a complement (Not) expression

    Parameters
    ----------
    fld : NotExpr
        Foldable NotExpr object

    Returns
    -------
    EvalExpr
    """
    return operator.invert(evaluate_expr(fld.term))


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
        case CompareExprType.COMPARE_IS | CompareExprType.COMPARE_ISNOT:
            raise EvaluatorError("Object reference comparisons cannot be folded")
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


@create_expr_eval_func(AddNegated)
def eval_add_negated(fld: AddNegated) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a negation annotation

    Parameters
    ----------
    fld : AddNegated
        Foldable AddNegated object

    Returns
    -------
    EvalExpr
    """
    return operator.neg(evaluate_expr(fld.wrapped_expr))


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
    return operator.add(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
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


@create_expr_eval_func(MultReciprocal)
def eval_mult_reciprocal(fld: MultReciprocal) -> EvalExpr:
    """NOT CALLED DIRECTLY

    Evaluate a reciprocal annotation

    Parameters
    ----------
    fld : MultReciprocal
        Foldable MultReciprocal object

    Returns
    -------
    EvalExpr
    """
    return evaluate_expr(fld.wrapped_expr).reciprocal()


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
    return operator.mul(
        # reduce left subtree
        evaluate_expr(fld.left),
        # reduce right subtree
        evaluate_expr(fld.right),
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
