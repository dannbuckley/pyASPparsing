"""Registry for code generation functions"""

from collections.abc import Callable  # pylint: disable=E0611
from functools import wraps
from typing import Optional
from ...ast.ast_types import (
    GlobalStmt,
    OutputText,
    IncludeFile,
    ProcessingDirective,
    OptionExplicit,
    ErrorStmt,
    FunctionDecl,
    SubDecl,
)
from ..scope import ScopeType
from .codegen_state import CodegenState
from .codegen_return import CodegenReturn

reg_stmt_cg: dict[
    type[GlobalStmt], Callable[[GlobalStmt, CodegenState], CodegenReturn]
] = {}


def create_global_cg_func(
    stmt_type: type[GlobalStmt], *, enters_scope: Optional[ScopeType] = None
):
    """
    Parameters
    ----------
    stmt_type : type[GlobalStmt]
        Statement type that will be handled by the decorated function
    enters_scope : ScopeType | None, default=None
        If not None, this scope type will be created/entered before
        calling the decorated function
    """
    if not issubclass(stmt_type, GlobalStmt):
        raise TypeError("stmt_type must be a subclass of GlobalStmt")

    def wrap_codegen_func(
        func: Callable[[GlobalStmt, CodegenState, CodegenReturn], CodegenReturn]
    ):
        @wraps(func)
        def perform_codegen(stmt: GlobalStmt, cg_state: CodegenState):
            if enters_scope is None:
                return func(stmt, cg_state, CodegenReturn())
            # enter into new scope
            with cg_state.scope_mgr.temporary_scope(enters_scope):
                ret = func(stmt, cg_state, CodegenReturn())
            return ret

        reg_stmt_cg[stmt_type] = perform_codegen
        return perform_codegen

    return wrap_codegen_func


def codegen_global_stmt(
    stmt: GlobalStmt, cg_state: CodegenState, *, top_level: bool = False
):
    """
    Parameters
    ----------
    stmt : GlobalStmt
    cg_state : CodegenState
    top_level : bool, default=False
        Set this to True if `stmt` comes directly from a `Program` object

    Returns
    -------
    CodegenReturn | None
        Returns None if `top_level` is True
    """
    if top_level:
        if cg_state.in_script_block and isinstance(stmt, OutputText):
            cg_state.end_script_block()
        elif not cg_state.in_script_block and not isinstance(
            stmt,
            (
                OutputText,
                IncludeFile,
                ProcessingDirective,
                OptionExplicit,
                ErrorStmt,
                FunctionDecl,
                SubDecl,
            ),
        ):
            cg_state.start_script_block()
        ret = str(reg_stmt_cg[type(stmt)](stmt, cg_state))
        print(
            ret,
            end="" if len(ret) == 0 else "\n",
            file=cg_state.script_file,
        )
        return None
    return reg_stmt_cg[type(stmt)](stmt, cg_state)
