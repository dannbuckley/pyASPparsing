import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


def test_parse_option_explicit():
    with Tokenizer("<%Option Explicit%>", False) as tkzr:
        tkzr.advance_pos()
        OptionExplicit.from_tokenizer(tkzr)
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_redim_decl_list,exp_preserve",
    [
        (
            "ReDim my_array(10)",
            [
                RedimDecl(
                    ExtendedID("my_array"),
                    [EvalExpr(10)],
                )
            ],
            False,
        ),
        (
            "ReDim my_array(10, 10)",
            [
                RedimDecl(
                    ExtendedID("my_array"),
                    [
                        EvalExpr(10),
                        EvalExpr(10),
                    ],
                )
            ],
            False,
        ),
        (
            "ReDim Preserve my_array(10, 10)",
            [
                RedimDecl(
                    ExtendedID("my_array"),
                    [
                        EvalExpr(10),
                        EvalExpr(10),
                    ],
                )
            ],
            True,
        ),
    ],
)
def test_parse_redim_stmt(
    codeblock: str, exp_redim_decl_list: typing.List[RedimDecl], exp_preserve: bool
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        redim_stmt = RedimStmt.from_tokenizer(tkzr)
        assert redim_stmt.redim_decl_list == exp_redim_decl_list
        assert redim_stmt.preserve == exp_preserve
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_target_expr,exp_assign_expr,exp_is_new",
    [
        (
            # LeftExpr = Expr
            "a = 1",
            LeftExpr("a"),
            EvalExpr(1),
            False,
        ),
        (
            # Set LeftExpr = Expr
            "Set a = 1",
            LeftExpr("a"),
            EvalExpr(1),
            False,
        ),
        (
            # Set LeftExpr = New LeftExpr
            "Set a = New b",
            LeftExpr("a"),
            LeftExpr("b"),
            True,
        ),
        (
            # LeftExpr with omitted expr in index or params list
            "Set a(1,, 3) = 42",
            LeftExpr("a")(EvalExpr(1), None, EvalExpr(3)),
            EvalExpr(42),
            False,
        ),
        (
            # LeftExpr with omitted expr in tail index or params list
            "Set a().b(1,, 3) = 42",
            LeftExpr("a")().get_subname("b")(EvalExpr(1), None, EvalExpr(3)),
            EvalExpr(42),
            False,
        ),
    ],
)
def test_parse_assign_stmt(
    codeblock: str, exp_target_expr: Expr, exp_assign_expr: Expr, exp_is_new: bool
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        assign_stmt = AssignStmt.from_tokenizer(tkzr)
        assert assign_stmt.target_expr == exp_target_expr
        assert assign_stmt.assign_expr == exp_assign_expr
        assert assign_stmt.is_new == exp_is_new
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_left_expr",
    [
        (
            # call QualifiedID with a QualifiedIDTail
            "Call Hello.World()",
            LeftExpr("hello").get_subname("world")(),
        ),
        (
            # no params
            "Call HelloWorld()",
            LeftExpr("helloworld")(),
        ),
        (
            # one param
            "Call HelloWorld(1)",
            LeftExpr("helloworld")(EvalExpr(1)),
        ),
        (
            # multiple IndexOrParam in LeftExpr
            "Call HelloWorld()()",
            LeftExpr("helloworld")()(),
        ),
        (
            # param in later IndexOrParam for LeftExpr
            "Call HelloWorld()(1)",
            LeftExpr("helloworld")()(EvalExpr(1)),
        ),
        (
            # LeftExprTail
            "Call HelloWorld().GoodMorning()",
            LeftExpr("helloworld")().get_subname("goodmorning")(),
        ),
        (
            # multiple IndexOrParam in LeftExprTail
            "Call HelloWorld().GoodMorning()()",
            LeftExpr("helloworld")().get_subname("goodmorning")()(),
        ),
        (
            # param in LeftExprTail
            "Call HelloWorld().GoodMorning(1)",
            LeftExpr("helloworld")().get_subname("goodmorning")(EvalExpr(1)),
        ),
        (
            # multiple params in LeftExprTail
            "Call HelloWorld().GoodMorning(1, 2)",
            LeftExpr("helloworld")().get_subname("goodmorning")(
                EvalExpr(1), EvalExpr(2)
            ),
        ),
        (
            # param in later IndexOrParam for LeftExprTail
            "Call HelloWorld().GoodMorning()(1)",
            LeftExpr("helloworld")().get_subname("goodmorning")()(EvalExpr(1)),
        ),
    ],
)
def test_parse_call_stmt(codeblock: str, exp_left_expr: LeftExpr):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        call_stmt = CallStmt.from_tokenizer(tkzr)
        assert call_stmt.left_expr == exp_left_expr
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_left_expr",
    [
        (
            # left_expr = <QualifiedID> <SubSafeExpr>
            'Response.Write "Hello, world!"',
            ResponseExpr.from_left_expr(
                LeftExpr("response").get_subname("write")(EvalExpr("Hello, world!")),
            ),
        ),
        (
            # left_expr = <QualifiedID> <SubSafeExpr> <CommaExprList>
            'Left.Expr "Hello, world!", "Second string"',
            LeftExpr("left").get_subname("expr")(
                EvalExpr("Hello, world!"), EvalExpr("Second string")
            ),
        ),
        (
            # left_expr = <QualifiedID> <CommaExprList>
            'Left.Expr , "Second param"',
            LeftExpr("left").get_subname("expr")(None, EvalExpr("Second param")),
        ),
        (
            # left_expr = <QualifiedID> '(' ')'
            "Response.End()",
            ResponseExpr.from_left_expr(LeftExpr("response").get_subname("end")()),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')'
            'Response.Write("Hello, world!")',
            ResponseExpr.from_left_expr(
                LeftExpr("response").get_subname("write")(EvalExpr("Hello, world!"))
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')' <CommaExprList>
            'Left.Expr("Hello, world!"), "String at end"',
            LeftExpr("left").get_subname("expr")(EvalExpr("Hello, world!"))(
                None, EvalExpr("String at end")
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')' <CommaExprList>
            'Left.Expr("Hello, world!"), "First",, "Last"',
            LeftExpr("left").get_subname("expr")(EvalExpr("Hello, world!"))(
                None, EvalExpr("First"), None, EvalExpr("Last")
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')' <CommaExprList>
            'Left.Expr("Hello, world!"), "String in middle", "String at end"',
            LeftExpr("left").get_subname("expr")(EvalExpr("Hello, world!"))(
                None, EvalExpr("String in middle"), EvalExpr("String at end")
            ),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail>
            "Left.Expr().WithTail()",
            LeftExpr("left").get_subname("expr")().get_subname("withtail")(),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail> <SubSafeExpr>
            'Left.Expr().WithTail() "Hello, world!"',
            LeftExpr("left")
            .get_subname("expr")()
            .get_subname("withtail")()(EvalExpr("Hello, world!")),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail> <SubSafeExpr> <CommaExprList>
            'Left.Expr().WithTail() "Hello, world!", "Second param"',
            LeftExpr("left")
            .get_subname("expr")()
            .get_subname("withtail")()(
                EvalExpr("Hello, world!"), EvalExpr("Second param")
            ),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail> <CommaExprList>
            'Left.Expr().WithTail() , "Second param"',
            LeftExpr("left")
            .get_subname("expr")()
            .get_subname("withtail")()(None, EvalExpr("Second param")),
        ),
    ],
)
def test_parse_subcall_stmt(
    codeblock: str,
    exp_left_expr: LeftExpr,
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        left_expr = ExpressionParser.parse_left_expr(tkzr, check_for_builtin=False)
        subcall_stmt = SubCallStmt.from_tokenizer(tkzr, left_expr, TokenType.DELIM_END)
        assert subcall_stmt.left_expr == exp_left_expr
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_resume_next,exp_goto_spec",
    [
        ("On Error Resume Next", True, None),
        ("On Error GoTo 0", False, Token.int_literal(16, 17)),
    ],
)
def test_parse_error_stmt(
    codeblock: str, exp_resume_next: bool, exp_goto_spec: typing.Optional[Token]
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        error_stmt = ErrorStmt.from_tokenizer(tkzr)
        assert error_stmt.resume_next == exp_resume_next
        assert error_stmt.goto_spec == exp_goto_spec
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_exit_token",
    [
        ("Exit Do", Token.identifier(7, 9)),
        ("Exit For", Token.identifier(7, 10)),
        ("Exit Function", Token.identifier(7, 15)),
        ("Exit Property", Token.identifier(7, 15)),
        ("Exit Sub", Token.identifier(7, 10)),
    ],
)
def test_parse_exit_stmt(codeblock: str, exp_exit_token: Token):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        exit_stmt = ExitStmt.from_tokenizer(tkzr)
        assert exit_stmt.exit_token == exp_exit_token
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_extended_id", [("Erase my_var", ExtendedID("my_var"))]
)
def test_parse_erase_stmt(codeblock: str, exp_extended_id: ExtendedID):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        erase_stmt = EraseStmt.from_tokenizer(tkzr)
        assert erase_stmt.extended_id == exp_extended_id
        tkzr.advance_pos()
