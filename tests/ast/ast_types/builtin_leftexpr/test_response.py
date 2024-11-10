import pytest
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.builtin_leftexpr.response import *
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer


@pytest.mark.parametrize(
    "exp_code,exp_type",
    [
        (
            "Response.Buffer",
            ResponseBufferExpr("response").get_subname("buffer"),
        ),
        (
            "Response.CacheControl",
            ResponseCacheControlExpr("response").get_subname("cachecontrol"),
        ),
        (
            "Response.Charset",
            ResponseCharsetExpr("response").get_subname("charset"),
        ),
        (
            "Response.ContentType",
            ResponseContentTypeExpr("response").get_subname("contenttype"),
        ),
        (
            "Response.Expires",
            ResponseExpiresExpr("response").get_subname("expires"),
        ),
        (
            "Response.ExpiresAbsolute",
            ResponseExpiresAbsoluteExpr("response").get_subname("expiresabsolute"),
        ),
        (
            "Response.IsClientConnected",
            ResponseIsClientConnectedExpr("response").get_subname("isclientconnected"),
        ),
        (
            'Response.PICS("")',
            ResponsePICSExpr("response")
            .get_subname("pics")(EvalExpr(""))
            .track_index_or_param(),
        ),
        (
            "Response.Status",
            ResponseStatusExpr("response").get_subname("status"),
        ),
        (
            "Response.Clear",
            ResponseClearExpr("response").get_subname("clear"),
        ),
        (
            "Response.Clear()",
            ResponseClearExpr("response").get_subname("clear")().track_index_or_param(),
        ),
        (
            "Response.End",
            ResponseEndExpr("response").get_subname("end"),
        ),
        (
            "Response.End()",
            ResponseEndExpr("response").get_subname("end")().track_index_or_param(),
        ),
        (
            "Response.Flush",
            ResponseFlushExpr("response").get_subname("flush"),
        ),
        (
            "Response.Flush()",
            ResponseFlushExpr("response").get_subname("flush")().track_index_or_param(),
        ),
    ],
)
def test_response(exp_code: str, exp_type: ResponseExpr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        resp_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert resp_expr == exp_type


@pytest.mark.parametrize(
    "exp_code,exp_name,exp_key,exp_attribute",
    [
        ('Response.Cookies("cookie")', EvalExpr("cookie"), None, None),
        (
            'Response.Cookies("cookie")("key")',
            EvalExpr("cookie"),
            EvalExpr("key"),
            None,
        ),
        ('Response.Cookies("cookie").domain', EvalExpr("cookie"), None, "domain"),
        ('Response.Cookies("cookie").expires', EvalExpr("cookie"), None, "expires"),
        ('Response.Cookies("cookie").haskeys', EvalExpr("cookie"), None, "haskeys"),
        ('Response.Cookies("cookie").path', EvalExpr("cookie"), None, "path"),
        ('Response.Cookies("cookie").secure', EvalExpr("cookie"), None, "secure"),
    ],
)
def test_response_cookies(exp_code: str, exp_name, exp_key, exp_attribute):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        resp_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(resp_expr, ResponseCookiesExpr)
        assert resp_expr.cookie_name == exp_name
        assert resp_expr.cookie_key == exp_key
        assert resp_expr.cookie_attribute == exp_attribute


def test_response_addheader():
    with Tokenizer('<%=Response.AddHeader("header", "value")%>', False) as tkzr:
        tkzr.advance_pos()
        resp_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(resp_expr, ResponseAddHeaderExpr)
        assert resp_expr.param_name == EvalExpr("header")
        assert resp_expr.param_value == EvalExpr("value")


def test_response_appendtolog():
    with Tokenizer('<%=Response.AppendToLog("my debug info")', False) as tkzr:
        tkzr.advance_pos()
        resp_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(resp_expr, ResponseAppendToLogExpr)
        assert resp_expr.param_string == EvalExpr("my debug info")


def test_response_binarywrite():
    with Tokenizer("<%=Response.BinaryWrite(data)%>", False) as tkzr:
        tkzr.advance_pos()
        resp_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(resp_expr, ResponseBinaryWriteExpr)
        assert resp_expr.param_data == LeftExpr("data")


def test_response_redirect():
    with Tokenizer('<%=Response.Redirect("https://www.google.com")%>', False) as tkzr:
        tkzr.advance_pos()
        resp_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(resp_expr, ResponseRedirectExpr)
        assert resp_expr.param_url == EvalExpr("https://www.google.com")


def test_response_write():
    with Tokenizer('<%=Response.Write("Hello, world!")%>', False) as tkzr:
        tkzr.advance_pos()
        resp_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(resp_expr, ResponseWriteExpr)
        assert resp_expr.param_variant == EvalExpr("Hello, world!")
