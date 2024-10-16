import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    "codeblock,exp_extended_id,exp_member_decl_list",
    [
        ("Class MyClass\nEnd Class\n", ExtendedID(Token.identifier(8, 15)), []),
        (
            # class with private field declaration
            "Class MyClass\nPrivate my_var\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                FieldDecl(
                    FieldName(FieldID(Token.identifier(24, 30))),
                    access_mod=AccessModifierType.PRIVATE,
                )
            ],
        ),
        (
            # class with public field declaration
            "Class MyClass\nPublic my_var\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                FieldDecl(
                    FieldName(FieldID(Token.identifier(23, 29))),
                    access_mod=AccessModifierType.PUBLIC,
                )
            ],
        ),
        (
            # class with variable declaration
            "Class MyClass\nDim my_var\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [VarDecl([VarName(ExtendedID(Token.identifier(20, 26)))])],
        ),
        (
            # class with const declaration
            "Class MyClass\nConst a = 42\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                ConstDecl(
                    [
                        ConstListItem(
                            ExtendedID(Token.identifier(22, 23)),
                            IntLiteral(Token.int_literal(26, 28)),
                        )
                    ]
                )
            ],
        ),
        (
            # class with public const declaration
            "Class MyClass\nPublic Const a = 42\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                ConstDecl(
                    [
                        ConstListItem(
                            ExtendedID(Token.identifier(29, 30)),
                            IntLiteral(Token.int_literal(33, 35)),
                        )
                    ],
                    access_mod=AccessModifierType.PUBLIC,
                )
            ],
        ),
        (
            # class with private const declaration
            "Class MyClass\nPrivate Const a = 42\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                ConstDecl(
                    [
                        ConstListItem(
                            ExtendedID(Token.identifier(30, 31)),
                            IntLiteral(Token.int_literal(34, 36)),
                        )
                    ],
                    access_mod=AccessModifierType.PRIVATE,
                )
            ],
        ),
        (
            # class with sub declaration
            "Class MyClass\nSub my_subroutine\nEnd Sub\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [SubDecl(ExtendedID(Token.identifier(20, 33)))],
        ),
        (
            # class with function declaration
            "Class MyClass\nFunction my_function\nEnd Function\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [FunctionDecl(ExtendedID(Token.identifier(25, 36)))],
        ),
        (
            # class with get property declaration
            "Class MyClass\nProperty Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28), ExtendedID(Token.identifier(29, 40))
                )
            ],
        ),
        (
            # class with let property declaration
            "Class MyClass\nProperty Let my_property\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28), ExtendedID(Token.identifier(29, 40))
                )
            ],
        ),
        (
            # class with set property declaration
            "Class MyClass\nProperty Set my_property\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28), ExtendedID(Token.identifier(29, 40))
                )
            ],
        ),
        (
            # class with property declaration, empty arg list
            "Class MyClass\nProperty Get my_property()\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28), ExtendedID(Token.identifier(29, 40))
                )
            ],
        ),
        (
            # class with property declaration, single arg
            "Class MyClass\nProperty Get my_property(first)\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28),
                    ExtendedID(Token.identifier(29, 40)),
                    [Arg(ExtendedID(Token.identifier(41, 46)))],
                )
            ],
        ),
        (
            # class with property declaration, single arg with paren
            "Class MyClass\nProperty Get my_property(first())\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28),
                    ExtendedID(Token.identifier(29, 40)),
                    [Arg(ExtendedID(Token.identifier(41, 46)), has_paren=True)],
                )
            ],
        ),
        (
            # class with property declaration, byval arg
            "Class MyClass\nProperty Get my_property(ByVal first)\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28),
                    ExtendedID(Token.identifier(29, 40)),
                    [
                        Arg(
                            ExtendedID(Token.identifier(47, 52)),
                            arg_modifier=Token.identifier(41, 46),
                        )
                    ],
                )
            ],
        ),
        (
            # class with property declaration, byref arg
            "Class MyClass\nProperty Get my_property(ByRef first)\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28),
                    ExtendedID(Token.identifier(29, 40)),
                    [
                        Arg(
                            ExtendedID(Token.identifier(47, 52)),
                            arg_modifier=Token.identifier(41, 46),
                        )
                    ],
                )
            ],
        ),
        (
            # class with property declaration, multiple args
            "Class MyClass\nProperty Get my_property(first, second)\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28),
                    ExtendedID(Token.identifier(29, 40)),
                    [
                        Arg(ExtendedID(Token.identifier(41, 46))),
                        Arg(ExtendedID(Token.identifier(48, 54))),
                    ],
                )
            ],
        ),
        (
            # class with property declaration, single method statement
            "Class MyClass\nProperty Get my_property\nDim c, d\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(25, 28),
                    ExtendedID(Token.identifier(29, 40)),
                    method_stmt_list=[
                        VarDecl(
                            [
                                VarName(ExtendedID(Token.identifier(45, 46))),
                                VarName(ExtendedID(Token.identifier(48, 49))),
                            ]
                        )
                    ],
                )
            ],
        ),
        (
            "Class MyClass\nPublic Property Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(32, 35),
                    ExtendedID(Token.identifier(36, 47)),
                    access_mod=AccessModifierType.PUBLIC,
                )
            ],
        ),
        (
            "Class MyClass\nPublic Default Property Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(40, 43),
                    ExtendedID(Token.identifier(44, 55)),
                    access_mod=AccessModifierType.PUBLIC_DEFAULT,
                )
            ],
        ),
        (
            "Class MyClass\nPrivate Property Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID(Token.identifier(8, 15)),
            [
                PropertyDecl(
                    Token.identifier(33, 36),
                    ExtendedID(Token.identifier(37, 48)),
                    access_mod=AccessModifierType.PRIVATE,
                )
            ],
        ),
    ],
)
def test_parse_class_decl(
    codeblock: str,
    exp_extended_id: ExtendedID,
    exp_member_decl_list: typing.List[MemberDecl],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        class_decl = Parser.parse_class_decl(tkzr)
        assert class_decl.extended_id == exp_extended_id
        assert class_decl.member_decl_list == exp_member_decl_list
        tkzr.advance_pos()
