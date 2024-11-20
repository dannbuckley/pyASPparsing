"""ASP Server object"""

from collections.abc import Callable
from functools import wraps
from typing import Any
import attrs
from ...ast.ast_types.optimize import EvalExpr
from ...ast.ast_types.builtin_leftexpr.obj_property import PropertyExpr
from ...ast.ast_types.builtin_leftexpr.server import (
    ServerExpr,
    # properties
    ServerScriptTimeoutExpr,
    # methods
    ServerCreateObjectExpr,
    ServerExecuteExpr,
    ServerGetLastErrorExpr,
    ServerHTMLEncodeExpr,
    ServerMapPathExpr,
    ServerTransferExpr,
    ServerURLEncodeExpr,
)
from .asp_object import ASPObject
from .symbol import prepare_symbol_name, FunctionReturnSymbol
from .adodb import Connection, Recordset
from .mswc import PageCounter
from ..codegen_state import CodegenState

server_object_types: dict[str, dict[str, type[ASPObject]]] = {
    "adodb": {"connection": Connection, "recordset": Recordset},
    "mswc": {"pagecounter": PageCounter},
}

server_expr_handlers: dict[
    type[ServerExpr], Callable[[ASPObject, ServerExpr, CodegenState], Any]
] = {}


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Server(ASPObject):
    """
    Methods
    -------
    handle_builtin_left_expr(left_expr)
    """

    def handle_builtin_left_expr(self, left_expr: ServerExpr, cg_state: CodegenState):
        """
        Parameters
        ----------
        left_expr : ServerExpr
        cg_state : CodegenState
        """
        assert isinstance(left_expr, ServerExpr)
        return server_expr_handlers[type(left_expr)](self, left_expr, cg_state)

    def handle_property_expr(self, prop_expr: PropertyExpr, cg_state: CodegenState):
        """
        Parameters
        ----------
        prop_expr : PropertyExpr
        cg_state : CodegenState
        """
        assert isinstance(prop_expr, PropertyExpr)


def create_server_handler(server_expr_type: type[ServerExpr]):
    """Decorator for ServerExpr handler functions

    Parameters
    ----------
    server_expr_type : type[ServerExpr]
    """
    assert issubclass(server_expr_type, ServerExpr)

    def wrap_func(func: Callable[[ASPObject, ServerExpr, CodegenState], Any]):
        @wraps(func)
        def handle_server_expr(
            serv: ASPObject, left_expr: ServerExpr, cg_state: CodegenState
        ):
            assert isinstance(left_expr, server_expr_type)
            return func(serv, left_expr, cg_state)

        server_expr_handlers[server_expr_type] = handle_server_expr
        return handle_server_expr

    return wrap_func


@create_server_handler(ServerScriptTimeoutExpr)
def handle_server_script_timeout_expr(
    serv: Server, left_expr: ServerScriptTimeoutExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerScriptTimeoutExpr
    """


@create_server_handler(ServerCreateObjectExpr)
def handle_server_create_object_expr(
    serv: Server, left_expr: ServerCreateObjectExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerCreateObjectExpr
    """
    assert isinstance(left_expr.param_progid, EvalExpr) and isinstance(
        left_expr.param_progid.expr_value, str
    ), "Server.CreateObject expects a string for progid"
    parts = left_expr.param_progid.expr_value.split(".")
    assert len(parts) == 2, "progid should match 'Vendor.Component'"
    try:
        new_obj = server_object_types[parts[0].casefold()][parts[1].casefold()]()
        cg_state.add_symbol(FunctionReturnSymbol("createobject", new_obj))
        cg_state.add_function_return(
            cg_state.scope_mgr.current_scope, "createobject"
        )
    except KeyError as ex:
        raise ValueError(
            f"Could not determine type of component: '{left_expr.param_progid.expr_value}'"
        ) from ex


@create_server_handler(ServerExecuteExpr)
def handle_server_execute_expr(
    serv: Server, left_expr: ServerExecuteExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerExecuteExpr
    """


@create_server_handler(ServerGetLastErrorExpr)
def handle_server_get_last_error_expr(
    serv: Server, left_expr: ServerGetLastErrorExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerGetLastErrorExpr
    """


@create_server_handler(ServerHTMLEncodeExpr)
def handle_server_html_encode_expr(
    serv: Server, left_expr: ServerHTMLEncodeExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerHTMLEncodeExpr
    """


@create_server_handler(ServerMapPathExpr)
def handle_server_map_path_expr(
    serv: Server, left_expr: ServerMapPathExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerMapPathExpr
    """


@create_server_handler(ServerTransferExpr)
def handle_server_transfer_expr(
    serv: Server, left_expr: ServerTransferExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerTransferExpr
    """


@create_server_handler(ServerURLEncodeExpr)
def handle_server_url_encode_expr(
    serv: Server, left_expr: ServerURLEncodeExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    serv : Server
    left_expr : ServerURLEncodeExpr
    """
