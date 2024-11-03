import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    [
        "codeblock",
        "exp_extended_id",
        "exp_method_arg_list",
        "exp_method_stmt_list",
        "exp_access_mod",
    ],
    [
        (
            # function declaration
            "Function my_function\nEnd Function\n",
            ExtendedID("my_function"),
            [],
            [],
            None,
        ),
        (
            # function declaration with parentheses
            "Function my_function()\nEnd Function\n",
            ExtendedID("my_function"),
            [],
            [],
            None,
        ),
        (
            # function declaration with arg
            "Function my_function(first)\nEnd Function\n",
            ExtendedID("my_function"),
            [Arg(ExtendedID("first"))],
            [],
            None,
        ),
        (
            # function declaration with paren arg
            "Function my_function(first())\nEnd Function\n",
            ExtendedID("my_function"),
            [Arg(ExtendedID("first"), has_paren=True)],
            [],
            None,
        ),
        (
            # function declaration with byval arg
            "Function my_function(ByVal first)\nEnd Function\n",
            ExtendedID("my_function"),
            [
                Arg(
                    ExtendedID("first"),
                    arg_modifier=Token.identifier(23, 28),
                )
            ],
            [],
            None,
        ),
        (
            # function declaration with byref arg
            "Function my_function(ByRef first)\nEnd Function\n",
            ExtendedID("my_function"),
            [
                Arg(
                    ExtendedID("first"),
                    arg_modifier=Token.identifier(23, 28),
                )
            ],
            [],
            None,
        ),
        (
            # function declaration with multiple args
            "Function my_function(first, second)\nEnd Function\n",
            ExtendedID("my_function"),
            [
                Arg(ExtendedID("first")),
                Arg(ExtendedID("second")),
            ],
            [],
            None,
        ),
        (
            # private function
            "Private Function my_function\nEnd Function\n",
            ExtendedID("my_function"),
            [],
            [],
            AccessModifierType.PRIVATE,
        ),
        (
            # public function
            "Public Function my_function\nEnd Function\n",
            ExtendedID("my_function"),
            [],
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public default function
            "Public Default Function my_function\nEnd Function\n",
            ExtendedID("my_function"),
            [],
            [],
            AccessModifierType.PUBLIC_DEFAULT,
        ),
        (
            # function with inline statement
            "Function my_function Set a = 1 End Function\n",
            ExtendedID("my_function"),
            [],
            [
                AssignStmt(
                    LeftExpr("a"),
                    EvalExpr(1),
                )
            ],
            None,
        ),
        (
            # function with statement list
            "Function my_function\nDim a, b\nEnd Function\n",
            ExtendedID("my_function"),
            [],
            [
                VarDecl(
                    [
                        VarName(ExtendedID("a")),
                        VarName(ExtendedID("b")),
                    ]
                )
            ],
            None,
        ),
    ],
)
def test_parse_function_decl(
    codeblock: str,
    exp_extended_id: ExtendedID,
    exp_method_arg_list: typing.List[Arg],
    exp_method_stmt_list: typing.List[MethodStmt],
    exp_access_mod: typing.Optional[AccessModifierType],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        if exp_access_mod is not None:
            tkzr.advance_pos()
            if exp_access_mod == AccessModifierType.PUBLIC_DEFAULT:
                tkzr.advance_pos()
        function_decl = Parser.parse_function_decl(tkzr, exp_access_mod)
        tkzr.advance_pos()
        assert function_decl.extended_id == exp_extended_id
        assert function_decl.method_arg_list == exp_method_arg_list
        assert function_decl.method_stmt_list == exp_method_stmt_list
        assert function_decl.access_mod == exp_access_mod
