"""state_handlers module"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
import typing

from ..tokenizer.token_types import TokenType
from ..tokenizer.state_machine import Tokenizer
from .parser_state import GlobalState, GlobalStateStack
from .base import GlobalStmt, Expr, AccessModifierType
from .declarations import *
from .expressions import *
from .statements import *
from .parse_expressions import ExpressionParser

type GlobalStmtGen = typing.Generator[None, typing.Any, GlobalStmt]
type GlobalStmtGenOpt = typing.Optional[GlobalStmtGen]
type GlobalStmtOpt = typing.Optional[GlobalStmt]

# states that return a global statement
reg_state_returns_stmt: typing.List[GlobalState] = []

# map state enum to handler function
reg_state_handlers: typing.Dict[
    GlobalState,
    Callable[[Tokenizer, GlobalStateStack, GlobalStmtGenOpt], GlobalStmtOpt],
] = {}


@dataclass
class StmtGenManager:
    """"""

    curr_stmt_gen: GlobalStmtGenOpt = None

    def start_generator(self, start_type: type):
        assert issubclass(start_type, GlobalStmt)
        self.curr_stmt_gen = start_type.generate_global_stmt()
        next(self.curr_stmt_gen, None)

    def clear_generator(self):
        self.curr_stmt_gen = None


@dataclass
class StateArgs:
    """"""

    tkzr: Tokenizer
    state_stack: GlobalStateStack
    stmt_gen_mngr: StmtGenManager


def create_parser_state(
    state: GlobalState,
    *,
    returns: bool = False,
):
    """Decorator function that adds state arguments
    to handler functions

    State handler is registered in `reg_state_handlers`

    Parameters
    ----------
    state : GlobalState
    returns : bool, default=False
        If True, register state in `reg_state_returns_stmt`
    """

    if returns:
        reg_state_returns_stmt.append(state)

    def wrap_func(func: Callable[[StateArgs], GlobalStmtOpt]):
        @wraps(func)
        def add_state_args(
            tkzr: Tokenizer,
            state_stack: GlobalStateStack,
            stmt_gen_mngr: GlobalStmtGenOpt = None,
        ):
            return func(StateArgs(tkzr, state_stack, stmt_gen_mngr))

        reg_state_handlers[state] = add_state_args
        return add_state_args

    return wrap_func


# ======== PARSER STATE HANDLERS ========
# THESE ARE NOT CALLED DIRECTLY
# Instead, the create_parser_state decorater registers them in the reg_state_handlers global dict
# States are exited automatically unless state_stack.persist_state() is called


@create_parser_state(GlobalState.CHECK_EXHAUSTED)
def state_check_exhausted(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    if not sargs.tkzr.current_token is None:
        sargs.state_stack.persist_state()
        sargs.state_stack.enter_multiple(
            [GlobalState.START_GLOBAL_STMT, GlobalState.END_GLOBAL_STMT]
        )


@create_parser_state(GlobalState.START_GLOBAL_STMT)
def state_start_global_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    assert sargs.tkzr.try_multiple_token_type(
        [
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER_IDDOT,
            TokenType.IDENTIFIER_DOTID,
            TokenType.IDENTIFIER_DOTIDDOT,
        ]
    ), "Global statement must start with a valid identifier"
    match sargs.tkzr.get_token_code():
        case "option":
            sargs.state_stack.enter_state(GlobalState.START_OPTION_EXPLICIT)
        case "public" | "private":
            sargs.state_stack.enter_state(GlobalState.CHECK_ACCESS_MODIFIER)
        case "class":
            sargs.state_stack.enter_state(GlobalState.START_CLASS_DECL)
        case "const":
            sargs.state_stack.enter_multiple(
                [GlobalState.START_CONST_DECL, GlobalState.SET_ACCESS_NONE]
            )
        case "sub":
            sargs.state_stack.enter_multiple(
                [GlobalState.START_SUB_DECL, GlobalState.SET_ACCESS_NONE]
            )
        case "function":
            sargs.state_stack.enter_multiple(
                [GlobalState.START_FUNCTION_DECL, GlobalState.SET_ACCESS_NONE]
            )
        case _:
            # try to parse as a block statement
            sargs.state_stack.enter_state(GlobalState.START_BLOCK_STMT)


@create_parser_state(GlobalState.END_GLOBAL_STMT, returns=True)
def state_end_global_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    ret_stmt: typing.Optional[GlobalStmt] = None
    try:
        next(sargs.stmt_gen_mngr.curr_stmt_gen)
    except StopIteration as ex:
        ret_stmt = ex.value
    finally:
        assert ret_stmt is not None and isinstance(ret_stmt, GlobalStmt)
        sargs.stmt_gen_mngr.clear_generator()
    return ret_stmt


@create_parser_state(GlobalState.START_OPTION_EXPLICIT)
def state_start_option_explicit(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(OptionExplicit)
    sargs.tkzr.assert_consume(TokenType.IDENTIFIER, "option")
    sargs.tkzr.assert_consume(TokenType.IDENTIFIER, "explicit")
    sargs.tkzr.assert_consume(TokenType.NEWLINE)


@create_parser_state(GlobalState.CHECK_ACCESS_MODIFIER)
def state_check_access_modifier(sargs: StateArgs) -> GlobalStmtOpt:
    """"""


@create_parser_state(GlobalState.SET_ACCESS_NONE)
def state_set_access_none(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.curr_stmt_gen.send(None)  # access_mod


@create_parser_state(GlobalState.SET_ACCESS_PRIVATE)
def state_set_access_private(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.curr_stmt_gen.send(AccessModifierType.PRIVATE)  # access_mod


@create_parser_state(GlobalState.SET_ACCESS_PUBLIC)
def state_set_access_public(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.curr_stmt_gen.send(AccessModifierType.PUBLIC)  # access_mod


@create_parser_state(GlobalState.SET_ACCESS_PUBLIC_DEFAULT)
def state_set_access_public_default(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.curr_stmt_gen.send(
        AccessModifierType.PUBLIC_DEFAULT
    )  # access_mod


@create_parser_state(GlobalState.START_CLASS_DECL)
def state_start_class_decl(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(ClassDecl)


@create_parser_state(GlobalState.START_FIELD_DECL)
def state_start_field_decl(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(FieldDecl)


@create_parser_state(GlobalState.START_CONST_DECL)
def state_start_const_decl(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(ConstDecl)


@create_parser_state(GlobalState.START_SUB_DECL)
def state_start_sub_decl(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(SubDecl)


@create_parser_state(GlobalState.START_FUNCTION_DECL)
def state_start_function_decl(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(FunctionDecl)


@create_parser_state(GlobalState.START_BLOCK_STMT)
def state_start_block_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    assert sargs.tkzr.try_multiple_token_type(
        [
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER_IDDOT,
            TokenType.IDENTIFIER_DOTID,
            TokenType.IDENTIFIER_DOTIDDOT,
        ]
    ), "Block statement must start with a valid identifier"

    match sargs.tkzr.get_token_code():
        case "dim":
            sargs.state_stack.enter_state(GlobalState.START_VAR_DECL)
        case "redim":
            sargs.state_stack.enter_state(GlobalState.START_REDIM_STMT)
        case "if":
            sargs.state_stack.enter_state(GlobalState.START_IF_STMT)
        case "with":
            sargs.state_stack.enter_state(GlobalState.START_WITH_STMT)
        case "select":
            sargs.state_stack.enter_state(GlobalState.START_SELECT_STMT)
        case "do" | "while":
            sargs.state_stack.enter_state(GlobalState.START_LOOP_STMT)
        case "for":
            sargs.state_stack.enter_state(GlobalState.START_FOR_STMT)
        case _:
            # try to parse as inline statement
            sargs.state_stack.enter_multiple(
                [
                    GlobalState.INLINE_TERM_NEWLINE,
                    GlobalState.CHECK_BLOCK_INLINE_NEWLINE,
                ]
            )


@create_parser_state(GlobalState.CHECK_BLOCK_INLINE_NEWLINE)
def state_check_block_inline_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    # inline block statements must be terminated by a NEWLINE token
    sargs.tkzr.assert_consume(TokenType.NEWLINE)


@create_parser_state(GlobalState.START_VAR_DECL)
def state_start_var_decl(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(VarDecl)


@create_parser_state(GlobalState.START_REDIM_STMT)
def state_start_redim_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(RedimStmt)


@create_parser_state(GlobalState.START_IF_STMT)
def state_start_if_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(IfStmt)


@create_parser_state(GlobalState.START_WITH_STMT)
def state_start_with_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(WithStmt)


@create_parser_state(GlobalState.START_SELECT_STMT)
def state_start_select_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(SelectStmt)


@create_parser_state(GlobalState.START_LOOP_STMT)
def state_start_loop_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(LoopStmt)


@create_parser_state(GlobalState.START_FOR_STMT)
def state_start_for_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(ForStmt)


def parse_inline_stmt(sargs: StateArgs, state: GlobalState):
    """"""
    assert sargs.tkzr.try_multiple_token_type(
        [
            TokenType.IDENTIFIER,
            TokenType.IDENTIFIER_IDDOT,
            TokenType.IDENTIFIER_DOTID,
            TokenType.IDENTIFIER_DOTIDDOT,
        ]
    ), "Inline statement must start with a valid identifier"

    matched: bool = False
    match sargs.tkzr.get_token_code():
        case "set":
            sargs.stmt_gen_mngr.start_generator(AssignStmt)
            sargs.state_stack.enter_state(GlobalState.START_ASSIGN_STMT)
            matched = True
        case "call":
            sargs.state_stack.enter_state(GlobalState.START_CALL_STMT)
            matched = True
        case "on":
            sargs.state_stack.enter_state(GlobalState.START_ERROR_STMT)
            matched = True
        case "exit":
            sargs.state_stack.enter_state(GlobalState.START_EXIT_STMT)
            matched = True
        case "erase":
            sargs.state_stack.enter_state(GlobalState.START_ERASE_STMT)
            matched = True

    if not matched:
        # no leading keyword, try parsing a left expression
        left_expr: LeftExpr = ExpressionParser.parse_left_expr(sargs.tkzr)

        # assign statement?
        if sargs.tkzr.try_consume(TokenType.SYMBOL, "="):
            assign_expr = ExpressionParser.parse_expr(sargs.tkzr)
            sargs.stmt_gen_mngr.start_generator(AssignStmt)
            sargs.stmt_gen_mngr.curr_stmt_gen.send(left_expr)  # left_expr
            sargs.stmt_gen_mngr.curr_stmt_gen.send(assign_expr)  # sub_safe_expr
            sargs.stmt_gen_mngr.curr_stmt_gen.send(False)  # is_new
        else:
            # must be a subcall statement
            sargs.stmt_gen_mngr.start_generator(SubCallStmt)
            sargs.stmt_gen_mngr.curr_stmt_gen.send(left_expr)  # left_expr
            match state:
                case GlobalState.INLINE_TERM_NEWLINE:
                    sargs.state_stack.enter_state(GlobalState.SUBCALL_TERM_NEWLINE)
                case GlobalState.INLINE_TERM_END:
                    sargs.state_stack.enter_state(GlobalState.SUBCALL_TERM_END)
                case GlobalState.INLINE_TERM_END_NEWLINE:
                    sargs.state_stack.enter_state(GlobalState.SUBCALL_TERM_END_NEWLINE)
                case GlobalState.INLINE_TERM_ELSE_END_NEWLINE:
                    sargs.state_stack.enter_state(
                        GlobalState.SUBCALL_TERM_ELSE_END_NEWLINE
                    )


@create_parser_state(GlobalState.INLINE_TERM_NEWLINE)
def state_inline_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_inline_stmt(sargs, GlobalState.INLINE_TERM_NEWLINE)


@create_parser_state(GlobalState.INLINE_TERM_END)
def state_inline_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_inline_stmt(sargs, GlobalState.INLINE_TERM_END)


@create_parser_state(GlobalState.INLINE_TERM_END_NEWLINE)
def state_inline_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_inline_stmt(sargs, GlobalState.INLINE_TERM_END_NEWLINE)


@create_parser_state(GlobalState.INLINE_TERM_ELSE_END_NEWLINE)
def state_inline_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_inline_stmt(sargs, GlobalState.INLINE_TERM_ELSE_END_NEWLINE)


@create_parser_state(GlobalState.START_ASSIGN_STMT)
def state_start_assign_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    # sargs.stmt_gen_mngr.start_generator(AssignStmt)


@create_parser_state(GlobalState.START_CALL_STMT)
def state_start_call_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(CallStmt)


@create_parser_state(GlobalState.START_ERROR_STMT)
def state_start_error_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(ErrorStmt)


@create_parser_state(GlobalState.START_EXIT_STMT)
def state_start_exit_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(ExitStmt)


@create_parser_state(GlobalState.START_ERASE_STMT)
def state_start_erase_stmt(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    sargs.stmt_gen_mngr.start_generator(EraseStmt)


def parse_subcall_stmt(
    sargs: StateArgs,
    terminal_type: typing.Optional[TokenType] = None,
    terminal_code: typing.Optional[str] = None,
    terminal_casefold: bool = True,
    *,
    terminal_pairs: typing.List[typing.Tuple[TokenType, typing.Optional[str]]] = [],
):
    """"""
    # need to send: sub_safe_expr, comma_expr_list
    assert (len(terminal_pairs) > 0) or (
        terminal_type is not None
    ), "Expected at least one terminal type or type/code pair"

    def _check_terminal() -> bool:
        nonlocal sargs, terminal_type, terminal_code, terminal_casefold, terminal_pairs
        if len(terminal_pairs) > 0:
            return any(
                map(
                    lambda tpair: sargs.tkzr.try_token_type(tpair[0])
                    and (
                        (tpair[1] is None)
                        or sargs.tkzr.get_token_code(terminal_casefold) == tpair[1]
                    ),
                    terminal_pairs,
                )
            )
        return sargs.tkzr.try_token_type(terminal_type) and (
            (terminal_code is None)
            or (sargs.tkzr.get_token_code(terminal_casefold) == terminal_code)
        )
    
    sub_safe_expr: typing.Optional[Expr] = None


@create_parser_state(GlobalState.SUBCALL_TERM_NEWLINE)
def state_subcall_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_subcall_stmt(sargs, TokenType.NEWLINE)


@create_parser_state(GlobalState.SUBCALL_TERM_END)
def state_subcall_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_subcall_stmt(sargs, TokenType.IDENTIFIER, "end")


@create_parser_state(GlobalState.SUBCALL_TERM_END_NEWLINE)
def state_subcall_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_subcall_stmt(
        sargs, terminal_pairs=[(TokenType.IDENTIFIER, "end"), (TokenType.NEWLINE, None)]
    )


@create_parser_state(GlobalState.SUBCALL_TERM_ELSE_END_NEWLINE)
def state_subcall_term_newline(sargs: StateArgs) -> GlobalStmtOpt:
    """"""
    parse_subcall_stmt(
        sargs,
        terminal_pairs=[
            (TokenType.IDENTIFIER, "else"),
            (TokenType.IDENTIFIER, "end"),
            (TokenType.NEWLINE, None),
        ],
    )
