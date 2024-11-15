"""Code generator state functions"""

from __future__ import annotations
from collections.abc import Callable
from functools import wraps
from typing import Optional
import attrs
from attrs.validators import instance_of
from ..ast.ast_types import (
    GlobalStmt,
    EvalExpr,
    LeftExpr,
    # special constructs
    ProcessingDirective,
    IncludeFile,
    OutputText,
    OutputDirective,
    OutputType,
    # global statements
    OptionExplicit,
    ClassDecl,
    FieldDecl,
    ConstDecl,
    ArgModifierType,
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
from .scope import ScopeType
from .symbols import ValueSymbol, ArraySymbol
from .symbols.symbol import (
    ValueMethodArgument,
    ReferenceMethodArgument,
    FunctionReturnSymbol,
    ConstantSymbol,
    ForLoopRangeTargetSymbol,
    ForLoopIteratorTargetSymbol,
)
from .codegen_state import CodegenState


@attrs.define
class CodegenReturn:
    """Return value for code generation functions"""

    indent_width: int = attrs.field(default=4, validator=instance_of(int), kw_only=True)
    _script_lines: list[str] = attrs.field(default=attrs.Factory(list), init=False)

    def __str__(self):
        return "\n".join(self._script_lines)

    def append(self, line: str):
        """
        Parameters
        ----------
        line : str
        """
        if not isinstance(line, str):
            raise ValueError("line must be a string")
        self._script_lines.append(line)

    def combine(self, other: CodegenReturn, *, indent: bool = True):
        """Append the content of `other` to the current instance

        Parameters
        ----------
        other : CodegenReturn
        indent : bool, default=True
        """
        # pylint: disable=W0212
        #         ~~~~~~~~~~~~~ _script_lines is "protected",
        #                       but we're accessing from the same class
        assert isinstance(other, CodegenReturn)
        self._script_lines.extend(
            map(lambda x: (" " * self.indent_width) + x, other._script_lines)
            if indent
            else other._script_lines
        )


reg_stmt_cg: dict[
    type[GlobalStmt], Callable[[GlobalStmt, CodegenState], CodegenReturn]
] = {}


def codegen_global_stmt(
    stmt: GlobalStmt, cg_state: CodegenState, *, top_level: bool = False
) -> Optional[CodegenReturn]:
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


def create_global_cg_func(
    stmt_type: type[GlobalStmt], *, enters_scope: Optional[ScopeType] = None
):
    """
    Parameters
    ----------
    stmt_type : type[GlobalStmt]
    """
    assert issubclass(
        stmt_type, GlobalStmt
    ), "stmt_type must be a subclass of GlobalStmt"

    def wrap_func(
        func: Callable[[GlobalStmt, CodegenState, CodegenReturn], CodegenReturn]
    ):
        @wraps(func)
        def perform_cg(stmt: GlobalStmt, cg_state: CodegenState):
            if enters_scope is None:
                return func(stmt, cg_state, CodegenReturn())
            with cg_state.scope_mgr.temporary_scope(enters_scope):
                ret = func(stmt, cg_state, CodegenReturn())
            return ret

        reg_stmt_cg[stmt_type] = perform_cg
        return perform_cg

    return wrap_func


@create_global_cg_func(ProcessingDirective)
def cg_processing_directive(
    stmt: ProcessingDirective, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for processing directive

    Parameters
    ----------
    stmt : ProcessingDirective
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Processing directive")
    return cg_ret


@create_global_cg_func(OptionExplicit)
def cg_option_explicit(
    stmt: OptionExplicit, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Handler for Option Explicit statement

    Parameters
    ----------
    stmt : OptionExplicit
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Option Explicit")
    cg_state.sym_table.set_explicit()
    return cg_ret


@create_global_cg_func(ErrorStmt)
def cg_error_stmt(
    stmt: ErrorStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Handler for error statement

    Parameters
    ----------
    stmt : ErrorStmt
    cg_state: CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Error statement")
    return cg_ret


@create_global_cg_func(IncludeFile)
def cg_include_file(
    stmt: IncludeFile, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Handler for (unresolved) includes

    Parameters
    ----------
    stmt : IncludeFile
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    print(f"Unresolved include: {stmt.include_path}", file=cg_state.error_file)
    return cg_ret


@create_global_cg_func(OutputText)
def cg_output_text(
    stmt: OutputText, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for output text

    Parameters
    ----------
    stmt : OutputText
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    if not (all(map(lambda x: x.isspace(), stmt.chunks)) and len(stmt.directives) == 0):
        for output in stmt.stitch():
            match output[0]:
                case OutputType.OUTPUT_RAW:
                    print(output[1], end="", file=cg_state.template_file)
                case OutputType.OUTPUT_DIRECTIVE:
                    # assert for type inference
                    assert isinstance(output[1], OutputDirective)
                    out_expr = output[1].output_expr
                    # check if the expression can be evaluated
                    if isinstance(out_expr, EvalExpr):
                        # print directly to template as string
                        print(
                            out_expr.str_cast().expr_value,
                            end="",
                            file=cg_state.template_file,
                        )
                        continue
                    elif isinstance(out_expr, LeftExpr):
                        # check if the left expression represents a value
                        res_out = cg_state.sym_table.resolve_symbol(
                            out_expr, cg_state.scope_mgr.current_environment
                        )
                        if len(res_out) == 1:
                            sym_out = res_out[0].symbol
                            if isinstance(sym_out, ValueSymbol) and isinstance(
                                sym_out.value, EvalExpr
                            ):
                                print(
                                    sym_out.value.str_cast().expr_value,
                                    end="",
                                    file=cg_state.template_file,
                                )
                                continue
                            elif isinstance(sym_out, ArraySymbol):
                                try:
                                    if isinstance(
                                        (sym_arr_val := sym_out.retrieve(out_expr)),
                                        EvalExpr,
                                    ):
                                        print(
                                            sym_arr_val.str_cast().expr_value,
                                            end="",
                                            file=cg_state.template_file,
                                        )
                                        continue
                                except AssertionError:
                                    # could not evaluate array indices
                                    pass
                    # register output expression
                    expr_name = cg_state.add_output_expr(output[1].output_expr)
                    print(
                        "{{- " + expr_name + " -}}", end="", file=cg_state.template_file
                    )
                    cg_ret.append(f"Create output expression {expr_name}")
    return cg_ret


@create_global_cg_func(VarDecl)
def cg_var_decl(
    stmt: VarDecl, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for variable declaration

    Parameters
    ----------
    stmt : VarDecl
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Variable declaration")
    for var_name in stmt.var_name:
        cg_state.add_symbol(
            ValueSymbol.from_var_name(var_name)
            if len(var_name.array_rank_list) == 0
            else ArraySymbol.from_var_name(var_name)
        )
    return cg_ret


@create_global_cg_func(FieldDecl)
def cg_field_decl(
    stmt: FieldDecl, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for field declaration

    Parameters
    ----------
    stmt : FieldDecl
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Field declaration")
    cg_state.add_symbol(
        ValueSymbol.from_field_name(stmt.field_name, stmt.access_mod)
        if len(stmt.field_name.array_rank_list) == 0
        else ArraySymbol.from_field_name(stmt.field_name, stmt.access_mod)
    )
    for var_name in stmt.other_vars:
        cg_state.add_symbol(
            ValueSymbol.from_var_name(var_name, access_mod=stmt.access_mod)
            if len(var_name.array_rank_list) == 0
            else ArraySymbol.from_var_name(var_name, access_mod=stmt.access_mod)
        )
    return cg_ret


@create_global_cg_func(ConstDecl)
def cg_const_decl(
    stmt: ConstDecl, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for constant declaration

    Parameters
    ----------
    stmt : ConstDecl
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Constant declaration")
    for const_item in stmt.const_list:
        cg_state.add_symbol(
            ConstantSymbol(
                const_item.extended_id.id_code,
                stmt.access_mod,
                const_item.const_expr.expr_value,
            )
        )
    return cg_ret


@create_global_cg_func(RedimStmt)
def cg_redim_stmt(
    stmt: RedimStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for redim statement

    Parameters
    ----------
    stmt : RedimStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Redim statement")
    return cg_ret


@create_global_cg_func(EraseStmt)
def cg_erase_stmt(
    stmt: EraseStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for erase statement

    Parameters
    ----------
    stmt : EraseStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Erase statement")
    return cg_ret


@create_global_cg_func(AssignStmt)
def cg_assign_stmt(
    stmt: AssignStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for assignment statement

    Parameters
    ----------
    stmt : AssignStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Assign statement")
    curr_env = cg_state.scope_mgr.current_environment
    scp_types = set(
        map(
            lambda x: cg_state.scope_mgr.scope_registry.nodes[x]["scope_type"], curr_env
        )
    )
    cg_state.sym_table.assign(
        stmt,
        curr_env,
        function_sub_body=(
            ScopeType.SCOPE_FUNCTION in scp_types or ScopeType.SCOPE_SUB in scp_types
        ),
    )
    return cg_ret


@create_global_cg_func(CallStmt)
def cg_call_stmt(
    stmt: CallStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for function call statement

    Parameters
    ----------
    stmt : CallStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Call statement")
    return cg_ret


@create_global_cg_func(SubCallStmt)
def cg_sub_call_stmt(
    stmt: SubCallStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for sub call statement

    Parameters
    ----------
    stmt : SubCallStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """

    def _display_left_expr():
        nonlocal stmt
        yield stmt.left_expr.sym_name
        for idx in range(stmt.left_expr.end_idx):
            if idx in stmt.left_expr.subnames:
                yield f".{stmt.left_expr.subnames[idx]}"
            elif idx in stmt.left_expr.call_args:
                yield "(...)"
            else:
                raise ValueError("Invalid left expression")

    cg_ret.append("".join(_display_left_expr()))
    curr_env = cg_state.scope_mgr.current_environment
    scp_types = set(
        map(
            lambda x: cg_state.scope_mgr.scope_registry.nodes[x]["scope_type"], curr_env
        )
    )
    cg_state.sym_table.call(
        stmt.left_expr,
        curr_env,
        function_sub_body=(
            ScopeType.SCOPE_FUNCTION in scp_types or ScopeType.SCOPE_SUB in scp_types
        ),
    )
    return cg_ret


@create_global_cg_func(ExitStmt)
def cg_exit_stmt(
    stmt: ExitStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for exit statement

    Parameters
    ----------
    stmt : ExitStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Exit statement")
    return cg_ret


@create_global_cg_func(IfStmt, enters_scope=ScopeType.SCOPE_IF)
def cg_if_stmt(
    stmt: IfStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for if statement

    Parameters
    ----------
    stmt : IfStatement
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("If statement {")
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_IF_BRANCH):
        for block_stmt in stmt.block_stmt_list:
            cg_ret.combine(codegen_global_stmt(block_stmt, cg_state))
    for else_stmt in stmt.else_stmt_list:
        cg_ret.append(
            "} Else statement {" if else_stmt.is_else else "} ElseIf statement {"
        )
        with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_IF_BRANCH):
            for else_block_stmt in else_stmt.stmt_list:
                cg_ret.combine(codegen_global_stmt(else_block_stmt, cg_state))
    cg_ret.append("}")
    return cg_ret


@create_global_cg_func(WithStmt, enters_scope=ScopeType.SCOPE_WITH)
def cg_with_stmt(
    stmt: WithStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for with statement

    Parameters
    ----------
    stmt : WithStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("With statement {")
    for block_stmt in stmt.block_stmt_list:
        cg_ret.combine(codegen_global_stmt(block_stmt, cg_state))
    cg_ret.append("}")
    return cg_ret


@create_global_cg_func(SelectStmt, enters_scope=ScopeType.SCOPE_SELECT)
def cg_select_stmt(
    stmt: SelectStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for select statement

    Parameters
    ----------
    stmt : SelectStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Select statement {")
    for case_stmt in stmt.case_stmt_list:
        case_cg = CodegenReturn()
        case_cg.append("Case statement {")
        with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_SELECT_CASE):
            for case_block_stmt in case_stmt.block_stmt_list:
                case_cg.combine(codegen_global_stmt(case_block_stmt, cg_state))
        case_cg.append("}")
        cg_ret.combine(case_cg)
    cg_ret.append("}")
    return cg_ret


@create_global_cg_func(LoopStmt, enters_scope=ScopeType.SCOPE_LOOP)
def cg_loop_stmt(
    stmt: LoopStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for loop statement

    Parameters
    ----------
    stmt : LoopStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Loop statement {")
    for block_stmt in stmt.block_stmt_list:
        cg_ret.combine(codegen_global_stmt(block_stmt, cg_state))
    cg_ret.append("}")
    return cg_ret


@create_global_cg_func(ForStmt, enters_scope=ScopeType.SCOPE_FOR)
def cg_for_stmt(
    stmt: ForStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for for statement

    Parameters
    ----------
    stmt : ForStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("For statement {")
    if stmt.each_in_expr is not None:
        cg_state.add_symbol(
            ForLoopIteratorTargetSymbol(stmt.target_id.id_code, stmt.each_in_expr)
        )
    else:
        cg_state.add_symbol(
            ForLoopRangeTargetSymbol(
                stmt.target_id.id_code, stmt.eq_expr, stmt.to_expr, stmt.step_expr
            )
        )
    for block_stmt in stmt.block_stmt_list:
        cg_ret.combine(codegen_global_stmt(block_stmt, cg_state))
    cg_ret.append("}")
    return cg_ret


@create_global_cg_func(SubDecl, enters_scope=ScopeType.SCOPE_SUB)
def cg_sub_decl(
    stmt: SubDecl, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for sub declaration

    Parameters
    ----------
    stmt : SubDecl
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append(f"Sub {stmt.extended_id.id_code} {'{'}")
    # define arguments in sub scope
    for method_arg in stmt.method_arg_list:
        match method_arg.arg_modifier:
            case ArgModifierType.ARG_VALUE:
                cg_state.add_symbol(ValueMethodArgument(method_arg.extended_id.id_code))
            case ArgModifierType.ARG_REFERENCE:
                cg_state.add_symbol(
                    ReferenceMethodArgument(method_arg.extended_id.id_code)
                )
    for method_stmt in stmt.method_stmt_list:
        cg_ret.combine(codegen_global_stmt(method_stmt, cg_state))
    cg_ret.append(f"{'}'} // end sub {stmt.extended_id.id_code} \n")
    # define sub symbol in enclosing scope
    cg_state.add_sub_symbol(
        stmt.extended_id.id_code,
        list(map(lambda x: x.extended_id.id_code, stmt.method_arg_list)),
    )
    return cg_ret


@create_global_cg_func(FunctionDecl, enters_scope=ScopeType.SCOPE_FUNCTION)
def cg_function_decl(
    stmt: FunctionDecl, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for function declaration

    Parameters
    ----------
    stmt : FunctionDecl
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append(f"Function {stmt.extended_id.id_code} {'{'}")
    # define function name as return target
    cg_state.add_symbol(FunctionReturnSymbol(stmt.extended_id.id_code))
    # define arguments in function scope
    for method_arg in stmt.method_arg_list:
        match method_arg.arg_modifier:
            case ArgModifierType.ARG_VALUE:
                cg_state.add_symbol(ValueMethodArgument(method_arg.extended_id.id_code))
            case ArgModifierType.ARG_REFERENCE:
                cg_state.add_symbol(
                    ReferenceMethodArgument(method_arg.extended_id.id_code)
                )
    for method_stmt in stmt.method_stmt_list:
        cg_ret.combine(codegen_global_stmt(method_stmt, cg_state))
    cg_ret.append(f"{'}'} // end function {stmt.extended_id.id_code}\n")
    # define function symbol in enclosing scope
    cg_state.add_function_symbol(
        stmt.extended_id.id_code,
        list(map(lambda x: x.extended_id.id_code, stmt.method_arg_list)),
    )
    return cg_ret


@create_global_cg_func(ClassDecl, enters_scope=ScopeType.SCOPE_CLASS)
def cg_class_decl(
    stmt: ClassDecl, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for class declaration

    Parameters
    ----------
    stmt : ClassDecl
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Class declaration")
    return cg_ret
