"""VBScript builtin other functions"""

from ....generators.codegen_state import CodegenState
from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_createobject(cg_state: CodegenState, param_type, param_location=None, /):
    """"""


@make_builtin_function
def builtin_eval(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_isempty(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_isnull(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_isnumeric(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_isobject(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_rgb(cg_state: CodegenState, param_red, param_green, param_blue, /):
    """"""


@make_builtin_function
def builtin_round(
    cg_state: CodegenState, param_expression, param_numdecimalplaces=None, /
):
    """"""


@make_builtin_function
def builtin_scriptengine(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_scriptenginebuildversion(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_scriptenginemajorversion(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_scriptengineminorversion(cg_state: CodegenState, /):
    """"""


@make_builtin_function
def builtin_typename(cg_state: CodegenState, param_varname, /):
    """"""


@make_builtin_function
def builtin_vartype(cg_state: CodegenState, param_varname, /):
    """"""
