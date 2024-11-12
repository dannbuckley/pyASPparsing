"""ASP Server object"""

from collections.abc import Callable
from functools import wraps
from typing import Any
import attrs
from ...ast.ast_types.optimize import EvalExpr
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
from .symbol import ASPObject, prepare_symbol_name
from .adodb import Connection, Recordset
from .mswc import PageCounter

server_object_types: dict[str, dict[str, type[ASPObject]]] = {
    "adodb": {"connection": Connection, "recordset": Recordset},
    "mswc": {"pagecounter": PageCounter},
}

server_expr_handlers: dict[type[ServerExpr], Callable[[ASPObject, ServerExpr], Any]] = (
    {}
)


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Server(ASPObject):
    """"""

    def handle_builtin_left_expr(self, left_expr: ServerExpr):
        """"""
        assert isinstance(left_expr, ServerExpr)
        return server_expr_handlers[type(left_expr)](self, left_expr)

    def createobject(self, param_progid, /) -> ASPObject:
        """NOT CALLED DIRECTLY

        Called indirectly by `__call__(..., name="createobject")`

        Parameters
        ----------
        param_progid

        Returns
        -------
        ASPObject

        Raises
        ------
        ValueError

        AssertionError
        """
        if not isinstance(param_progid, EvalExpr) or not isinstance(
            param_progid.expr_value, str
        ):
            raise ValueError("Server.CreateObject expects a string for progid")
        parts = param_progid.expr_value.split(".")
        assert len(parts) == 2, "progid should match 'Vendor.Component'"
        try:
            return server_object_types[parts[0].casefold()][parts[1].casefold()]()
        except KeyError as ex:
            raise ValueError(
                f"Could not determine type of component: '{param_progid.expr_value}'"
            ) from ex

    def execute(self, param_path, /):
        """"""

    def getlasterror(self):
        """"""

    def htmlencode(self, param_string, /):
        """"""

    def mappath(self, param_path, /):
        """"""

    def transfer(self, param_path, /):
        """"""

    def urlencode(self, param_string, /):
        """"""


def create_server_handler(server_expr_type: type[ServerExpr]):
    """"""
    assert issubclass(server_expr_type, ServerExpr)

    def wrap_func(func: Callable[[ASPObject, ServerExpr], Any]):
        @wraps(func)
        def handle_server_expr(serv: ASPObject, left_expr: ServerExpr):
            assert isinstance(left_expr, server_expr_type)
            return func(serv, left_expr)

        server_expr_handlers[server_expr_type] = handle_server_expr
        return handle_server_expr

    return wrap_func


@create_server_handler(ServerScriptTimeoutExpr)
def handle_server_script_timeout_expr(serv: Server, left_expr: ServerScriptTimeoutExpr):
    """"""


@create_server_handler(ServerCreateObjectExpr)
def handle_server_create_object_expr(serv: Server, left_expr: ServerCreateObjectExpr):
    """"""
    assert isinstance(left_expr.param_progid, EvalExpr) and isinstance(
        left_expr.param_progid.expr_value, str
    ), "Server.CreateObject expects a string for progid"
    parts = left_expr.param_progid.expr_value.split(".")
    assert len(parts) == 2, "progid should match 'Vendor.Component'"
    try:
        return server_object_types[parts[0].casefold()][parts[1].casefold()]()
    except KeyError as ex:
        raise ValueError(
            f"Could not determine type of component: '{left_expr.param_progid.expr_value}'"
        ) from ex


@create_server_handler(ServerExecuteExpr)
def handle_server_execute_expr(serv: Server, left_expr: ServerExecuteExpr):
    """"""


@create_server_handler(ServerGetLastErrorExpr)
def handle_server_get_last_error_expr(serv: Server, left_expr: ServerGetLastErrorExpr):
    """"""


@create_server_handler(ServerHTMLEncodeExpr)
def handle_server_html_encode_expr(serv: Server, left_expr: ServerHTMLEncodeExpr):
    """"""


@create_server_handler(ServerMapPathExpr)
def handle_server_map_path_expr(serv: Server, left_expr: ServerMapPathExpr):
    """"""


@create_server_handler(ServerTransferExpr)
def handle_server_transfer_expr(serv: Server, left_expr: ServerTransferExpr):
    """"""


@create_server_handler(ServerURLEncodeExpr)
def handle_server_url_encode_expr(serv: Server, left_expr: ServerURLEncodeExpr):
    """"""
