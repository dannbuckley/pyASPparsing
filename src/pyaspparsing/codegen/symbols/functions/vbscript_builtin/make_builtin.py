"""Helper function to make a builtin Function symbol"""

from collections.abc import Callable
from functools import wraps
import re
from typing import Concatenate, ParamSpec
from ..function import ASPFunction
from ....scope import ScopeType
from ....codegen_state import CodegenState

P = ParamSpec("P")


def make_builtin_function(
    func: Callable[Concatenate[CodegenState, P], None]
) -> Callable[[], ASPFunction]:
    """Wrapper function for making VBScript builtin function symbols

    Parameters
    ----------
    func : Callable

    Returns
    -------
    partial[Function]

    Raises
    ------
    AssertionError
        If the name of func does not match r"builtin_([a-z]+)"
    """
    match_name = re.match(r"builtin_(?P<vbscript_name>[a-z]+)", func.__name__)
    assert (
        match_name is not None
    ), "Builtin function must match r'builtin_([a-z]+)' pattern"

    @wraps(func)
    def call_builtin(cg_state: CodegenState, /, *args: P.args):
        with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
            func(cg_state, *args)

    def make_function_symbol():
        return ASPFunction(match_name.groupdict()["vbscript_name"], call_builtin)

    return make_function_symbol
