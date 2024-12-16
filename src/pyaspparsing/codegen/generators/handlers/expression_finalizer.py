"""expression_finalizer module"""

from collections.abc import Callable
from functools import wraps
import operator
from ....ast.ast_types import Expr, EvalExpr, ConcatExpr, LeftExpr
from ...symbols import ValueSymbol
from ..codegen_state import CodegenState

reg_expr_fin: dict[type[Expr], Callable[[Expr, CodegenState], Expr]] = {}


def finalize_expr(exp: Expr, cg_state: CodegenState) -> Expr:
    """Try to finalize the given expression using
    the given code generator state

    Parameters
    ----------
    exp : Expr
    cg_state : CodegenState

    Returns
    -------
    Expr
    """
    if isinstance(exp, EvalExpr) or type(exp) not in reg_expr_fin:
        return exp
    return reg_expr_fin[type(exp)](exp, cg_state)


def create_expr_fin_func(expr_type: type[Expr]):
    """
    Parameters
    ----------
    expr_type : type[Expr]
    """
    assert issubclass(expr_type, Expr)

    def wrap_func(func: Callable[[Expr, CodegenState], Expr]):
        @wraps(func)
        def run_finalizer(exp: Expr, cg_state: CodegenState) -> Expr:
            return func(exp, cg_state)

        reg_expr_fin[expr_type] = run_finalizer
        return run_finalizer

    return wrap_func


@create_expr_fin_func(ConcatExpr)
def fin_concat_expr(exp: ConcatExpr, cg_state: CodegenState) -> Expr:
    fin_left = finalize_expr(exp.left, cg_state)
    fin_right = finalize_expr(exp.right, cg_state)
    if isinstance(fin_left, EvalExpr) and isinstance(fin_right, EvalExpr):
        return operator.add(fin_left.str_cast(), fin_right.str_cast())
    return exp


@create_expr_fin_func(LeftExpr)
def fin_left_expr(exp: Expr, cg_state: CodegenState) -> Expr:
    res_sym = cg_state.sym_table.resolve_symbol(
        exp, cg_state.scope_mgr.current_environment[:-1]
    )
    if len(res_sym) == 0:
        return exp
    if isinstance(res_sym[-1].symbol, ValueSymbol):
        return res_sym[-1].symbol.value
    return exp
