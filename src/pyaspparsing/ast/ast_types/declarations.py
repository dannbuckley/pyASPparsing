"""Declaration AST classes"""

import enum
from typing import Optional

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
from .expressions import UnaryExpr, UnarySign
from .optimize import EvalExpr
from .expression_parser import ExpressionParser
from .expression_evaluator import evaluate_expr


@attrs.define(repr=False, slots=False)
class FieldID(FormatterMixin):
    """Defined on grammar line 291

    Attributes
    ----------
    id_code : str
    """

    id_code: str


@attrs.define(repr=False, slots=False)
class FieldName(FormatterMixin):
    """Field name AST type

    Defined on grammar line 288

    Attributes
    ----------
    field_id : FieldID
    array_rank_list : List[Token], default=[]
    """

    field_id: FieldID
    array_rank_list: list[int] = attrs.field(
        default=attrs.Factory(list),
        validator=attrs.validators.deep_iterable(attrs.validators.instance_of(int)),
    )


@attrs.define(repr=False, slots=False)
class VarName(FormatterMixin):
    """Variable name AST type

    Defined on grammar line 300

    &lt;ExtendedID&gt; [ '(' &lt;ArrayRankList&gt; ')']

    Where &lt;ArrayRankList&gt; is defined as (line 306):

    [ &lt;IntLiteral&gt; [ ',' &lt;ArrayRankList&gt; ] ]

    Attributes
    ----------
    extended_id : ExtendedID
    array_rank_list : List[Token], default=[]
    """

    extended_id: ExtendedID
    array_rank_list: list[int] = attrs.field(
        default=attrs.Factory(list),
        validator=attrs.validators.deep_iterable(attrs.validators.instance_of(int)),
    )


@attrs.define(repr=False, slots=False)
class FieldDecl(FormatterMixin, GlobalStmt, MemberDecl):
    """Field declaration AST type

    Defined on grammar line 285

    { 'Private' | 'Public' } &lt;FieldName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;

    Attributes
    ----------
    field_name : FieldName
    other_vars : List[VarName], default=[]
    access_mod : AccessModifierType | None, default=None

    Methods
    -------
    from_tokenizer(tkzr, access_mod)
    """

    field_name: FieldName
    other_vars: list[VarName] = attrs.field(default=attrs.Factory(list))
    access_mod: Optional[AccessModifierType] = attrs.field(default=None, kw_only=True)

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer, access_mod: AccessModifierType):
        """Construct a FieldDecl object from an active Tokenizer

        Parameters
        ----------
        tkzr : Tokenizer
        access_mod : AccessModifierType

        Returns
        -------
        FieldDecl
        """
        assert (
            access_mod != AccessModifierType.PUBLIC_DEFAULT
        ), "'Public Default' access modifier cannot be used with field declaration"
        assert tkzr.try_token_type(
            TokenType.IDENTIFIER
        ), "Expected field name identifier in field declaration"

        field_id = FieldID(tkzr.get_identifier_code())
        tkzr.advance_pos()  # consume identifier

        int_literals: list[int] = []
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
                int_literals.append(int(tkzr.get_token_code()))
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

        other_vars: list[VarName] = []
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
                int_literals: list[int] = []
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
                    int_literals.append(int(tkzr.get_token_code()))
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

        tkzr.assert_newline_or_script_end()
        return FieldDecl(field_name, other_vars, access_mod=access_mod)


@attrs.define(repr=False, slots=False)
class VarDecl(FormatterMixin, MemberDecl, BlockStmt):
    """Variable declaration AST type

    Defined on grammar line 298

    'Dim' &lt;VarName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;

    Attributes
    ----------
    var_name : List[VarName], default=[]

    Methods
    -------
    from_tokenizer(tkzr)
    """

    var_name: list[VarName] = attrs.field(default=attrs.Factory(list))

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """Construct a VarDecl object from an active Tokenizer

        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        VarDecl
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "dim")
        var_name: list[VarName] = []
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
                int_literals: list[Token] = []
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
                    int_literals.append(int(tkzr.get_token_code()))
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

        tkzr.assert_newline_or_script_end()
        return VarDecl(var_name)


@attrs.define(repr=False, slots=False)
class ConstListItem(FormatterMixin):
    """List item within a constant declaration

    Defined on grammar line 312

    Attributes
    ----------
    extended_id : ExtendedID
    const_expr : Expr
    """

    extended_id: ExtendedID
    # similar to a UnaryExpr
    # <ConstExprDef> (line 315) ::=
    #       | '(' <ConstExprDef> ')'
    #       | '-' <ConstExprDef>
    #       | '+' <ConstExprDef>
    #       | <ConstExpr>
    const_expr: EvalExpr


@attrs.define(repr=False, slots=False)
class ConstDecl(FormatterMixin, GlobalStmt, MethodStmt, MemberDecl):
    """Constant declaration AST type

    Defined on grammar line 310

    [ 'Public' | 'Private' ] 'Const' &lt;ConstList&gt; &lt;NEWLINE&gt;

    Attributes
    ----------
    const_list : List[ConstListItem], default=[]
    access_mod : AccessModifierType, default=AccessModifierType.PUBLIC

    Methods
    -------
    from_tokenizer(tkzr, access_mod=None)
    """

    const_list: list[ConstListItem] = attrs.field(default=attrs.Factory(list))
    access_mod: AccessModifierType = attrs.field(
        default=AccessModifierType.PUBLIC, kw_only=True
    )

    @staticmethod
    def from_tokenizer(
        tkzr: Tokenizer, access_mod: Optional[AccessModifierType] = None
    ):
        """Construct a ConstDecl object from an active Tokenizer

        Parameters
        ----------
        tkzr : Tokenizer
        access_mod : AccessModifierType | None, default=None

        Returns
        -------
        ConstDecl
        """
        if access_mod is None:
            access_mod = AccessModifierType.PUBLIC
        tkzr.assert_consume(TokenType.IDENTIFIER, "const")
        const_list: list[ConstListItem] = []
        while not tkzr.try_multiple_token_type(
            [TokenType.NEWLINE, TokenType.DELIM_END]
        ):
            const_id = ExtendedID.from_tokenizer(tkzr)
            tkzr.assert_consume(TokenType.SYMBOL, "=")
            const_expr: Optional[Expr] = None
            num_paren: int = 0
            # signs expand to the right, use a stack
            sign_stack: list[Token] = []
            while not (
                tkzr.try_multiple_token_type([TokenType.NEWLINE, TokenType.DELIM_END])
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
                next_sign = sign_stack.pop()
                const_expr = UnaryExpr(
                    (
                        UnarySign.SIGN_POS
                        if tkzr.get_token_code(tok=next_sign) == "+"
                        else UnarySign.SIGN_NEG
                    ),
                    const_expr,
                )
            const_list.append(ConstListItem(const_id, evaluate_expr(const_expr)))
            del const_id, const_expr, num_paren, sign_stack

            # advance to next item
            tkzr.try_consume(TokenType.SYMBOL, ",")
        tkzr.assert_newline_or_script_end()
        return ConstDecl(const_list, access_mod=access_mod)


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class ArgModifierType(enum.Enum):
    """Enumeration of valid argument modifier types"""

    ARG_REFERENCE = enum.auto()
    ARG_VALUE = enum.auto()


@attrs.define(repr=False, slots=False)
class Arg(FormatterMixin):
    """Argument AST type

    Defined on grammar line 340

    Attributes
    ----------
    extended_id : ExtendedID
    arg_modifier : ArgModifierType, default=ArgModifierType.ARG_VALUE
        If no modifier is specified, ByVal is the default
    has_paren : bool, default=False
    """

    extended_id: ExtendedID
    arg_modifier: ArgModifierType = attrs.field(
        default=ArgModifierType.ARG_VALUE, kw_only=True
    )
    has_paren: bool = attrs.field(default=False, kw_only=True)

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        Arg
        """
        mod_types: dict[str, ArgModifierType] = {
            "byref": ArgModifierType.ARG_REFERENCE,
            "byval": ArgModifierType.ARG_VALUE,
        }
        arg_modifier = None
        if (
            tkzr.try_token_type(TokenType.IDENTIFIER)
            and (arg_modifier := mod_types.get(tkzr.get_token_code(), None)) is not None
        ):
            tkzr.advance_pos()  # consume modifier
        else:
            arg_modifier = ArgModifierType.ARG_VALUE
        arg_id = ExtendedID.from_tokenizer(tkzr)
        has_paren = tkzr.try_consume(TokenType.SYMBOL, "(")
        if has_paren:
            tkzr.assert_consume(TokenType.SYMBOL, ")")
        return Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)


@attrs.define(repr=False, slots=False)
class SubDecl(FormatterMixin, GlobalStmt, MemberDecl):
    """Sub-procedure declaration AST type

    Defined on grammar line 320

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Sub' &lt;ExtendedID&gt; &lt;MethodArgList&gt; &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Sub' &lt;NEWLINE&gt;

    Attributes
    ----------
    extended_id : ExtendedID
    method_arg_list : List[Arg], default=[]
    method_stmt_list : List[MethodStmt], default=[]
    access_mod : AccessModifierType | None, default=None
    """

    extended_id: ExtendedID
    method_arg_list: list[Arg] = attrs.field(default=attrs.Factory(list))
    method_stmt_list: list[MethodStmt] = attrs.field(default=attrs.Factory(list))
    access_mod: Optional[AccessModifierType] = attrs.field(default=None, kw_only=True)


@attrs.define(repr=False, slots=False)
class FunctionDecl(FormatterMixin, GlobalStmt, MemberDecl):
    """Function declaration AST type

    Defined on grammar line 323

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Function' &lt;ExtendedID&gt; &lt;MethodArgList&gt; &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Function' &lt;NEWLINE&gt;

    Attributes
    ----------
    extended_id : ExtendedID
    method_arg_list : List[Arg], default=[]
    method_stmt_list : List[MethodStmt], default=[]
    access_mod : AccessModifierType | None, default=None
    """

    extended_id: ExtendedID
    method_arg_list: list[Arg] = attrs.field(default=attrs.Factory(list))
    method_stmt_list: list[MethodStmt] = attrs.field(default=attrs.Factory(list))
    access_mod: Optional[AccessModifierType] = attrs.field(default=None, kw_only=True)


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class PropertyAccessType(enum.Enum):
    """Enumeration of valid property access types"""

    PROPERTY_GET = enum.auto()
    PROPERTY_LET = enum.auto()
    PROPERTY_SET = enum.auto()


@attrs.define(repr=False, slots=False)
class PropertyDecl(FormatterMixin, MemberDecl):
    """Property declaration AST type

    Defined on grammar line 347

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Property' &lt;PropertyAccessType&gt; &lt;ExtendedID&gt; &lt;MethodArgList&gt;
    &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Property' &lt;NEWLINE&gt;

    Attributes
    ----------
    prop_access_type : PropertyAccessType
    extended_id : ExtendedID
    method_arg_list : List[Arg], default=[]
    method_stmt_list : List[MethodStmt], default=[]
    access_mod : AccessModifierType | None, default=None
    """

    prop_access_type: PropertyAccessType
    extended_id: ExtendedID
    method_arg_list: list[Arg] = attrs.field(default=attrs.Factory(list))
    method_stmt_list: list[MethodStmt] = attrs.field(default=attrs.Factory(list))
    access_mod: Optional[AccessModifierType] = attrs.field(default=None, kw_only=True)


@attrs.define(repr=False, slots=False)
class ClassDecl(FormatterMixin, GlobalStmt):
    """Class declaration AST type

    Defined on grammar line 273

    'Class' &lt;ExtendedID&gt; &lt;NEWLINE&gt; <br />
    &lt;MemberDeclList&gt; 'End' 'Class' &lt;NEWLINE&gt;

    Attributes
    ----------
    extended_id : ExtendedID
    member_decl_list : List[MemberDecl], default=[]
    """

    extended_id: ExtendedID
    member_decl_list: list[MemberDecl] = attrs.field(default=attrs.Factory(list))
