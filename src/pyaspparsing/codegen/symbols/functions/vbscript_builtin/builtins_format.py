"""VBScript builtin format functions"""

from ....codegen_state import CodegenState
from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_formatcurrency(
    cg_state: CodegenState,
    param_expression,
    param_numdigafterdec=None,
    param_incleadingdig=None,
    param_useparfornegnum=None,
    param_groupdig=None,
    /,
):
    """"""


@make_builtin_function
def builtin_formatdatetime(cg_state: CodegenState, param_date, param_format, /):
    """"""


@make_builtin_function
def builtin_formatnumber(
    cg_state: CodegenState,
    param_expression,
    param_numdigafterdec=None,
    param_incleadingdig=None,
    param_useparfornegnum=None,
    param_groupdig=None,
    /,
):
    """"""


@make_builtin_function
def builtin_formatpercent(
    cg_state: CodegenState,
    param_expression,
    param_numdigafterdec=None,
    param_incleadingdig=None,
    param_useparfornegnum=None,
    param_groupdig=None,
    /,
):
    """"""
