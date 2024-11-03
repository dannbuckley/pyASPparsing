import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldableExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("a", LeftExpr("a")),
        (
            "a(1,, 3)",
            LeftExpr("a")(EvalExpr(1), None, EvalExpr(3)),
        ),
        (
            "a().b(1,, 3)",
            LeftExpr("a")().get_subname("b")(EvalExpr(1), None, EvalExpr(3)),
        ),
        (
            "Hello.World()",
            LeftExpr("hello").get_subname("world")(),
        ),
        (
            "HelloWorld()",
            LeftExpr("helloworld")(),
        ),
        (
            "HelloWorld(1)",
            LeftExpr("helloworld")(EvalExpr(1)),
        ),
        (
            "HelloWorld((1))",
            LeftExpr("helloworld")(EvalExpr(1)),
        ),
        (
            "HelloWorld(a)",
            LeftExpr("helloworld")(LeftExpr("a")),
        ),
        (
            "HelloWorld()()",
            LeftExpr("helloworld")()(),
        ),
        (
            "HelloWorld()(1)",
            LeftExpr("helloworld")()(EvalExpr(1)),
        ),
        (
            "HelloWorld().GoodMorning()",
            LeftExpr("helloworld")().get_subname("goodmorning")(),
        ),
        (
            "HelloWorld().GoodMorning()()",
            LeftExpr("helloworld")().get_subname("goodmorning")()(),
        ),
        (
            "HelloWorld().GoodMorning(1)",
            LeftExpr("helloworld")().get_subname("goodmorning")(EvalExpr(1)),
        ),
        (
            "HelloWorld().GoodMorning(1, 2)",
            LeftExpr("helloworld")().get_subname("goodmorning")(
                EvalExpr(1), EvalExpr(2)
            ),
        ),
        (
            "HelloWorld().GoodMorning()(1)",
            LeftExpr("helloworld")().get_subname("goodmorning")()(EvalExpr(1)),
        ),
    ],
)
def test_parse_left_expr(expr_code: str, expr_val: Expr):
    with Tokenizer(f"<%={expr_code}%>", False) as tkzr:
        tkzr.advance_pos()
        left_expr: Expr = ExpressionParser.parse_left_expr(tkzr)
        assert left_expr == expr_val
