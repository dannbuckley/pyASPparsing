"""Declaration AST classes"""

import typing

import attrs

from ... import ParserError
from ..tokenizer.token_types import Token, TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import (
    FormatterMixin,
    AccessModifierType,
    BlockStmt,
    Expr,
    GlobalStmt,
    MethodStmt,
    MemberDecl,
)
from .statements import ExtendedID
from .expressions import UnaryExpr
from .parse_expressions import ExpressionParser

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


@attrs.define(repr=False, slots=False)
class FieldID(FormatterMixin):
    """Defined on grammar line 291"""

    id_token: Token


@attrs.define(repr=False, slots=False)
class FieldName(FormatterMixin):
    """Defined on grammar line 288"""

    field_id: FieldID
    array_rank_list: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class VarName(FormatterMixin):
    """Defined on grammar line 300

    &lt;ExtendedID&gt; [ '(' &lt;ArrayRankList&gt; ')']

    Where &lt;ArrayRankList&gt; is defined as (line 306):

    [ &lt;IntLiteral&gt; [ ',' &lt;ArrayRankList&gt; ] ]
    """

    extended_id: ExtendedID
    array_rank_list: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class FieldDecl(FormatterMixin, GlobalStmt, MemberDecl):
    """Defined on grammar line 285

    { 'Private' | 'Public' } &lt;FieldName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;
    """

    field_name: FieldName
    other_vars: typing.List[VarName] = attrs.field(default=attrs.Factory(list))
    access_mod: typing.Optional[AccessModifierType] = attrs.field(
        default=None, kw_only=True
    )

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer, access_mod: AccessModifierType):
        assert (
            access_mod != AccessModifierType.PUBLIC_DEFAULT
        ), "'Public Default' access modifier cannot be used with field declaration"
        assert tkzr.try_token_type(
            TokenType.IDENTIFIER
        ), "Expected field name identifier in field declaration"

        field_id: FieldID = FieldID(tkzr.current_token)
        tkzr.advance_pos()  # consume identifier

        int_literals: typing.List[Token] = []
        if tkzr.try_consume(TokenType.SYMBOL, "("):
            find_int_literal = tkzr.try_multiple_token_type(
                [
                    TokenType.LITERAL_INT,
                    TokenType.LITERAL_HEX,
                    TokenType.LITERAL_OCT,
                ]
            )
            while find_int_literal:
                if not tkzr.try_multiple_token_type(
                    [
                        TokenType.LITERAL_INT,
                        TokenType.LITERAL_HEX,
                        TokenType.LITERAL_OCT,
                    ]
                ):
                    raise ParserError(
                        "Invalid token type found in array rank list "
                        "of field name declaration"
                    )
                int_literals.append(tkzr.current_token)
                tkzr.advance_pos()  # consume int literal

                tkzr.try_consume(TokenType.SYMBOL, ",")

                # last int literal is optional, check for ending ')'
                if (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and tkzr.get_token_code() == ")"
                ):
                    find_int_literal = False
            # should have an ending ')'
            tkzr.assert_consume(TokenType.SYMBOL, ")")
            del find_int_literal
        field_name: FieldName = FieldName(field_id, int_literals)
        del int_literals

        # prepare for other vars
        tkzr.try_consume(TokenType.SYMBOL, ",")

        other_vars: typing.List[VarName] = []
        parse_var_name = tkzr.try_token_type(TokenType.IDENTIFIER)
        while parse_var_name:
            var_id = ExtendedID.from_tokenizer(tkzr)
            if tkzr.try_consume(TokenType.SYMBOL, "("):
                find_int_literal = tkzr.try_multiple_token_type(
                    [
                        TokenType.LITERAL_INT,
                        TokenType.LITERAL_HEX,
                        TokenType.LITERAL_OCT,
                    ]
                )
                int_literals: typing.List[Token] = []
                while find_int_literal:
                    if not tkzr.try_multiple_token_type(
                        [
                            TokenType.LITERAL_INT,
                            TokenType.LITERAL_HEX,
                            TokenType.LITERAL_OCT,
                        ]
                    ):
                        raise ParserError(
                            "Invalid token type found in array rank list "
                            "of variable name declaration (part of field declaration)"
                        )
                    int_literals.append(tkzr.current_token)
                    tkzr.advance_pos()  # consume int literal

                    tkzr.try_consume(TokenType.SYMBOL, ",")

                    # last int literal is optional, check for ending ')'
                    if (
                        tkzr.try_token_type(TokenType.SYMBOL)
                        and tkzr.get_token_code() == ")"
                    ):
                        find_int_literal = False
                # should have and ending ')'
                tkzr.assert_consume(TokenType.SYMBOL, ")")
                other_vars.append(VarName(var_id, int_literals))
                del find_int_literal, int_literals
            else:
                other_vars.append(VarName(var_id))

            # another variable name?
            if not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ","
            ):
                parse_var_name = False
            else:
                tkzr.advance_pos()  # consume ','

        tkzr.assert_consume(TokenType.NEWLINE)
        return FieldDecl(field_name, other_vars, access_mod=access_mod)


@attrs.define(repr=False, slots=False)
class VarDecl(FormatterMixin, MemberDecl, BlockStmt):
    """Defined on grammar line 298

    'Dim' &lt;VarName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;
    """

    var_name: typing.List[VarName] = attrs.field(default=attrs.Factory(list))

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        tkzr.assert_consume(TokenType.IDENTIFIER, "dim")
        var_name: typing.List[VarName] = []
        parse_var_name = True
        while parse_var_name:
            var_id = ExtendedID.from_tokenizer(tkzr)
            if tkzr.try_consume(TokenType.SYMBOL, "("):
                # parse array rank list
                # first int literal is also optional
                find_int_literal = tkzr.try_multiple_token_type(
                    [
                        TokenType.LITERAL_INT,
                        TokenType.LITERAL_HEX,
                        TokenType.LITERAL_OCT,
                    ]
                )
                int_literals: typing.List[Token] = []
                while find_int_literal:
                    if not tkzr.try_multiple_token_type(
                        [
                            TokenType.LITERAL_INT,
                            TokenType.LITERAL_HEX,
                            TokenType.LITERAL_OCT,
                        ]
                    ):
                        raise ParserError(
                            "Invalid token type found in array rank list "
                            "of variable name declaration"
                        )
                    int_literals.append(tkzr.current_token)
                    tkzr.advance_pos()  # consume int literal

                    tkzr.try_consume(TokenType.SYMBOL, ",")

                    # last int literal is optional, check for ending ')'
                    if (
                        tkzr.try_token_type(TokenType.SYMBOL)
                        and tkzr.get_token_code() == ")"
                    ):
                        find_int_literal = False
                # should have an ending ')'
                tkzr.assert_consume(TokenType.SYMBOL, ")")
                var_name.append(VarName(var_id, int_literals))
                del find_int_literal, int_literals
            else:
                var_name.append(VarName(var_id))

            # another variable name?
            if not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ","
            ):
                parse_var_name = False
            else:
                tkzr.advance_pos()  # consume ','

        tkzr.assert_consume(TokenType.NEWLINE)
        return VarDecl(var_name)


@attrs.define(repr=False, slots=False)
class ConstListItem(FormatterMixin):
    """Defined on grammar line 312"""

    extended_id: ExtendedID
    # similar to a UnaryExpr
    # <ConstExprDef> (line 315) ::=
    #       | '(' <ConstExprDef> ')'
    #       | '-' <ConstExprDef>
    #       | '+' <ConstExprDef>
    #       | <ConstExpr>
    const_expr: Expr


@attrs.define(repr=False, slots=False)
class ConstDecl(FormatterMixin, GlobalStmt, MethodStmt, MemberDecl):
    """Defined on grammar line 310

    [ 'Public' | 'Private' ] 'Const' &lt;ConstList&gt; &lt;NEWLINE&gt;
    """

    const_list: typing.List[ConstListItem] = attrs.field(default=attrs.Factory(list))
    access_mod: typing.Optional[AccessModifierType] = attrs.field(
        default=None, kw_only=True
    )

    @staticmethod
    def from_tokenizer(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ):
        tkzr.assert_consume(TokenType.IDENTIFIER, "const")
        const_list: typing.List[ConstListItem] = []
        while not tkzr.try_token_type(TokenType.NEWLINE):
            const_id = ExtendedID.from_tokenizer(tkzr)
            tkzr.assert_consume(TokenType.SYMBOL, "=")
            const_expr: typing.Optional[Expr] = None
            num_paren: int = 0
            # signs expand to the right, use a stack
            sign_stack: typing.List[Token] = []
            while not (
                tkzr.try_token_type(TokenType.NEWLINE)
                or (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and (tkzr.get_token_code() == ",")
                )
            ):
                if tkzr.try_consume(TokenType.SYMBOL, "("):
                    num_paren += 1
                elif (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and tkzr.get_token_code() in "-+"
                ):
                    sign_stack.append(tkzr.current_token)
                    tkzr.advance_pos()  # consume
                elif (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and tkzr.get_token_code() in ")"
                ):
                    assert (
                        const_expr is not None
                    ), "Expected const expression before ')' in const list item"
                    break
                else:
                    assert (
                        const_expr is None
                    ), "Can only have one const expression per const list item"
                    const_expr = ExpressionParser.parse_const_expr(tkzr)
            assert (
                const_expr is not None
            ), "Expected const expression in const list item"

            # verify correct number of closing parentheses
            while num_paren > 0:
                tkzr.assert_consume(TokenType.SYMBOL, ")")
                num_paren -= 1

            # combine signs into one expression
            while len(sign_stack) > 0:
                const_expr = UnaryExpr(sign_stack.pop(), const_expr)
            const_list.append(ConstListItem(const_id, const_expr))
            del const_id, const_expr, num_paren, sign_stack

            # advance to next item
            tkzr.try_consume(TokenType.SYMBOL, ",")
        tkzr.assert_consume(TokenType.NEWLINE)
        return ConstDecl(const_list, access_mod=access_mod)


@attrs.define(repr=False, slots=False)
class Arg(FormatterMixin):
    """Defined on grammar line 340"""

    extended_id: ExtendedID
    arg_modifier: typing.Optional[Token] = attrs.field(default=None, kw_only=True)
    has_paren: bool = attrs.field(default=False, kw_only=True)


@attrs.define(repr=False, slots=False)
class SubDecl(FormatterMixin, GlobalStmt, MemberDecl):
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


@attrs.define(repr=False, slots=False)
class FunctionDecl(FormatterMixin, GlobalStmt, MemberDecl):
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


@attrs.define(repr=False, slots=False)
class PropertyDecl(FormatterMixin, MemberDecl):
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


@attrs.define(repr=False, slots=False)
class ClassDecl(FormatterMixin, GlobalStmt):
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
