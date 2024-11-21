from ....ast.ast_types import (
    # global statements
    ClassDecl,
    FieldDecl,
    ConstDecl,
    ArgModifierType,
    SubDecl,
    FunctionDecl,
    # block statements
    VarDecl,
)
from ...symbols.symbol import (
    ValueSymbol,
    ArraySymbol,
    ValueMethodArgument,
    ReferenceMethodArgument,
    FunctionReturnSymbol,
    ConstantSymbol,
)
from ...scope import ScopeType
from ..codegen_state import CodegenState
from ..codegen_return import CodegenReturn
from ..codegen_reg import create_global_cg_func, codegen_global_stmt

__all__ = [
    "cg_var_decl",
    "cg_field_decl",
    "cg_const_decl",
    "cg_sub_decl",
    "cg_function_decl",
    "cg_class_decl",
]


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


@create_global_cg_func(SubDecl, enters_scope=ScopeType.SCOPE_SUB_DEFINITION)
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
    # define arguments in sub scope
    arg_names: list[str] = []
    for method_arg in stmt.method_arg_list:
        arg_names.append(method_arg.extended_id.id_code)
        match method_arg.arg_modifier:
            case ArgModifierType.ARG_VALUE:
                cg_state.add_symbol(ValueMethodArgument(arg_names[-1]))
            case ArgModifierType.ARG_REFERENCE:
                cg_state.add_symbol(ReferenceMethodArgument(arg_names[-1]))
    if (body_len := len(stmt.method_stmt_list)) > 0:
        body_desc = f" // {body_len} body statement{'s' if body_len > 1 else ''}"
    else:
        body_desc = " // empty sub body"
    cg_ret.append(f"Sub {stmt.extended_id.id_code}({', '.join(arg_names)});{body_desc}")
    # define sub symbol in enclosing scope
    cg_state.add_user_sub_symbol(
        stmt.extended_id.id_code,
        arg_names,
        # don't evaluate the sub body until the sub is called
        stmt.method_stmt_list,
    )
    return cg_ret


@create_global_cg_func(FunctionDecl, enters_scope=ScopeType.SCOPE_FUNCTION_DEFINITION)
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
    # define function name as return target
    cg_state.add_symbol(FunctionReturnSymbol(stmt.extended_id.id_code))
    # define arguments in function scope
    arg_names: list[str] = []
    for method_arg in stmt.method_arg_list:
        arg_names.append(method_arg.extended_id.id_code)
        match method_arg.arg_modifier:
            case ArgModifierType.ARG_VALUE:
                cg_state.add_symbol(ValueMethodArgument(arg_names[-1]))
            case ArgModifierType.ARG_REFERENCE:
                cg_state.add_symbol(ReferenceMethodArgument(arg_names[-1]))
    if (body_len := len(stmt.method_stmt_list)) > 0:
        body_desc = f" // {body_len} body statement{'s' if body_len > 1 else ''}"
    else:
        body_desc = " // empty function body"
    cg_ret.append(
        f"Function {stmt.extended_id.id_code}({', '.join(arg_names)});{body_desc}"
    )
    # define function symbol in enclosing scope
    cg_state.add_user_function_symbol(
        stmt.extended_id.id_code,
        arg_names,
        # don't evaluate the function body until the function is called
        stmt.method_stmt_list,
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
