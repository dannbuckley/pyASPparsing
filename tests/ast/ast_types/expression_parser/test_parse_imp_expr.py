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
        ("True Imp True", True),
        ("True Imp False Imp True", True),
        ("True Imp (False Imp True)", True),
        ("True Imp False Imp True Imp False", False),
        ("True Eqv False Imp True", True),
        ("True Imp False Eqv True", False),
        ("True Eqv False Imp True Eqv False", True),
    ],
)
def test_parse_imp_expr_folded(exp_code: str, expr_value: typing.Union[int, float, bool, str]):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        imp_expr: Expr = ExpressionParser.parse_imp_expr(tkzr)
        tkzr.advance_pos()
        assert isinstance(imp_expr, EvalExpr)
        assert imp_expr.expr_value == expr_value
