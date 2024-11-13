"""ASP Request object"""

from collections.abc import Callable
from functools import wraps
from typing import Any
import attrs
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
from .symbol import ASPObject, prepare_symbol_name

request_expr_handlers: dict[
    type[RequestExpr], Callable[[ASPObject, RequestExpr], Any]
] = {}


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Request(ASPObject):
    """
    Methods
    -------
    handle_builtin_left_expr(left_expr)
    """

    def handle_builtin_left_expr(self, left_expr: RequestExpr):
        """
        Parameters
        ----------
        left_expr : RequestExpr
        """
        assert isinstance(left_expr, RequestExpr)
        return request_expr_handlers[type(left_expr)](self, left_expr)


def create_request_handler(request_expr_type: type[RequestExpr]):
    """Decorator for RequestExpr handler functions

    Parameters
    ----------
    request_expr_type : type[RequestExpr]
    """
    assert issubclass(request_expr_type, RequestExpr)

    def wrap_func(func: Callable[[ASPObject, RequestExpr], Any]):
        @wraps(func)
        def handle_request_expr(req: ASPObject, left_expr: RequestExpr):
            assert isinstance(left_expr, request_expr_type)
            return func(req, left_expr)

        request_expr_handlers[request_expr_type] = handle_request_expr
        return handle_request_expr

    return wrap_func


@create_request_handler(RequestAnonymousExpr)
def handle_request_anonymous_expr(req: Request, left_expr: RequestAnonymousExpr):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestAnonymousExpr
    """


@create_request_handler(RequestClientCertificateExpr)
def handle_request_client_certificate_expr(
    req: Request, left_expr: RequestClientCertificateExpr
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestClientCertificateExpr
    """


@create_request_handler(RequestCookiesExpr)
def handle_request_cookies_expr(req: Request, left_expr: RequestCookiesExpr):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestCookiesExpr
    """


@create_request_handler(RequestFormExpr)
def handle_request_form_expr(req: Request, left_expr: RequestFormExpr):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestFormExpr
    """


@create_request_handler(RequestQueryStringExpr)
def handle_request_query_string_expr(req: Request, left_expr: RequestQueryStringExpr):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestQueryStringExpr
    """


@create_request_handler(RequestServerVariablesExpr)
def handle_request_server_variables_expr(
    req: Request, left_expr: RequestServerVariablesExpr
):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestServerVariablesExpr
    """


@create_request_handler(RequestTotalBytesExpr)
def handle_request_total_bytes_expr(req: Request, left_expr: RequestTotalBytesExpr):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestTotalBytesExpr
    """


@create_request_handler(RequestBinaryReadExpr)
def handle_request_binary_read_expr(req: Request, left_expr: RequestBinaryReadExpr):
    """
    Parameters
    ----------
    req : Request
    left_expr : RequestBinaryReadExpr
    """
