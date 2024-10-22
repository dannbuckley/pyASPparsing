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
        ("True Or False", True),
        ("True Or False Or True", True),
        ("True Or (False Or True)", True),
        ("True Or False Or True Or False", True),
        ("True And False Or True", True),
        ("True Or False And True", True),
        ("True And False Or True And False", False),
    ],
)
def test_parse_or_expr_folded(
    exp_code: str, expr_value: typing.Union[int, float, bool, str]
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        or_expr: Expr = ExpressionParser.parse_or_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(or_expr, EvalExpr)
        assert or_expr.expr_value == expr_value
