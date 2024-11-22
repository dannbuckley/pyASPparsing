"""VBScript builtin math functions"""

from ....generators.codegen_state import CodegenState
from .make_builtin import make_builtin_function


@make_builtin_function
def builtin_abs(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_atn(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_cos(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_exp(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_int(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_fix(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_log(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_rnd(cg_state: CodegenState, param_number=None, /):
    """"""


@make_builtin_function
def builtin_sgn(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_sin(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_sqr(cg_state: CodegenState, param_number, /):
    """"""


@make_builtin_function
def builtin_tan(cg_state: CodegenState, param_number, /):
    """"""
