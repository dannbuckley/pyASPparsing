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
            FieldName(FieldID(Token.identifier(10, 16))),
            [],
            AccessModifierType.PRIVATE,
        ),
        (
            # public field declaration
            "Public my_var",
            FieldName(FieldID(Token.identifier(9, 15))),
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with array rank list
            "Public my_var(1)",
            FieldName(FieldID(Token.identifier(9, 15)), [Token.int_literal(16, 17)]),
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with array rank list
            "Public my_var(1, 2)",
            FieldName(
                FieldID(Token.identifier(9, 15)),
                [Token.int_literal(16, 17), Token.int_literal(19, 20)],
            ),
            [],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with other var
            "Public my_var, my_other_var",
            FieldName(FieldID(Token.identifier(9, 15))),
            [VarName(ExtendedID(Token.identifier(17, 29)))],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with multiple other var
            "Public my_var, my_other_var, yet_another",
            FieldName(FieldID(Token.identifier(9, 15))),
            [
                VarName(ExtendedID(Token.identifier(17, 29))),
                VarName(ExtendedID(Token.identifier(31, 42))),
            ],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with other var
            "Public my_var, my_other_var(1)",
            FieldName(FieldID(Token.identifier(9, 15))),
            [
                VarName(
                    ExtendedID(Token.identifier(17, 29)), [Token.int_literal(30, 31)]
                )
            ],
            AccessModifierType.PUBLIC,
        ),
        (
            # public field declaration with other var
            "Public my_var, my_other_var(1, 2)",
            FieldName(FieldID(Token.identifier(9, 15))),
            [
                VarName(
                    ExtendedID(Token.identifier(17, 29)),
                    [Token.int_literal(30, 31), Token.int_literal(33, 34)],
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
        ("Dim my_var", [VarName(ExtendedID(Token.identifier(6, 12)))]),
        (
            "Dim vara, var_b",
            [
                VarName(ExtendedID(Token.identifier(6, 10))),
                VarName(ExtendedID(Token.identifier(12, 17))),
            ],
        ),
        (
            "Dim my_array(3)",
            [VarName(ExtendedID(Token.identifier(6, 14)), [Token.int_literal(15, 16)])],
        ),
        ("Dim my_array()", [VarName(ExtendedID(Token.identifier(6, 14)))]),
        (
            "Dim my_array(3,)",
            [VarName(ExtendedID(Token.identifier(6, 14)), [Token.int_literal(15, 16)])],
        ),
        (
            "Dim my_table(4, 6)",
            [
                VarName(
                    ExtendedID(Token.identifier(6, 14)),
                    [Token.int_literal(15, 16), Token.int_literal(18, 19)],
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
                    ExtendedID(Token.identifier(8, 9)),
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
                    ExtendedID(Token.identifier(8, 9)),
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
                    ExtendedID(Token.identifier(8, 9)),
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
                    ExtendedID(Token.identifier(8, 9)),
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
                    ExtendedID(Token.identifier(8, 9)),
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
                    ExtendedID(Token.identifier(8, 9)),
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
                    ExtendedID(Token.identifier(8, 9)),
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
                    ExtendedID(Token.identifier(8, 9)),
                    EvalExpr(1),
                ),
                ConstListItem(
                    ExtendedID(Token.identifier(15, 16)),
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
                    ExtendedID(Token.identifier(15, 16)),
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
                    ExtendedID(Token.identifier(16, 17)),
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
