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
            # sub declaration
            "Sub my_subroutine\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [],
            None,
        ),
        (
            # sub declaration with parentheses
            "Sub my_subroutine()\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [],
            None,
        ),
        (
            # sub declaration with arg
            "Sub my_subroutine(first)\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [Arg(ExtendedID("first"))],
            [],
            None,
        ),
        (
            # sub declaration with paren arg
            "Sub my_subroutine(first())\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [Arg(ExtendedID("first"), has_paren=True)],
            [],
            None,
        ),
        (
            # sub declaration with byval arg
            "Sub my_subroutine(ByVal first)\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [
                Arg(
                    ExtendedID("first"),
                    arg_modifier=Token.identifier(20, 25),
                )
            ],
            [],
            None,
        ),
        (
            # sub declaration with byref arg
            "Sub my_subroutine(ByRef first)\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [
                Arg(
                    ExtendedID("first"),
                    arg_modifier=Token.identifier(20, 25),
                )
            ],
            [],
            None,
        ),
        (
            # sub declaration with multiple args
            "Sub my_subroutine(first, second)\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [
                Arg(ExtendedID("first")),
                Arg(ExtendedID("second")),
            ],
            [],
            None,
        ),
        (
            # private sub
            "Private Sub my_subroutine\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [],
            AccessModifierType.PRIVATE,
        ),
        (
            # public sub
            "Public Sub my_subroutine\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public default sub
            "Public Default Sub my_subroutine\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [],
            AccessModifierType.PUBLIC_DEFAULT,
        ),
        (
            # sub with inline statement
            "Sub my_subroutine Set a = 1 End Sub\n",
            ExtendedID("my_subroutine"),
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
            # sub with statement list
            "Sub my_subroutine\nDim c, d\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [
                VarDecl(
                    [
                        VarName(ExtendedID("c")),
                        VarName(ExtendedID("d")),
                    ]
                )
            ],
            None,
        ),
        (
            # const declaration as method statement
            "Sub my_subroutine\nConst a = 42\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [
                ConstDecl(
                    [
                        ConstListItem(
                            ExtendedID("a"),
                            EvalExpr(42),
                        )
                    ]
                )
            ],
            None,
        ),
        (
            # public const declaration as method statement
            "Sub my_subroutine\nPublic Const a = 42\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [
                ConstDecl(
                    [
                        ConstListItem(
                            ExtendedID("a"),
                            EvalExpr(42),
                        )
                    ],
                    access_mod=AccessModifierType.PUBLIC,
                )
            ],
            None,
        ),
        (
            # private const declaration as method statement
            "Sub my_subroutine\nPrivate Const a = 42\nEnd Sub\n",
            ExtendedID("my_subroutine"),
            [],
            [
                ConstDecl(
                    [
                        ConstListItem(
                            ExtendedID("a"),
                            EvalExpr(42),
                        )
                    ],
                    access_mod=AccessModifierType.PRIVATE,
                )
            ],
            None,
        ),
    ],
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
        if exp_access_mod is not None:
            tkzr.advance_pos()
            if exp_access_mod == AccessModifierType.PUBLIC_DEFAULT:
                tkzr.advance_pos()
        sub_decl = Parser.parse_sub_decl(tkzr, exp_access_mod)
        tkzr.advance_pos()
        assert sub_decl.extended_id == exp_extended_id
        assert sub_decl.method_arg_list == exp_method_arg_list
        assert sub_decl.method_stmt_list == exp_method_stmt_list
        assert sub_decl.access_mod == exp_access_mod
