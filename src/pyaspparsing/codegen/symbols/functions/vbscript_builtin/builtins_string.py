"""VBScript builtin string functions"""

from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_instr(*params):
    """"""
    param_opts: dict[int, tuple[str, ...]] = {
        2: ("param_string1", "param_string2"),
        3: ("param_start", "param_string1", "param_string2"),
        4: ("param_start", "param_string1", "param_string2", "param_compare"),
    }
    try:
        kw_params = dict(zip(param_opts[len(params)], params))
    except KeyError as ex:
        raise TypeError("InStr expects 2, 3, or 4 parameters") from ex


@make_builtin_function
def builtin_instrrev(
    param_string1, param_string2, param_start=None, param_compare=None, /
):
    """"""


@make_builtin_function
def builtin_lcase(param_string, /):
    """"""


@make_builtin_function
def builtin_left(param_string, param_length, /):
    """"""


@make_builtin_function
def builtin_len(param_string, /):
    """"""


@make_builtin_function
def builtin_ltrim(param_string, /):
    """"""


@make_builtin_function
def builtin_rtrim(param_string, /):
    """"""


@make_builtin_function
def builtin_trim(param_string, /):
    """"""


@make_builtin_function
def builtin_mid(param_string, param_start, param_length=None, /):
    """"""


@make_builtin_function
def builtin_replace(
    param_string,
    param_find,
    param_replacewith,
    param_start=None,
    param_count=None,
    param_compare=None,
    /,
):
    """"""


@make_builtin_function
def builtin_right(param_string, param_length, /):
    """"""


@make_builtin_function
def builtin_space(param_number, /):
    """"""


@make_builtin_function
def builtin_strcomp(param_string1, param_string2, param_compare=None, /):
    """"""


@make_builtin_function
def builtin_string(param_number, param_character, /):
    """"""


@make_builtin_function
def builtin_strreverse(param_string, /):
    """"""


@make_builtin_function
def builtin_ucase(param_string, /):
    """"""
