"""VBScript builtin conversion functions"""

from ....generators.codegen_state import CodegenState
from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_asc(cg_state: CodegenState, param_string, /):
    """"""


@make_builtin_function
def builtin_cbool(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_cbyte(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_ccur(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_cdate(cg_state: CodegenState, param_date, /):
    """"""


@make_builtin_function
def builtin_cdbl(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_chr(cg_state: CodegenState, param_charcode, /):
    """"""


@make_builtin_function
def builtin_cint(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_clng(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_csng(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_cstr(cg_state: CodegenState, param_expression, /):
    """"""


@make_builtin_function
def builtin_hex(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_oct(cg_state: CodegenState, param_number, /):
    """"""
