import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *


def test_parse_option_explicit():
    pass


def test_parse_redim_stmt(
    codeblock: str, exp_redim_decl_list: typing.List[RedimDecl], exp_preserve: bool
):
    pass


def test_parse_assign_stmt(
    codeblock: str, exp_target_expr: Expr, exp_assign_expr: Expr, exp_is_new: bool
):
    pass


def test_parse_call_stmt(codeblock: str, exp_left_expr: LeftExpr):
    pass


def test_parse_error_stmt(
    codeblock: str, exp_resume_next: bool, exp_goto_spec: typing.Optional[Token]
):
    pass


def test_parse_exit_stmt(codeblock: str, exp_exit_token: Token):
    pass


def test_parse_erase_stmt(codeblock: str, exp_extended_id: ExtendedID):
    pass
