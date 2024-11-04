"""Helper function to make a builtin Function symbol"""

from collections.abc import Callable
from functools import partial
import re
from ..function import Function


def make_builtin_function(func: Callable):
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
    return partial(
        Function, symbol_name=match_name.groupdict()["vbscript_name"], func=func
    )
