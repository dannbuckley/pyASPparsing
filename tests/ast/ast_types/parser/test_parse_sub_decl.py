import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    ["codeblock", "exp_extended_id", "exp_method_arg_list", "exp_method_stmt_list", "exp_access_mod"],
    [
        (
            "Sub my_subroutine\nEnd Sub\n",
            ExtendedID(Token.identifier(6, 19)),
            [],
            [],
            None
        )
    ]
)
def test_parse_sub_decl(
    codeblock: str,
    exp_extended_id: ExtendedID,
    exp_method_arg_list: typing.List[Arg],
    exp_method_stmt_list: typing.List[MethodStmt],
    exp_access_mod: typing.Optional[AccessModifierType],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        sub_decl = Parser.parse_sub_decl(tkzr, exp_access_mod)
        assert sub_decl.extended_id == exp_extended_id
        assert sub_decl.method_arg_list == exp_method_arg_list
        assert sub_decl.method_stmt_list == exp_method_stmt_list
        assert sub_decl.access_mod == exp_access_mod
        tkzr.advance_pos()
