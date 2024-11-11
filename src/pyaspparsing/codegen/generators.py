"""Code generator state functions"""

from collections.abc import Callable
from functools import wraps
import sys
from typing import Optional, Any, IO
import attrs
from jinja2 import Environment
from ..ast.ast_types import (
    GlobalStmt,
    # special constructs
    ProcessingDirective,
    IncludeFile,
    OutputText,
    # global statements
    OptionExplicit,
    ClassDecl,
    FieldDecl,
    ConstDecl,
    SubDecl,
    FunctionDecl,
    # block statements
    VarDecl,
    RedimStmt,
    IfStmt,
    WithStmt,
    SelectStmt,
    LoopStmt,
    ForStmt,
    # inline statements
    AssignStmt,
    CallStmt,
    SubCallStmt,
    ErrorStmt,
    ExitStmt,
    EraseStmt,
)


@attrs.define
class CodegenState:
    """"""

    jinja_env: Environment
    script_file: IO
    template_file: IO
    error_file: IO = attrs.field(default=sys.stderr)
    _in_script_block: bool = attrs.field(default=False, repr=False, init=False)
    _script_blocks: list[str] = attrs.field(
        default=attrs.Factory(list), repr=False, init=False
    )

    @property
    def in_script_block(self) -> bool:
        """Flag indicating whether the previous global statement was
        part of a script block (as opposed to a global output block)

        Returns
        -------
        bool
        """
        return self._in_script_block

    @property
    def current_script_block(self) -> Optional[str]:
        """Name of the current script block;
        returns None if no script blocks have been started yet

        Returns
        -------
        str | None
        """
        if len(self._script_blocks) == 0:
            return None
        return self._script_blocks[-1]

    def start_script_block(self):
        """"""
        assert not self._in_script_block
        self._in_script_block = True
        self._script_blocks.append(f"__script_block_{len(self._script_blocks)}")
        print(
            self.jinja_env.variable_start_string
            + f"- {self.current_script_block} -"
            + self.jinja_env.variable_end_string,
            file=self.template_file,
        )
        print(f"\nSTART {self.current_script_block}", file=self.script_file)

    def end_script_block(self):
        """"""
        assert self._in_script_block and self.current_script_block is not None
        self._in_script_block = False
        print(f"END {self.current_script_block}", file=self.script_file)


reg_stmt_cg: dict[type[GlobalStmt], Callable[[GlobalStmt, CodegenState], Any]] = {}


def codegen_global_stmt(
    stmt: GlobalStmt, cg_state: CodegenState, *, top_level: bool = False
) -> Any:
    """
    Parameters
    ----------
    stmt : GlobalStmt
    cg_state : CodegenState
    top_level : bool, default=False
        Set this to True if `stmt` comes directly from a `Program` object

    Returns
    -------
    Any
    """
    if top_level:
        if cg_state.in_script_block and isinstance(stmt, OutputText):
            cg_state.end_script_block()
        elif not cg_state.in_script_block and not isinstance(
            stmt,
            (OutputText, IncludeFile, ProcessingDirective, OptionExplicit, ErrorStmt),
        ):
            cg_state.start_script_block()
    return reg_stmt_cg[type(stmt)](stmt, cg_state)


def create_global_cg_func(stmt_type: type[GlobalStmt]):
    """
    Parameters
    ----------
    stmt_type : type[GlobalStmt]
    """
    assert issubclass(
        stmt_type, GlobalStmt
    ), "stmt_type must be a subclass of GlobalStmt"

    def wrap_func(func: Callable[[GlobalStmt], Any]):
        @wraps(func)
        def perform_cg(stmt: GlobalStmt, cg_state: CodegenState):
            return func(stmt, cg_state)

        reg_stmt_cg[stmt_type] = perform_cg
        return perform_cg

    return wrap_func


@create_global_cg_func(ProcessingDirective)
def cg_processing_directive(stmt: ProcessingDirective, cg_state: CodegenState) -> Any:
    """"""
    print("Processing directive", file=cg_state.script_file)


@create_global_cg_func(IncludeFile)
def cg_include_file(stmt: IncludeFile, cg_state: CodegenState) -> Any:
    """"""
    print("Unresolved include", file=cg_state.error_file)


@create_global_cg_func(OutputText)
def cg_output_text(stmt: OutputText, cg_state: CodegenState) -> Any:
    """"""
    if not (all(map(lambda x: x.isspace(), stmt.chunks)) and len(stmt.directives) == 0):
        print("Output text", file=cg_state.template_file)


@create_global_cg_func(OptionExplicit)
def cg_option_explicit(stmt: OptionExplicit, cg_state: CodegenState) -> Any:
    """"""
    print("Option Explicit", file=cg_state.script_file)


@create_global_cg_func(ClassDecl)
def cg_class_decl(stmt: ClassDecl, cg_state: CodegenState) -> Any:
    """"""
    print("Class declaration", file=cg_state.script_file)


@create_global_cg_func(FieldDecl)
def cg_field_decl(stmt: FieldDecl, cg_state: CodegenState) -> Any:
    """"""
    print("Field declaration", file=cg_state.script_file)


@create_global_cg_func(ConstDecl)
def cg_const_decl(stmt: ConstDecl, cg_state: CodegenState) -> Any:
    """"""
    print("Constant declaration", file=cg_state.script_file)


@create_global_cg_func(SubDecl)
def cg_sub_decl(stmt: SubDecl, cg_state: CodegenState) -> Any:
    """"""
    # map(codegen_global_stmt, stmt.method_stmt_list)
    print("Sub declaration", file=cg_state.script_file)


@create_global_cg_func(FunctionDecl)
def cg_function_decl(stmt: FunctionDecl, cg_state: CodegenState) -> Any:
    """"""
    # map(codegen_global_stmt, stmt.method_stmt_list)
    print("Function declaration", file=cg_state.script_file)


@create_global_cg_func(VarDecl)
def cg_var_decl(stmt: VarDecl, cg_state: CodegenState) -> Any:
    """"""
    print("Variable declaration", file=cg_state.script_file)


@create_global_cg_func(RedimStmt)
def cg_redim_stmt(stmt: RedimStmt, cg_state: CodegenState) -> Any:
    """"""
    print("Redim statement", file=cg_state.script_file)


@create_global_cg_func(IfStmt)
def cg_if_stmt(stmt: IfStmt, cg_state: CodegenState) -> Any:
    """"""
    # map(codegen_global_stmt, stmt.block_stmt_list)
    # else_cg = [
    #     map(codegen_global_stmt, else_ast.stmt_list) for else_ast in stmt.else_stmt_list
    # ]
    print("If statement", file=cg_state.script_file)


@create_global_cg_func(WithStmt)
def cg_with_stmt(stmt: WithStmt, cg_state: CodegenState) -> Any:
    """"""
    # map(codegen_global_stmt, stmt.block_stmt_list)
    print("With statement", file=cg_state.script_file)


@create_global_cg_func(SelectStmt)
def cg_select_stmt(stmt: SelectStmt, cg_state: CodegenState) -> Any:
    """"""
    # case_cg = [
    #     map(codegen_global_stmt, case_stmt.block_stmt_list)
    #     for case_stmt in stmt.case_stmt_list
    # ]
    print("Select statement", file=cg_state.script_file)


@create_global_cg_func(LoopStmt)
def cg_loop_stmt(stmt: LoopStmt, cg_state: CodegenState) -> Any:
    """"""
    # map(codegen_global_stmt, stmt.block_stmt_list)
    print("Loop statement", file=cg_state.script_file)


@create_global_cg_func(ForStmt)
def cg_for_stmt(stmt: ForStmt, cg_state: CodegenState) -> Any:
    """"""
    # map(codegen_global_stmt, stmt.block_stmt_list)
    print("For statement", file=cg_state.script_file)


@create_global_cg_func(AssignStmt)
def cg_assign_stmt(stmt: AssignStmt, cg_state: CodegenState) -> Any:
    """"""
    print("Assign statement", file=cg_state.script_file)


@create_global_cg_func(CallStmt)
def cg_call_stmt(stmt: CallStmt, cg_state: CodegenState) -> Any:
    """"""
    print("Call statement", file=cg_state.script_file)


@create_global_cg_func(SubCallStmt)
def cg_sub_call_stmt(stmt: SubCallStmt, cg_state: CodegenState) -> Any:
    """"""
    print("Sub-call statement", file=cg_state.script_file)


@create_global_cg_func(ErrorStmt)
def cg_error_stmt(stmt: ErrorStmt, cg_state: CodegenState) -> Any:
    """"""
    print("Error statement", file=cg_state.script_file)


@create_global_cg_func(ExitStmt)
def cg_exit_stmt(stmt: ExitStmt, cg_state: CodegenState) -> Any:
    """"""
    print("Exit statement", file=cg_state.script_file)


@create_global_cg_func(EraseStmt)
def cg_erase_stmt(stmt: EraseStmt, cg_state: CodegenState) -> Any:
    """"""
    print("Erase statement", file=cg_state.script_file)
