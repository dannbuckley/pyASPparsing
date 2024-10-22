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
        ("True And False", False),
        ("True And False And True", False),
        ("True And (False And True)", False),
        ("True And False And True And False", False),
        ("Not False And True", True),
        ("True And Not False", True),
        ("Not False And Not False", True),
        ("Not Not True And True", True),
        ("1 = 1 And True", True),
        ("True And 1 = 1", True),
        ("1 = 1 And 2 = 2", True),
        ("Not 1 <> 1 And 2 = 2", True),
        ("1 = 1 And Not 2 <> 2", True),
        ("Not 1 <> 1 And Not 2 <> 2", True),
    ],
)
def test_parse_and_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        and_expr: Expr = ExpressionParser.parse_and_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(and_expr, EvalExpr)
        assert and_expr.expr_value == expr_value
