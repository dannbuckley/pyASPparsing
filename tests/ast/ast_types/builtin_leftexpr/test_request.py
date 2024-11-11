import pytest
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.builtin_leftexpr.request import *
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer


def test_request_anonymous():
    with Tokenizer('<%=Request("whereami")%>', False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestAnonymousExpr)
        assert (
            len(req_expr.call_args) == 1
            and len(req_expr.call_args[0]) == 1
            and req_expr.call_args[0][0] == EvalExpr("whereami")
        )


@pytest.mark.parametrize(
    "exp_code,cert_key",
    [
        ("Request.ClientCertificate", None),
        ('Request.ClientCertificate("Issuer")', EvalExpr("Issuer")),
    ],
)
def test_request_clientcertificate(exp_code: str, cert_key):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestClientCertificateExpr)
        assert req_expr.cert_key == cert_key


@pytest.mark.parametrize(
    "exp_code,cookie_name,cookie_key,cookie_attribute",
    [
        ('Request.Cookies("cookie")', EvalExpr("cookie"), None, None),
        ('Request.Cookies("cookie")("key")', EvalExpr("cookie"), EvalExpr("key"), None),
        ('Request.Cookies("cookie").haskeys', EvalExpr("cookie"), None, "haskeys"),
    ],
)
def test_request_cookies(exp_code: str, cookie_name, cookie_key, cookie_attribute):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestCookiesExpr)
        assert req_expr.cookie_name == cookie_name
        assert req_expr.cookie_key == cookie_key
        assert req_expr.cookie_attribute == cookie_attribute


@pytest.mark.parametrize(
    "exp_code,element,index,has_count",
    [
        ('Request.Form("input")', EvalExpr("input"), None, False),
        ('Request.Form("input")(5)', EvalExpr("input"), EvalExpr(5), False),
        ('Request.Form("input").Count', EvalExpr("input"), None, True),
    ],
)
def test_request_form(exp_code: str, element, index, has_count: bool):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestFormExpr)
        assert req_expr.element == element
        assert req_expr.index == index
        assert req_expr.has_count == has_count


@pytest.mark.parametrize(
    "exp_code,variable,index,has_count",
    [
        ('Request.QueryString("queryvar")', EvalExpr("queryvar"), None, False),
        (
            'Request.QueryString("queryvar")(2)',
            EvalExpr("queryvar"),
            EvalExpr(2),
            False,
        ),
        ('Request.QueryString("queryvar").Count', EvalExpr("queryvar"), None, True),
    ],
)
def test_request_querystring(exp_code: str, variable, index, has_count: bool):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestQueryStringExpr)
        assert req_expr.variable == variable
        assert req_expr.index == index
        assert req_expr.has_count == has_count


@pytest.mark.parametrize(
    "exp_code,server_variable",
    [
        ("Request.ServerVariables", None),
        ('Request.ServerVariables("REQUEST_METHOD")', EvalExpr("REQUEST_METHOD")),
    ],
)
def test_request_servervariables(exp_code: str, server_variable):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestServerVariablesExpr)
        assert req_expr.server_variable == server_variable


def test_request_totalbytes():
    with Tokenizer("<%=Request.TotalBytes%>", False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestTotalBytesExpr)


def test_request_binaryread():
    with Tokenizer("<%=Request.BinaryRead(Request.TotalBytes)", False) as tkzr:
        tkzr.advance_pos()
        req_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(req_expr, RequestBinaryReadExpr)
        assert isinstance(req_expr.param_count, RequestTotalBytesExpr)
