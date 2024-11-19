"""ASP Request object"""

from collections.abc import Callable
from functools import wraps
from typing import Optional, Any
import attrs
from ...ast.ast_types.base import FormatterMixin
from ...ast.ast_types.builtin_leftexpr.obj_property import PropertyExpr
from ...ast.ast_types.builtin_leftexpr.request import (
    RequestExpr,
    RequestAnonymousExpr,
    # collections
    RequestClientCertificateExpr,
    RequestCookiesExpr,
    RequestFormExpr,
    RequestQueryStringExpr,
    RequestServerVariablesExpr,
    # properties
    RequestTotalBytesExpr,
    # methods
    RequestBinaryReadExpr,
)
from .asp_object import ASPObject
from .symbol import prepare_symbol_name, FunctionReturnSymbol
from ..scope import ScopeType
from ..codegen_state import CodegenState

request_expr_handlers: dict[
    type[RequestExpr], Callable[[ASPObject, RequestExpr, CodegenState], Any]
] = {}


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Request(ASPObject):
    """
    Methods
    -------
    handle_builtin_left_expr(left_expr)
    """

    def handle_builtin_left_expr(self, left_expr: RequestExpr, cg_state: CodegenState):
        """
        Parameters
        ----------
        left_expr : RequestExpr
        cg_state : CodegenState
        """
        assert isinstance(left_expr, RequestExpr)
        return request_expr_handlers[type(left_expr)](self, left_expr, cg_state)

    def handle_property_expr(self, prop_expr: PropertyExpr, cg_state: CodegenState):
        """
        Parameters
        ----------
        prop_expr : PropertyExpr
        cg_state : CodegenState
        """
        assert isinstance(prop_expr, PropertyExpr)


def create_request_handler(request_expr_type: type[RequestExpr]):
    """Decorator for RequestExpr handler functions

    Parameters
    ----------
    request_expr_type : type[RequestExpr]
    """
    assert issubclass(request_expr_type, RequestExpr)

    def wrap_func(func: Callable[[ASPObject, RequestExpr, CodegenState], Any]):
        @wraps(func)
        def handle_request_expr(
            req: ASPObject, left_expr: RequestExpr, cg_state: CodegenState
        ):
            assert isinstance(left_expr, request_expr_type)
            return func(req, left_expr, cg_state)

        request_expr_handlers[request_expr_type] = handle_request_expr
        return handle_request_expr

    return wrap_func


@create_request_handler(RequestAnonymousExpr)
def handle_request_anonymous_expr(
    req: Request, left_expr: RequestAnonymousExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestAnonymousExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(FunctionReturnSymbol("<anonymous>"))
        cg_state.add_function_return(cg_state.scope_mgr.current_scope, "<anonymous>")


@create_request_handler(RequestClientCertificateExpr)
def handle_request_client_certificate_expr(
    req: Request, left_expr: RequestClientCertificateExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestClientCertificateExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(FunctionReturnSymbol("clientcertificate"))
        cg_state.add_function_return(
            cg_state.scope_mgr.current_scope, "clientcertificate"
        )


@attrs.define(repr=False, slots=False)
class RequestCookie(FormatterMixin):
    """
    Attributes
    ----------
    name : Any
    key : Any
    attribute : str | None
    """

    name: Any
    key: Any
    attribute: Optional[str]


@create_request_handler(RequestCookiesExpr)
def handle_request_cookies_expr(
    req: Request, left_expr: RequestCookiesExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestCookiesExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(
            FunctionReturnSymbol(
                "cookies",
                RequestCookie(
                    left_expr.cookie_name,
                    left_expr.cookie_key,
                    left_expr.cookie_attribute,
                ),
            )
        )
        cg_state.add_function_return(cg_state.scope_mgr.current_scope, "cookies")


@create_request_handler(RequestFormExpr)
def handle_request_form_expr(
    req: Request, left_expr: RequestFormExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestFormExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(FunctionReturnSymbol("form"))
        cg_state.add_function_return(cg_state.scope_mgr.current_scope, "form")


@create_request_handler(RequestQueryStringExpr)
def handle_request_query_string_expr(
    req: Request, left_expr: RequestQueryStringExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestQueryStringExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(FunctionReturnSymbol("querystring"))
        cg_state.add_function_return(cg_state.scope_mgr.current_scope, "querystring")


@create_request_handler(RequestServerVariablesExpr)
def handle_request_server_variables_expr(
    req: Request, left_expr: RequestServerVariablesExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestServerVariablesExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(FunctionReturnSymbol("servervariables"))
        cg_state.add_function_return(
            cg_state.scope_mgr.current_scope, "servervariables"
        )


@create_request_handler(RequestTotalBytesExpr)
def handle_request_total_bytes_expr(
    req: Request, left_expr: RequestTotalBytesExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestTotalBytesExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(FunctionReturnSymbol("totalbytes"))
        cg_state.add_function_return(cg_state.scope_mgr.current_scope, "totalbytes")


@create_request_handler(RequestBinaryReadExpr)
def handle_request_binary_read_expr(
    req: Request, left_expr: RequestBinaryReadExpr, cg_state: CodegenState
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestBinaryReadExpr
    """
    with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
        cg_state.add_symbol(FunctionReturnSymbol("binaryread"))
        cg_state.add_function_return(cg_state.scope_mgr.current_scope, "binaryread")
