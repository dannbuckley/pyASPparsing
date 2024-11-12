"""ASP Response object"""

from collections.abc import Callable
from functools import wraps
from typing import Any
import attrs
from ...ast.ast_types.builtin_leftexpr.response import (
    ResponseExpr,
    # collections
    ResponseCookiesExpr,
    # properties
    ResponseBufferExpr,
    ResponseCacheControlExpr,
    ResponseCharsetExpr,
    ResponseContentTypeExpr,
    ResponseExpiresExpr,
    ResponseExpiresAbsoluteExpr,
    ResponseIsClientConnectedExpr,
    ResponsePICSExpr,
    ResponseStatusExpr,
    # methods
    ResponseAddHeaderExpr,
    ResponseAppendToLogExpr,
    ResponseBinaryWriteExpr,
    ResponseClearExpr,
    ResponseEndExpr,
    ResponseFlushExpr,
    ResponseRedirectExpr,
    ResponseWriteExpr,
)
from .symbol import ASPObject, prepare_symbol_name

response_expr_handlers: dict[
    type[ResponseExpr], Callable[[ASPObject, ResponseExpr], Any]
] = {}


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Response(ASPObject):
    """"""

    def handle_builtin_left_expr(self, left_expr: ResponseExpr):
        """"""
        assert isinstance(left_expr, ResponseExpr)
        return response_expr_handlers[type(left_expr)](self, left_expr)

    def addheader(self, param_name, param_value, /):
        """"""

    def appendtolog(self, param_string, /):
        """"""

    def binarywrite(self, param_data, /):
        """"""

    def clear(self):
        """"""

    def end(self):
        """"""

    def flush(self):
        """"""

    def redirect(self, param_url, /):
        """"""

    def write(self, param_variant, /):
        """"""


def create_response_handler(response_expr_type: type[ResponseExpr]):
    """"""
    assert issubclass(response_expr_type, ResponseExpr)

    def wrap_func(func: Callable[[ASPObject, ResponseExpr], Any]):
        @wraps(func)
        def handle_response_expr(resp: ASPObject, left_expr: ResponseExpr):
            assert isinstance(left_expr, response_expr_type)
            return func(resp, left_expr)

        response_expr_handlers[response_expr_type] = handle_response_expr
        return handle_response_expr

    return wrap_func


@create_response_handler(ResponseCookiesExpr)
def handle_response_cookies_expr(resp: Response, left_expr: ResponseCookiesExpr):
    """"""


@create_response_handler(ResponseBufferExpr)
def handle_response_buffer_expr(resp: Response, left_expr: ResponseBufferExpr):
    """"""


@create_response_handler(ResponseCacheControlExpr)
def handle_response_cache_control_expr(
    resp: Response, left_expr: ResponseCacheControlExpr
):
    """"""


@create_response_handler(ResponseCharsetExpr)
def handle_response_charset_expr(resp: Response, left_expr: ResponseCharsetExpr):
    """"""


@create_response_handler(ResponseContentTypeExpr)
def handle_response_content_type_expr(
    resp: Response, left_expr: ResponseContentTypeExpr
):
    """"""


@create_response_handler(ResponseExpiresExpr)
def handle_response_expires_expr(resp: Response, left_expr: ResponseExpiresExpr):
    """"""


@create_response_handler(ResponseExpiresAbsoluteExpr)
def handle_response_expires_absolute_expr(
    resp: Response, left_expr: ResponseExpiresAbsoluteExpr
):
    """"""


@create_response_handler(ResponseIsClientConnectedExpr)
def handle_response_is_client_connected_expr(
    resp: Response, left_expr: ResponseIsClientConnectedExpr
):
    """"""


@create_response_handler(ResponsePICSExpr)
def handle_response_pics_expr(resp: Response, left_expr: ResponsePICSExpr):
    """"""


@create_response_handler(ResponseStatusExpr)
def handle_response_status_expr(resp: Response, left_expr: ResponseStatusExpr):
    """"""


@create_response_handler(ResponseAddHeaderExpr)
def handle_response_add_header_expr(resp: Response, left_expr: ResponseAddHeaderExpr):
    """"""


@create_response_handler(ResponseAppendToLogExpr)
def handle_response_append_to_log_expr(
    resp: Response, left_expr: ResponseAppendToLogExpr
):
    """"""


@create_response_handler(ResponseBinaryWriteExpr)
def handle_response_binary_write_expr(
    resp: Response, left_expr: ResponseBinaryWriteExpr
):
    """"""


@create_response_handler(ResponseClearExpr)
def handle_response_clear_expr(resp: Response, left_expr: ResponseClearExpr):
    """"""


@create_response_handler(ResponseEndExpr)
def handle_response_end_expr(resp: Response, left_expr: ResponseEndExpr):
    """"""


@create_response_handler(ResponseFlushExpr)
def handle_response_flush_expr(resp: Response, left_expr: ResponseFlushExpr):
    """"""


@create_response_handler(ResponseRedirectExpr)
def handle_response_redirect_expr(resp: Response, left_expr: ResponseRedirectExpr):
    """"""


@create_response_handler(ResponseWriteExpr)
def handle_response_write_expr(resp: Response, left_expr: ResponseWriteExpr):
    """"""
