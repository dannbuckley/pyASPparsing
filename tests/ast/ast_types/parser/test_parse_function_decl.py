import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    ["codeblock", "exp_extended_id", "exp_method_arg_list", "exp_method_stmt_list", "exp_access_mod"], []
)
def test_parse_function_decl(
    codeblock: str,
    exp_extended_id: ExtendedID,
    exp_method_arg_list: typing.List[Arg],
    exp_method_stmt_list: typing.List[MethodStmt],
    exp_access_mod: typing.Optional[AccessModifierType],
):
    pass
