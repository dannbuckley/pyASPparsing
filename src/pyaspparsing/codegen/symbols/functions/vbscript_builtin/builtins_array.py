"""VBScript builtin array functions"""

from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_array(*param_arglist):
    """"""


@make_builtin_function
def builtin_filter(
    param_inputstring, param_value, param_include=None, param_compare=None, /
):
    """"""


@make_builtin_function
def builtin_isarray(param_variable, /):
    """"""


@make_builtin_function
def builtin_join(param_list, param_delimiter=None, /):
    """"""


@make_builtin_function
def builtin_lbound(param_arrayname, param_dimension=None, /):
    """"""


@make_builtin_function
def builtin_split(
    param_expression, param_delimiter=None, param_count=None, param_compare=None, /
):
    """"""


@make_builtin_function
def builtin_ubound(param_arrayname, param_dimension=None, /):
    """"""
