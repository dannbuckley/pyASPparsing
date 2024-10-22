import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.optimize import FoldableExpr
from pyaspparsing.ast.ast_types.expression_parser import ExpressionParser


@pytest.mark.parametrize(
    "exp_code,expr_value",
    [
        ("6 Mod 2", 0),
        ("6 Mod 4 Mod 2", 0),
        ("6 Mod (5 Mod 2)", 0),
        ("8 Mod 6 Mod 4 Mod 2", 0),
        ("6 \\ 2 Mod 4", 3),
        ("6 Mod 4 \\ 2", 0),
        ("6 \\ 2 Mod 8 \\ 4", 1),
    ],
)
def test_parse_mod_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mod_expr: Expr = ExpressionParser.parse_mod_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(mod_expr, EvalExpr)
        assert mod_expr.expr_value == expr_value
