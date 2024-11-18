"""VBScript builtin array functions"""

from ....codegen_state import CodegenState
from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_array(cg_state: CodegenState, /, *param_arglist):
    """"""


@make_builtin_function
def builtin_filter(
    cg_state: CodegenState,
    param_inputstring,
    param_value,
    param_include=None,
    param_compare=None,
    /,
):
    """"""


@make_builtin_function
def builtin_isarray(cg_state: CodegenState, param_variable, /):
    """"""


@make_builtin_function
def builtin_join(cg_state: CodegenState, param_list, param_delimiter=None, /):
    """"""


@make_builtin_function
def builtin_lbound(cg_state: CodegenState, param_arrayname, param_dimension=None, /):
    """"""


@make_builtin_function
def builtin_split(
    cg_state: CodegenState,
    param_expression,
    param_delimiter=None,
    param_count=None,
    param_compare=None,
    /,
):
    """"""


@make_builtin_function
def builtin_ubound(cg_state: CodegenState, param_arrayname, param_dimension=None, /):
    """"""
