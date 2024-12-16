from difflib import SequenceMatcher
from inspect import signature, Signature
from io import StringIO
from typing import Any, Generator
import attrs
from ....ast.ast_types import (
    FormatterMixin,
    Expr,
    EvalExpr,
    LeftExpr,
    PropertyExpr,
    ResponseExpr,
    RequestExpr,
    ServerExpr,
    # global statements
    OptionExplicit,
    # block statements
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
from ...symbols.asp_object import ASPObject
from ...symbols.symbol import (
    ValueSymbol,
    ArraySymbol,
    LocalAssignmentSymbol,
    ValueMethodArgument,
    ReferenceMethodArgument,
    ForLoopRangeTargetSymbol,
    ForLoopIteratorTargetSymbol,
)
from ...symbols.symbol_table import ResolvedSymbol
from ...symbols.functions.function import ASPFunction, UserFunction, UserSub
from ...scope import ScopeType
from ..codegen_state import CodegenState
from ..codegen_return import CodegenReturn
from ..codegen_reg import create_global_cg_func, codegen_global_stmt
from .expression_finalizer import finalize_expr

__all__ = [
    "cg_option_explicit",
    "cg_error_stmt",
    "cg_redim_stmt",
    "cg_erase_stmt",
    "cg_call_stmt",
    "cg_sub_call_stmt",
    "cg_assign_stmt",
    "cg_exit_stmt",
    "cg_if_stmt",
    "cg_with_stmt",
    "cg_select_stmt",
    "cg_loop_stmt",
    "cg_for_stmt",
]


# ======== HELPER FUNCTIONS ========


def display_left_expr(left_expr: LeftExpr) -> str:
    """
    Parameters
    ----------
    left_expr : LeftExpr

    Returns
    -------
    str
    """

    def _display_helper() -> Generator[str, None, None]:
        nonlocal left_expr
        yield left_expr.sym_name
        for idx in range(left_expr.end_idx):
            if idx in left_expr.subnames:
                yield f".{left_expr.subnames[idx]}"
            elif idx in left_expr.call_args:
                yield "(...)"
            else:
                raise ValueError("Invalid left expression")

    return "".join(_display_helper())


def cghelper_setup_builtin_arguments(
    sig: Signature, left_expr: LeftExpr, cg_state: CodegenState
) -> Generator[Any, None, None]:
    """
    Parameters
    ----------
    sig : Signature
    left_expr : LeftExpr
    cg_state : CodegenState

    Yields
    ------
    Any
    """
    if (l_callargs := left_expr.call_args.get(left_expr.end_idx - 1, None)) is not None:
        for param_idx, (_, param_obj) in enumerate(sig.parameters.items(), -1):
            if param_idx < 0:
                # ignore cg_state parameter
                continue
            try:
                # try to access value before creating symbol
                idx_arg = l_callargs[param_idx]
                cg_state.add_symbol(ValueMethodArgument(param_obj.name))
                # ignore codegen output for argument assignment
                codegen_global_stmt(
                    AssignStmt(LeftExpr(param_obj.name), idx_arg), cg_state
                )
                yield (
                    cg_state.sym_table.sym_scopes[cg_state.scope_mgr.current_scope]
                    .sym_table[param_obj.name]
                    .value
                )
            except IndexError:
                # argument not specified in left expression
                # check for default value in function signature
                assert param_obj.default is not param_obj.empty, (
                    f"Missing parameter {repr(param_obj.name)} in "
                    f"{display_left_expr(left_expr)} function call, "
                    "no default value available"
                )
                yield param_obj.default


def cghelper_call_object(
    left_expr: LeftExpr, cg_state: CodegenState, *, res_scope: int = 0
):
    """Call a function attached to an object

    Parameters
    ----------
    left_expr : LeftExpr
    cg_state : CodegenState
    res_scope : int, default=0
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        sym: ASPObject
        if res_scope > 0:
            # object assigned to a variable
            assert (
                (res_scp := cg_state.sym_table.sym_scopes.get(res_scope, None))
                is not None
                and (res_sym := res_scp.sym_table.get(left_expr.sym_name, None))
                is not None
                and isinstance(res_sym, ValueSymbol)
                and isinstance(res_sym.value, ASPObject)
            ), (
                f"Left expression {repr(left_expr.sym_name)} does not "
                "point to a callable ASPObject symbol"
            )
            sym = res_sym.value
        else:
            # builtin object
            assert (
                res_sym := cg_state.sym_table.sym_scopes[0].sym_table.get(
                    left_expr.sym_name, None
                )
            ) is not None and isinstance(res_sym, ASPObject), (
                f"Left expression {repr(left_expr.sym_name)} does not "
                "point to a callable builtin ASPObject symbol"
            )
            sym = res_sym
        try:
            ex = None
            assert isinstance(
                left_expr, LeftExpr
            ), f"left_expr must be a valid left expression, got {repr(type(left_expr))}"
            assert left_expr.end_idx >= 1, "left_expr cannot contain only symbol name"
            if isinstance(left_expr, PropertyExpr):
                getattr(sym, "handle_property_expr")(left_expr, cg_state)
                return
            if isinstance(left_expr, (ResponseExpr, RequestExpr, ServerExpr)):
                getattr(sym, "handle_builtin_left_expr")(left_expr, cg_state)
                return
            idx = 0
            ret_obj = sym
            try:
                while idx < left_expr.end_idx:
                    if (l_subname := left_expr.subnames.get(idx, None)) is not None:
                        ret_obj = getattr(ret_obj, l_subname)
                        if left_expr.end_idx == 1:
                            # "object.method" call with no parentheses
                            ret_obj(cg_state)
                    elif left_expr.call_args.get(idx, None) is not None:
                        ret_obj = ret_obj(
                            cg_state,
                            *cghelper_setup_builtin_arguments(
                                signature(ret_obj), left_expr, cg_state
                            ),
                        )
                    else:
                        # don't catch, something is seriously wrong
                        raise RuntimeError(
                            f"Index {idx} of left expression is not valid"
                        )
                    idx += 1
            except (AttributeError, TypeError):
                # retry as a get property
                getattr(sym, "handle_property_expr")(
                    PropertyExpr.from_retrieval(left_expr), cg_state
                )
        except AssertionError as ex_wrong_type:
            ex = ex_wrong_type
        except AttributeError as ex_wrong_name:
            ex = ex_wrong_name
        except TypeError as ex_wrong_sig:
            ex = ex_wrong_sig
        finally:
            if ex is not None:
                raise ValueError(
                    f"Invalid call on {sym.__class__.__name__} object symbol"
                ) from ex


def cghelper_call_builtin_function(left_expr: LeftExpr, cg_state: CodegenState):
    """Call a builtin function

    The function will always be in SCOPE_SCRIPT_BUILTIN at ID 0 (zero)

    Parameters
    ----------
    left_expr : LeftExpr
    cg_state : CodegenState
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        sym: ASPFunction
        assert (
            sym := cg_state.sym_table.sym_scopes[0].sym_table.get(
                left_expr.sym_name, None
            )
        ) is not None, (
            f"Left expression {repr(left_expr.sym_name)} does not "
            "point to a callable ASPFunction symbol"
        )
        cg_state.sym_table.sym_scopes[0].sym_table[left_expr.sym_name](
            cg_state,
            *cghelper_setup_builtin_arguments(signature(sym.func), left_expr, cg_state),
        )


def cghelper_setup_user_arguments(
    method_args: list[str], call_args: tuple[Any, ...], cg_state: CodegenState
):
    """Prepare arguments for a user-defined function or sub

    Parameters
    ----------
    method_args : list[str]
    call_args : tuple[Any, ...]
    cg_state : CodegenState
    """
    call_scp = cg_state.scope_mgr.current_scope
    for marg, carg in zip(method_args, call_args):
        arg_sym = cg_state.sym_table.sym_scopes[call_scp].sym_table[marg]
        if isinstance(arg_sym, ValueMethodArgument):
            # ignore codegen output for argument assignment
            codegen_global_stmt(AssignStmt(LeftExpr(marg), carg), cg_state)
        elif isinstance(arg_sym, ReferenceMethodArgument):
            assert isinstance(carg, LeftExpr) and carg.end_idx == 0, (
                "Argument given by reference must be a "
                "left expression that contains only a symbol name"
            )
            arg_resv = cg_state.sym_table.resolve_symbol(
                carg,
                # referenced argument must exist in an enclosing scope
                cg_state.scope_mgr.current_environment[:-1],
            )
            assert len(arg_resv) > 0
            # refer to the name in the nearest enclosing scope
            cg_state.sym_table.sym_scopes[call_scp].sym_table[marg].ref_name = arg_resv[
                -1
            ].symbol.symbol_name
            cg_state.sym_table.sym_scopes[call_scp].sym_table[
                marg
            ].ref_scope = arg_resv[-1].scope


def cghelper_call_user_function(
    res_scope: int, left_expr: LeftExpr, cg_state: CodegenState
) -> CodegenReturn:
    """Call a user-defined function

    Parameters
    ----------
    res_scope : int
    left_expr : LeftExpr
    cg_state : CodegenState
    """
    cg_ret = CodegenReturn()
    call_sym: UserFunction = cg_state.sym_table.sym_scopes[res_scope].sym_table[
        left_expr.sym_name
    ]
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        call_scp = cg_state.scope_mgr.current_scope
        # copy function signature into new scope
        cg_state.sym_table.copy_scope(call_sym.func_scope_id, call_scp)
        # setup function arguments
        if (num_args := len(call_sym.arg_names)) > 0:
            assert (
                cargs := left_expr.call_args.get(left_expr.end_idx - 1, None)
            ) is not None and len(cargs) == num_args, (
                "Number of arguments in left expression "
                "must match number of function arguments"
            )
            cghelper_setup_user_arguments(call_sym.arg_names, cargs, cg_state)
        # copy-and-paste function body into current statement
        for body_stmt in call_sym.func_body:
            cg_ret.combine(codegen_global_stmt(body_stmt, cg_state), indent=False)
        # make a pointer to the return value
        cg_state.add_function_return(
            cg_state.scope_mgr.current_scope, left_expr.sym_name
        )
    return cg_ret


def cghelper_call_user_sub(
    res_scope: int, left_expr: LeftExpr, cg_state: CodegenState
) -> CodegenReturn:
    """Call a user-defined sub

    Parameters
    ----------
    res_scope : int
    left_expr : LeftExpr
    cg_state : CodegenState
    """
    cg_ret = CodegenReturn()
    call_sym: UserSub = cg_state.sym_table.sym_scopes[res_scope].sym_table[
        left_expr.sym_name
    ]
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_SUB_CALL):
        call_scp = cg_state.scope_mgr.current_scope
        # copy sub signature into new scope
        cg_state.sym_table.copy_scope(call_sym.sub_scope_id, call_scp)
        # setup sub arguments
        if (num_args := len(call_sym.arg_names)) > 0:
            assert (
                cargs := left_expr.call_args.get(left_expr.end_idx - 1, None)
            ) is not None and len(cargs) == num_args, (
                "Number of arguments in left expression "
                "must match number of sub arguments"
            )
            cghelper_setup_user_arguments(call_sym.arg_names, cargs, cg_state)
        # copy-and-paste sub body into current statement
        for body_stmt in call_sym.sub_body:
            cg_ret.combine(codegen_global_stmt(body_stmt, cg_state), indent=False)
    return cg_ret


def cghelper_call(
    left_expr: LeftExpr, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Helper function for call and sub-call statements

    Parameters
    ----------
    left_expr : LeftExpr
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    display_str = display_left_expr(left_expr)
    curr_env = cg_state.scope_mgr.current_environment
    sym_resv = cg_state.sym_table.resolve_symbol(left_expr, curr_env)
    if len(sym_resv) == 0:
        # since return value doesn't matter for (sub)call statements,
        # ignore method if cannot resolve
        print(
            f"Skipped {left_expr.sym_name} call (cannot resolve symbol)",
            file=cg_state.error_file,
        )
        return cg_ret
    # assume callable is only defined once
    assert len(sym_resv) == 1
    # determine callable type
    if isinstance(sym_resv[0].symbol, ASPObject):
        cg_ret.append(f"{display_str};")
        cghelper_call_object(left_expr, cg_state)
    elif isinstance(sym_resv[0].symbol, ASPFunction):
        cg_ret.append(f"{display_str};")
        cghelper_call_builtin_function(left_expr, cg_state)
    elif isinstance(sym_resv[0].symbol, ValueSymbol) and isinstance(
        sym_resv[0].symbol.value, ASPObject
    ):
        cg_ret.append(f"{display_str};")
        cghelper_call_object(left_expr, cg_state, res_scope=sym_resv[0].scope)
    elif isinstance(sym_resv[0].symbol, UserFunction):
        if len(sym_resv[0].symbol.func_body) == 0:
            print(
                f"Skipped {sym_resv[0].symbol.symbol_name} function call (empty function body)",
                file=cg_state.error_file,
            )
        else:
            cg_ret.append(f"{display_str} {'{'}")
            cg_ret.combine(
                cghelper_call_user_function(sym_resv[0].scope, left_expr, cg_state)
            )
            cg_ret.append(f"{'}'} // end {display_str} function call")
    elif isinstance(sym_resv[0].symbol, UserSub):
        if len(sym_resv[0].symbol.sub_body) == 0:
            print(
                f"Skipped {sym_resv[0].symbol.symbol_name} sub call (empty sub body)",
                file=cg_state.error_file,
            )
        else:
            cg_ret.append(f"{display_str} {'{'}")
            cg_ret.combine(
                cghelper_call_user_sub(sym_resv[0].scope, left_expr, cg_state)
            )
            cg_ret.append(f"{'}'} // end {display_str} sub call")
    else:
        raise ValueError("Symbol associated with left expression is not callable")
    return cg_ret


# ======== CODE GENERATION FUNCTIONS ========


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
    call_ret = cghelper_call(stmt.left_expr, cg_state, cg_ret)
    if cg_state.have_returned:
        # not assigning to any symbol, ignore return value
        cg_state.pop_function_return()
    return call_ret


@create_global_cg_func(SubCallStmt)
def cg_sub_call_stmt(
    stmt: SubCallStmt, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for sub-call statement

    Parameters
    ----------
    stmt : SubCallStmt
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    call_ret = cghelper_call(stmt.left_expr, cg_state, cg_ret)
    if cg_state.have_returned:
        # not assigning to any symbol, ignore return value
        cg_state.pop_function_return()
    return call_ret


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
    if isinstance(stmt.assign_expr, LeftExpr) and stmt.target_expr == stmt.assign_expr:
        print(
            "Skipped no-op assignment (target_expr == assign_expr)",
            file=cg_state.error_file,
        )
        return cg_ret
    cg_ret.append(f"Assign to {display_left_expr(stmt.target_expr)}")
    curr_env = cg_state.scope_mgr.current_environment
    rhs_expr = stmt.assign_expr
    if isinstance(rhs_expr, LeftExpr):
        # try to evaluate expression before assigning to target
        found = False
        for scp in reversed(curr_env):
            if (
                scp_sym := cg_state.sym_table.sym_scopes.get(scp, None)
            ) is not None and (
                rhs_sym := scp_sym.sym_table.get(rhs_expr.sym_name)
            ) is not None:
                found = True
                if isinstance(rhs_sym, ReferenceMethodArgument):
                    # method argument passed by reference
                    # resolve reference before trying to evaluate expression
                    assert (
                        rhs_sym.ref_scope is not None and rhs_sym.ref_name is not None
                    )
                    rhs_sym = cg_state.sym_table.sym_scopes[
                        rhs_sym.ref_scope
                    ].sym_table[rhs_sym.ref_name]
                if isinstance(rhs_sym, ValueMethodArgument):
                    # method argument passed by value
                    rhs_expr = rhs_sym.value
                    break
                elif isinstance(rhs_sym, ArraySymbol):
                    # array variable
                    try:
                        rhs_expr = rhs_sym.retrieve(rhs_expr)
                    except AssertionError:
                        rhs_expr = EvalExpr("PLACEHOLDER")
                    break
                elif isinstance(rhs_sym, ValueSymbol):
                    if isinstance(rhs_sym.value, ASPObject):
                        # object created in script
                        cghelper_call_object(rhs_expr, cg_state, res_scope=scp)
                    else:
                        # simple variable
                        rhs_expr = rhs_sym.value
                        break
                elif isinstance(rhs_sym, ForLoopIteratorTargetSymbol):
                    # TODO: add a for loop iteration expression
                    rhs_expr = EvalExpr("PLACEHOLDER")
                    break
                elif isinstance(rhs_sym, ForLoopRangeTargetSymbol):
                    rhs_expr = EvalExpr("PLACEHOLDER")
                    break
                elif isinstance(rhs_sym, ASPObject):
                    # builtin object
                    cghelper_call_object(rhs_expr, cg_state)
                elif isinstance(rhs_sym, ASPFunction):
                    # builtin function
                    cghelper_call_builtin_function(rhs_expr, cg_state)
                elif isinstance(rhs_sym, UserFunction):
                    # user-defined function
                    cghelper_call_user_function(scp, rhs_expr, cg_state)
                # overwrite expression with function return value
                rhs_expr = cg_state.function_return_symbols[-1].return_value
                cg_state.pop_function_return()
                break
        if not found:
            raise ValueError(
                "Could not find symbol associated with assignment expression"
            )

    lhs_expr = stmt.target_expr
    for scp in reversed(curr_env):
        if (scp_sym := cg_state.sym_table.sym_scopes.get(scp, None)) is not None and (
            lhs_sym := scp_sym.sym_table.get(lhs_expr.sym_name, None)
        ) is not None:
            if isinstance(lhs_sym, ASPObject):
                # property assignment on builtin object
                # treat property assignment as function call
                cghelper_call_object(
                    PropertyExpr.from_assignment(lhs_expr, rhs_expr),
                    cg_state,
                )
            elif isinstance(lhs_sym, ValueSymbol):
                if scp != curr_env[-1]:
                    # symbol defined in an enclosing scope
                    cg_state.add_symbol(
                        LocalAssignmentSymbol.from_value_symbol(lhs_sym)
                    )
                if lhs_expr.end_idx > 0 and isinstance(lhs_sym.value, ASPObject):
                    # property assignment on user-created object
                    # treat property assignment as function call
                    cghelper_call_object(
                        PropertyExpr.from_assignment(lhs_expr, rhs_expr),
                        cg_state,
                        res_scope=curr_env[-1],
                    )
                else:
                    cg_state.sym_table.sym_scopes[curr_env[-1]].assign(
                        lhs_expr, rhs_expr
                    )
            elif isinstance(lhs_sym, ArraySymbol):
                for ckey in lhs_expr.call_args.keys():
                    lhs_expr.call_args[ckey] = cg_state.sym_table.try_resolve_args(
                        lhs_expr.call_args[ckey], curr_env
                    )
                cg_state.sym_table.sym_scopes[scp].assign(lhs_expr, rhs_expr)
            else:
                cg_state.sym_table.sym_scopes[scp].assign(lhs_expr, rhs_expr)
            return cg_ret
    # did not find symbol
    assert (
        not cg_state.sym_table.option_explicit
    ), "Option Explicit is set, variables must be defined before use"
    # if symbol doesn't exist,
    # ensure that only the new symbol name is in the left expression
    assert lhs_expr.end_idx == 0
    cg_state.add_symbol(ValueSymbol(lhs_expr.sym_name, rhs_expr))
    cg_state.sym_table.sym_scopes[curr_env[-1]].track_assign(lhs_expr.sym_name)
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


@attrs.define(repr=False, slots=False)
class BranchingExpr(FormatterMixin, Expr):
    """Graph type representing all possible values for
    a variable that has been assigned to within a branching statement

    Attributes
    ----------
    orig_sym : ValueSymbol
        Original value symbol, to be used for substitution in
        branch expressions
    branches : list[Any]
        List of locally assigned values from different statement branches
    default_value : Any
        Either a value locally assigned within an else branch
        or the original value of the variable
    """

    orig_sym: ValueSymbol
    branches: list[Any]
    default_value: Any


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
    # helpers for constructing BranchingExpr values
    local_branches: dict[str, list[Any]] = {}
    local_defaults: dict[str, Any] = {}

    def _add_branch_scopes(name: str, scope: int):
        nonlocal local_branches, cg_state
        scp_sym: LocalAssignmentSymbol = cg_state.sym_table.sym_scopes[scope].sym_table[
            name
        ]
        assert isinstance(scp_sym, LocalAssignmentSymbol)
        branch_val = finalize_expr(scp_sym.value, cg_state)
        if name in local_branches:
            local_branches[name].append(branch_val)
        else:
            local_branches[name] = [branch_val]

    cg_ret.append(f"If[{cg_state.scope_mgr.current_scope}] {'{'}")
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_IF_BRANCH):
        main_branch_scope = cg_state.scope_mgr.current_scope
        main_branch_ret = CodegenReturn()
        main_branch_ret.append(f"If Branch[{main_branch_scope}] {'{'}")
        for block_stmt in stmt.block_stmt_list:
            main_branch_ret.combine(codegen_global_stmt(block_stmt, cg_state))
        main_branch_ret.append("}")
        cg_ret.combine(main_branch_ret)

        # check for local assignments in main branch scope
        if main_branch_scope in cg_state.sym_table.sym_scopes:
            for sym_name, sym_type in cg_state.sym_table.sym_scopes[
                main_branch_scope
            ].sym_table.items():
                if isinstance(sym_type, LocalAssignmentSymbol):
                    _add_branch_scopes(sym_name, main_branch_scope)

    for else_stmt in stmt.else_stmt_list:
        with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_IF_BRANCH):
            else_branch_scope = cg_state.scope_mgr.current_scope
            else_branch_ret = CodegenReturn()
            else_branch_type = "Else" if else_stmt.is_else else "ElseIf"
            else_branch_ret.append(
                f"{else_branch_type} Branch[{else_branch_scope}] {'{'}"
            )
            for else_block_stmt in else_stmt.stmt_list:
                else_branch_ret.combine(codegen_global_stmt(else_block_stmt, cg_state))
            else_branch_ret.append("}")
            cg_ret.combine(else_branch_ret)

            # check for local assignments in else(if) branch scope
            if else_branch_scope in cg_state.sym_table.sym_scopes:
                for sym_name, sym_type in cg_state.sym_table.sym_scopes[
                    else_branch_scope
                ].sym_table.items():
                    if isinstance(sym_type, LocalAssignmentSymbol):
                        if else_stmt.is_else:
                            # local assignment in an else branch
                            # overrides the original value
                            local_defaults[sym_name] = finalize_expr(
                                sym_type.value, cg_state
                            )
                        else:
                            _add_branch_scopes(sym_name, else_branch_scope)
    cg_ret.append("}")

    # update value symbols in enclosing scopes
    for bname, bvals in local_branches.items():
        # don't catch index error
        bsym: ResolvedSymbol = cg_state.sym_table.resolve_symbol(
            LeftExpr(bname), cg_state.scope_mgr.current_environment
        )[-1]
        assert isinstance(bsym.symbol, ValueSymbol)
        bdef = local_defaults.get(bname, finalize_expr(bsym.symbol.value, cg_state))
        if (
            len(bvals) == 1
            and isinstance(bvals[0], EvalExpr)
            and isinstance(bvals[0].expr_value, str)
        ) and (isinstance(bdef, EvalExpr) and isinstance(bdef.expr_value, str)):
            res_str = StringIO()
            val_a: str = bdef.expr_value
            val_b: str = bvals[0].expr_value
            for tag, i1, i2, j1, j2 in SequenceMatcher(
                lambda x: x.isspace(), val_a, val_b, False
            ).get_opcodes():
                match tag:
                    case "replace":
                        print(
                            f"{'{{'}{val_a[i1:i2]}|{val_b[j1:j2]}{'}}'}",
                            end="",
                            file=res_str,
                        )
                    case "delete":
                        print(f"{'{{'}{val_a[i1:i2]}{'}}'}", end="", file=res_str)
                    case "insert":
                        print(f"{'{{'}{val_b[j1:j2]}{'}}'}", end="", file=res_str)
                    case "equal":
                        print(val_a[i1:i2], end="", file=res_str)
            cg_state.sym_table.sym_scopes[bsym.scope].sym_table[bname].value = EvalExpr(
                res_str.getvalue()
            )
        else:
            cg_state.sym_table.sym_scopes[bsym.scope].sym_table[
                bname
            ].value = BranchingExpr(
                ValueSymbol(bsym.symbol.symbol_name, bsym.symbol.value), bvals, bdef
            )

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
