"""Declaration AST classess"""

import typing

import attrs

from ..tokenizer.token_types import Token
from .base import (
    AccessModifierType,
    BlockStmt,
    Expr,
    GlobalStmt,
    MethodStmt,
    ExtendedID,
    MemberDecl,
)

__all__ = [
    "ClassDecl",
    "FieldID",
    "FieldName",
    "VarName",
    "FieldDecl",
    "VarDecl",
    "ConstListItem",
    "ConstDecl",
    "Arg",
    "SubDecl",
    "FunctionDecl",
    "PropertyDecl",
]


@attrs.define(slots=False)
class ClassDecl(GlobalStmt):
    """Defined on grammar line 273

    'Class' &lt;ExtendedID&gt; &lt;NEWLINE&gt; <br />
    &lt;MemberDeclList&gt; 'End' 'Class' &lt;NEWLINE&gt;

    Attributes
    ----------
    extended_id : ExtendedID
    member_decl_list : List[MemberDecl], default=[]
    """

    extended_id: ExtendedID
    member_decl_list: typing.List[MemberDecl] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class FieldID:
    """Defined on grammar line 291"""

    id_token: Token


@attrs.define(slots=False)
class FieldName:
    """Defined on grammar line 288"""

    field_id: FieldID
    array_rank_list: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class VarName:
    """Defined on grammar line 300

    &lt;ExtendedID&gt; [ '(' &lt;ArrayRankList&gt; ')']

    Where &lt;ArrayRankList&gt; is defined as (line 306):

    [ &lt;IntLiteral&gt; [ ',' &lt;ArrayRankList&gt; ] ]
    """

    extended_id: ExtendedID
    array_rank_list: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class FieldDecl(GlobalStmt, MemberDecl):
    """Defined on grammar line 285

    { 'Private' | 'Public' } &lt;FieldName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;
    """

    field_name: FieldName
    other_vars: typing.List[VarName] = attrs.field(default=attrs.Factory(list))
    access_mod: typing.Optional[AccessModifierType] = attrs.field(
        default=None, kw_only=True
    )


@attrs.define(slots=False)
class VarDecl(MemberDecl, BlockStmt):
    """Defined on grammar line 298

    'Dim' &lt;VarName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;
    """

    var_name: typing.List[VarName] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class ConstListItem:
    """Defined on grammar line 312"""

    extended_id: ExtendedID
    # similar to a UnaryExpr
    # <ConstExprDef> (line 315) ::=
    #       | '(' <ConstExprDef> ')'
    #       | '-' <ConstExprDef>
    #       | '+' <ConstExprDef>
    #       | <ConstExpr>
    const_expr: Expr


@attrs.define(slots=False)
class ConstDecl(GlobalStmt, MethodStmt, MemberDecl):
    """Defined on grammar line 310

    [ 'Public' | 'Private' ] 'Const' &lt;ConstList&gt; &lt;NEWLINE&gt;
    """

    const_list: typing.List[ConstListItem] = attrs.field(default=attrs.Factory(list))
    access_mod: typing.Optional[AccessModifierType] = attrs.field(
        default=None, kw_only=True
    )


@attrs.define(slots=False)
class Arg:
    """Defined on grammar line 340"""

    extended_id: ExtendedID
    arg_modifier: typing.Optional[Token] = attrs.field(default=None, kw_only=True)
    has_paren: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class SubDecl(GlobalStmt, MemberDecl):
    """Defined on grammar line 320

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Sub' &lt;ExtendedID&gt; &lt;MethodArgList&gt; &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Sub' &lt;NEWLINE&gt;
    """

    extended_id: ExtendedID
    method_arg_list: typing.List[Arg] = attrs.field(default=attrs.Factory(list))
    method_stmt_list: typing.List[MethodStmt] = attrs.field(default=attrs.Factory(list))
    access_mod: typing.Optional[AccessModifierType] = attrs.field(
        default=None, kw_only=True
    )


@attrs.define(slots=False)
class FunctionDecl(GlobalStmt, MemberDecl):
    """Defined on grammar line 323

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Function' &lt;ExtendedID&gt; &lt;MethodArgList&gt; &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Function' &lt;NEWLINE&gt;
    """

    extended_id: ExtendedID
    method_arg_list: typing.List[Arg] = attrs.field(default=attrs.Factory(list))
    method_stmt_list: typing.List[MethodStmt] = attrs.field(default=attrs.Factory(list))
    access_mod: typing.Optional[AccessModifierType] = attrs.field(
        default=None, kw_only=True
    )


@attrs.define(slots=False)
class PropertyDecl(MemberDecl):
    """Defined on grammar line 347

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Property' &lt;PropertyAccessType&gt; &lt;ExtendedID&gt; &lt;MethodArgList&gt;
    &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Property' &lt;NEWLINE&gt;
    """

    prop_access_type: Token
    extended_id: ExtendedID
    method_arg_list: typing.List[Arg] = attrs.field(default=attrs.Factory(list))
    method_stmt_list: typing.List[MethodStmt] = attrs.field(default=attrs.Factory(list))
    access_mod: typing.Optional[AccessModifierType] = attrs.field(
        default=None, kw_only=True
    )
