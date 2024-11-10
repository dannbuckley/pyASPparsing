import pytest
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.builtin_leftexpr.server import *
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer


def test_server_scripttimeout():
    with Tokenizer("<%=Server.ScriptTimeout%>", False) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerScriptTimeoutExpr)


def test_server_createobject():
    with Tokenizer('<%=Server.CreateObject("ADODB.Connection")%>', False) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerCreateObjectExpr)
        assert serv_expr.param_progid == EvalExpr("ADODB.Connection")


def test_server_execute():
    with Tokenizer('<%=Server.Execute("scriptpath.asp")%>', False) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerExecuteExpr)
        assert serv_expr.param_path == EvalExpr("scriptpath.asp")


@pytest.mark.parametrize(
    "exp_code", [("Server.GetLastError"), ("Server.GetLastError()")]
)
def test_server_getlasterror(exp_code: str):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerGetLastErrorExpr)


def test_server_htmlencode():
    with Tokenizer(
        '<%=Server.HTMLEncode("String with <special> characters")%>', False
    ) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerHTMLEncodeExpr)
        assert serv_expr.param_string == EvalExpr("String with <special> characters")


def test_server_mappath():
    with Tokenizer('<%=Server.MapPath("scriptpath.asp")%>', False) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerMapPathExpr)
        assert serv_expr.param_path == EvalExpr("scriptpath.asp")


def test_server_transfer():
    with Tokenizer('<%=Server.Transfer("scriptpath.asp")%>', False) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerTransferExpr)
        assert serv_expr.param_path == EvalExpr("scriptpath.asp")


def test_server_urlencode():
    with Tokenizer('<%=Server.URLEncode("https://www.google.com")', False) as tkzr:
        tkzr.advance_pos()
        serv_expr = ExpressionParser.parse_left_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(serv_expr, ServerURLEncodeExpr)
        assert serv_expr.param_string == EvalExpr("https://www.google.com")
