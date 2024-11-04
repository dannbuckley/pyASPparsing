"""VBScript builtin other functions"""

from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_createobject(param_type, param_location=None, /):
    """"""


@make_builtin_function
def builtin_eval(param_expression, /):
    """"""


@make_builtin_function
def builtin_isempty(param_expression, /):
    """"""


@make_builtin_function
def builtin_isnull(param_expression, /):
    """"""


@make_builtin_function
def builtin_isnumeric(param_expression, /):
    """"""


@make_builtin_function
def builtin_isobject(param_expression, /):
    """"""


@make_builtin_function
def builtin_rgb(param_red, param_green, param_blue, /):
    """"""


@make_builtin_function
def builtin_round(param_expression, param_numdecimalplaces=None, /):
    """"""


@make_builtin_function
def builtin_scriptengine():
    """"""


@make_builtin_function
def builtin_scriptenginebuildversion():
    """"""


@make_builtin_function
def builtin_scriptenginemajorversion():
    """"""


@make_builtin_function
def builtin_scriptengineminorversion():
    """"""


@make_builtin_function
def builtin_typename(param_varname, /):
    """"""


@make_builtin_function
def builtin_vartype(param_varname, /):
    """"""
