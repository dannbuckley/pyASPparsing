import typing
import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *


@pytest.mark.parametrize(
    "codeblock,exp_field_name,exp_other_vars,exp_access_mod",
    [
        (
            # private field declaration
            "Private my_var",
            FieldName(FieldID("my_var")),
            [],
            AccessModifierType.PRIVATE,
        ),
        (
            # public field declaration
            "Public my_var",
            FieldName(FieldID("my_var")),
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with array rank list
            "Public my_var(1)",
            FieldName(FieldID("my_var"), [1]),
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with array rank list
            "Public my_var(1, 2)",
            FieldName(
                FieldID("my_var"),
                [1, 2],
            ),
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with other var
            "Public my_var, my_other_var",
            FieldName(FieldID("my_var")),
            [VarName(ExtendedID("my_other_var"))],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with multiple other var
            "Public my_var, my_other_var, yet_another",
            FieldName(FieldID("my_var")),
            [
                VarName(ExtendedID("my_other_var")),
                VarName(ExtendedID("yet_another")),
            ],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with other var
            "Public my_var, my_other_var(1)",
            FieldName(FieldID("my_var")),
            [VarName(ExtendedID("my_other_var"), [1])],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with other var
            "Public my_var, my_other_var(1, 2)",
            FieldName(FieldID("my_var")),
            [
                VarName(
                    ExtendedID("my_other_var"),
                    [1, 2],
                )
            ],
            AccessModifierType.PUBLIC,
        ),
    ],
)
def test_parse_field_decl(
    codeblock: str,
    exp_field_name: FieldName,
    exp_other_vars: typing.List[VarName],
    exp_access_mod: typing.Optional[AccessModifierType],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        # access modifier consumed before reaching FieldDecl.from_tokenizer()
        tkzr.advance_pos()
        field_decl = FieldDecl.from_tokenizer(tkzr, exp_access_mod)
        assert field_decl.field_name == exp_field_name
        assert field_decl.other_vars == exp_other_vars
        assert field_decl.access_mod == exp_access_mod
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_var_name",
    [
        ("Dim my_var", [VarName(ExtendedID("my_var"))]),
        (
            "Dim vara, var_b",
            [
                VarName(ExtendedID("vara")),
                VarName(ExtendedID("var_b")),
            ],
        ),
        (
            "Dim my_array(3)",
            [VarName(ExtendedID("my_array"), [3])],
        ),
        ("Dim my_array()", [VarName(ExtendedID("my_array"))]),
        (
            "Dim my_array(3,)",
            [VarName(ExtendedID("my_array"), [3])],
        ),
        (
            "Dim my_table(4, 6)",
            [
                VarName(
                    ExtendedID("my_table"),
                    [4, 6],
                )
            ],
        ),
    ],
)
def test_parse_var_decl(codeblock: str, exp_var_name: typing.List[VarName]):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        var_decl = VarDecl.from_tokenizer(tkzr)
        assert var_decl.var_name == exp_var_name
        tkzr.advance_pos()


@pytest.mark.parametrize(
    "codeblock,exp_const_list,exp_access_mod",
    [
        (
            # const declaration
            "Const a = 1",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(1),
                )
            ],
            None,
        ),
        (
            # const declaration with paren ConstExprDef
            "Const a = (1)",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(1),
                )
            ],
            None,
        ),
        (
            # const declaration with nested paren ConstExprDef
            "Const a = ((1))",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(1),
                )
            ],
            None,
        ),
        (
            # const declaration with sign ConstExprDef
            "Const a = -1",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(-1),
                )
            ],
            None,
        ),
        (
            # const declaration with multiple sign ConstExprDef
            "Const a = +-1",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(-1),
                )
            ],
            None,
        ),
        (
            # const declaration with sign paren ConstExprDef
            "Const a = -(1)",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(-1),
                )
            ],
            None,
        ),
        (
            # const declaration with multiple sign nested paren ConstExprDef
            "Const a = +(-(1))",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(-1),
                )
            ],
            None,
        ),
        (
            # const declaration with multiple items
            "Const a = 1, b = 2",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(1),
                ),
                ConstListItem(
                    ExtendedID("b"),
                    EvalExpr(2),
                ),
            ],
            None,
        ),
        (
            # public const declaration
            "Public Const a = 1",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(1),
                )
            ],
            AccessModifierType.PUBLIC,
        ),
        (
            # private const declaration
            "Private Const a = 1",
            [
                ConstListItem(
                    ExtendedID("a"),
                    EvalExpr(1),
                )
            ],
            AccessModifierType.PRIVATE,
        ),
    ],
)
def test_parse_const_decl(
    codeblock: str,
    exp_const_list: typing.List[ConstListItem],
    exp_access_mod: typing.Optional[AccessModifierType],
):
    with Tokenizer(f"<%{codeblock}%>", False) as tkzr:
        tkzr.advance_pos()
        if exp_access_mod is not None:
            tkzr.advance_pos()
        const_decl = ConstDecl.from_tokenizer(tkzr, exp_access_mod)
        assert const_decl.const_list == exp_const_list
        assert const_decl.access_mod == exp_access_mod
        tkzr.advance_pos()
