"""VBScript builtin format functions"""

from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_formatcurrency(
    param_expression,
    param_numdigafterdec=None,
    param_incleadingdig=None,
    param_useparfornegnum=None,
    param_groupdig=None,
    /,
):
    """"""


@make_builtin_function
def builtin_formatdatetime(param_date, param_format, /):
    """"""


@make_builtin_function
def builtin_formatnumber(
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
    param_expression,
    param_numdigafterdec=None,
    param_incleadingdig=None,
    param_useparfornegnum=None,
    param_groupdig=None,
    /,
):
    """"""
