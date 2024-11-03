import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parser import Parser


@pytest.mark.parametrize(
    "codeblock,exp_extended_id,exp_member_decl_list",
    [
        ("Class MyClass\nEnd Class\n", ExtendedID("myclass"), []),
        (
            # class with private field declaration
            "Class MyClass\nPrivate my_var\nEnd Class\n",
            ExtendedID("myclass"),
            [
                FieldDecl(
                    FieldName(FieldID("my_var")),
                    access_mod=AccessModifierType.PRIVATE,
                )
            ],
        ),
        (
            # class with public field declaration
            "Class MyClass\nPublic my_var\nEnd Class\n",
            ExtendedID("myclass"),
            [
                FieldDecl(
                    FieldName(FieldID("my_var")),
                    access_mod=AccessModifierType.PUBLIC,
                )
            ],
        ),
        (
            # class with variable declaration
            "Class MyClass\nDim my_var\nEnd Class\n",
            ExtendedID("myclass"),
            [VarDecl([VarName(ExtendedID("my_var"))])],
        ),
        (
            # class with const declaration
            "Class MyClass\nConst a = 42\nEnd Class\n",
            ExtendedID("myclass"),
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
        ),
        (
            # class with public const declaration
            "Class MyClass\nPublic Const a = 42\nEnd Class\n",
            ExtendedID("myclass"),
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
        ),
        (
            # class with private const declaration
            "Class MyClass\nPrivate Const a = 42\nEnd Class\n",
            ExtendedID("myclass"),
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
        ),
        (
            # class with sub declaration
            "Class MyClass\nSub my_subroutine\nEnd Sub\nEnd Class\n",
            ExtendedID("myclass"),
            [SubDecl(ExtendedID("my_subroutine"))],
        ),
        (
            # class with function declaration
            "Class MyClass\nFunction my_function\nEnd Function\nEnd Class\n",
            ExtendedID("myclass"),
            [FunctionDecl(ExtendedID("my_function"))],
        ),
        (
            # class with get property declaration
            "Class MyClass\nProperty Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [PropertyDecl(PropertyAccessType.PROPERTY_GET, ExtendedID("my_property"))],
        ),
        (
            # class with let property declaration
            "Class MyClass\nProperty Let my_property\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [PropertyDecl(PropertyAccessType.PROPERTY_LET, ExtendedID("my_property"))],
        ),
        (
            # class with set property declaration
            "Class MyClass\nProperty Set my_property\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [PropertyDecl(PropertyAccessType.PROPERTY_SET, ExtendedID("my_property"))],
        ),
        (
            # class with property declaration, empty arg list
            "Class MyClass\nProperty Get my_property()\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [PropertyDecl(PropertyAccessType.PROPERTY_GET, ExtendedID("my_property"))],
        ),
        (
            # class with property declaration, single arg
            "Class MyClass\nProperty Get my_property(first)\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    [Arg(ExtendedID("first"))],
                )
            ],
        ),
        (
            # class with property declaration, single arg with paren
            "Class MyClass\nProperty Get my_property(first())\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    [Arg(ExtendedID("first"), has_paren=True)],
                )
            ],
        ),
        (
            # class with property declaration, byval arg
            "Class MyClass\nProperty Get my_property(ByVal first)\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    [
                        Arg(
                            ExtendedID("first"),
                            arg_modifier=ArgModifierType.ARG_VALUE,
                        )
                    ],
                )
            ],
        ),
        (
            # class with property declaration, byref arg
            "Class MyClass\nProperty Get my_property(ByRef first)\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    [
                        Arg(
                            ExtendedID("first"),
                            arg_modifier=ArgModifierType.ARG_REFERENCE,
                        )
                    ],
                )
            ],
        ),
        (
            # class with property declaration, multiple args
            "Class MyClass\nProperty Get my_property(first, second)\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    [
                        Arg(ExtendedID("first")),
                        Arg(ExtendedID("second")),
                    ],
                )
            ],
        ),
        (
            # class with property declaration, single method statement
            "Class MyClass\nProperty Get my_property\nDim c, d\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    method_stmt_list=[
                        VarDecl(
                            [
                                VarName(ExtendedID("c")),
                                VarName(ExtendedID("d")),
                            ]
                        )
                    ],
                )
            ],
        ),
        (
            "Class MyClass\nPublic Property Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    access_mod=AccessModifierType.PUBLIC,
                )
            ],
        ),
        (
            "Class MyClass\nPublic Default Property Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
                    access_mod=AccessModifierType.PUBLIC_DEFAULT,
                )
            ],
        ),
        (
            "Class MyClass\nPrivate Property Get my_property\nEnd Property\nEnd Class\n",
            ExtendedID("myclass"),
            [
                PropertyDecl(
                    PropertyAccessType.PROPERTY_GET,
                    ExtendedID("my_property"),
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
        tkzr.advance_pos()
        assert class_decl.extended_id == exp_extended_id
        assert class_decl.member_decl_list == exp_member_decl_list
