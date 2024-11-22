"""VBScript builtin string functions"""

from ....generators.codegen_state import CodegenState
from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_instr(cg_state: CodegenState, /, *params):
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
    cg_state: CodegenState,
    param_string1,
    param_string2,
    param_start=None,
    param_compare=None,
    /,
):
    """"""


@make_builtin_function
def builtin_lcase(cg_state: CodegenState, param_string, /):
    """"""


@make_builtin_function
def builtin_left(cg_state: CodegenState, param_string, param_length, /):
    """"""


@make_builtin_function
def builtin_len(cg_state: CodegenState, param_string, /):
    """"""


@make_builtin_function
def builtin_ltrim(cg_state: CodegenState, param_string, /):
    """"""


@make_builtin_function
def builtin_rtrim(cg_state: CodegenState, param_string, /):
    """"""


@make_builtin_function
def builtin_trim(cg_state: CodegenState, param_string, /):
    """"""


@make_builtin_function
def builtin_mid(
    cg_state: CodegenState, param_string, param_start, param_length=None, /
):
    """"""


@make_builtin_function
def builtin_replace(
    cg_state: CodegenState,
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
def builtin_right(cg_state: CodegenState, param_string, param_length, /):
    """"""


@make_builtin_function
def builtin_space(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_strcomp(
    cg_state: CodegenState, param_string1, param_string2, param_compare=None, /
):
    """"""


@make_builtin_function
def builtin_string(cg_state: CodegenState, param_number, param_character, /):
    """"""


@make_builtin_function
def builtin_strreverse(cg_state: CodegenState, param_string, /):
    """"""


@make_builtin_function
def builtin_ucase(cg_state: CodegenState, param_string, /):
    """"""
