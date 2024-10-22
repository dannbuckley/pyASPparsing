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
        ("True Eqv True", True),
        ("True Eqv False Eqv True", False),
        ("True Eqv (False Eqv True)", False),
        ("True Eqv False Eqv True Eqv False", True), # (False) Eqv False
        ("True Xor False Eqv True", True),
        ("True Eqv False Xor True", True),
        ("True Xor False Eqv True Xor False", True),
    ],
)
def test_parse_eqv_expr_folded(exp_code: str, expr_value: typing.Union[int, float, bool, str]):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        eqv_expr: Expr = ExpressionParser.parse_eqv_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(eqv_expr, EvalExpr)
        assert eqv_expr.expr_value == expr_value
