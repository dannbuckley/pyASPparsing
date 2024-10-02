"""ast_types module"""

import enum
import typing
import attrs
from .tokenizer import Token


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class AccessModifierType(enum.Enum):
    """Enumeration of valid access modifiers"""

    PRIVATE = 0
    PUBLIC = 1
    # using an enum because PUBLIC DEFAULT is two tokens
    PUBLIC_DEFAULT = 2


@attrs.define(slots=False)
class Expr:
    """Defined on grammar line 664

    &lt;ImpExpr&gt;
    """


@attrs.define(slots=False)
class ImpExpr(Expr):
    """Defined on grammar line 666

    [ &lt;ImpExpr&gt; 'Imp' ] &lt;EqvExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class EqvExpr(Expr):
    """Defined on grammar line 669

    [ &lt;EqvExpr&gt; 'Eqv' ] &lt;XorExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class XorExpr(Expr):
    """Defined on grammar line 672

    [ &lt;XorExpr&gt; 'Xor' ] &lt;OrExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class OrExpr(Expr):
    """Defined on grammar line 675

    [ &lt;OrExpr&gt; 'Or' ] &lt;AndExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class AndExpr(Expr):
    """Defined on grammar line 678

    [ &lt;AndExpr&gt; 'And' ] &lt;NotExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class NotExpr(Expr):
    """Defined on grammar line 681

    { 'Not' &lt;NotExpr&gt; | &lt;CompareExpr&gt; }
    """

    term: Expr


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class CompareExprType(enum.Enum):
    """Enumeration of valid operators that can appear
    in a comparison expresssion (CompareExpr)"""

    COMPARE_IS = 0
    COMPARE_ISNOT = 1
    COMPARE_GTEQ = 2
    COMPARE_EQGT = 3
    COMPARE_LTEQ = 4
    COMPARE_EQLT = 5
    COMPARE_GT = 6
    COMPARE_LT = 7
    COMPARE_LTGT = 8
    COMPARE_EQ = 9


@attrs.define(slots=False)
class CompareExpr(Expr):
    """Defined on grammar line 684

    [
        &lt;CompareExpr&gt;
        { 'Is' [ 'Not' ] | '>=' | '=>' | '<=' | '=<' | '>' | '<' | '<>' | '=' }
    ] &lt;ConcatExpr&gt;
    """

    cmp_type: CompareExprType
    left: Expr
    right: Expr


@attrs.define(slots=False)
class ConcatExpr(Expr):
    """Defined on grammar line 696

    [ &lt;ConcatExpr&gt; '&' ] &lt;AddExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class AddExpr(Expr):
    """Defined on grammar line 699

    [ &lt;AddExpr&gt; { '+' | '-' } ] &lt;ModExpr&gt;
    """

    op: Token
    left: Expr
    right: Expr


@attrs.define(slots=False)
class ModExpr(Expr):
    """Defined on grammar line 703

    [ &lt;ModExpr&gt; 'Mod' ] &lt;IntDivExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class IntDivExpr(Expr):
    """Defined on grammar line 706

    [ &lt;IntDivExpr&gt; '\\\\' ] &lt;MultExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class MultExpr(Expr):
    """Defined on grammar line 709

    [ &lt;MultExpr&gt; { '*' | '/' } ] &lt;UnaryExpr&gt;
    """

    op: Token
    left: Expr
    right: Expr


@attrs.define(slots=False)
class UnaryExpr(Expr):
    """Defined on grammar line 713

    { { '-' | '+' } &lt;UnaryExpr&gt; | &lt;ExpExpr&gt; }
    """

    sign: Token
    term: Expr


@attrs.define(slots=False)
class ExpExpr(Expr):
    """Defined on grammar line 717

    &lt;Value&gt; [ '^' &lt;ExpExpr&gt; ]
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class Value(Expr):
    """Defined on grammar line 720

    &lt;ConstExpr&gt; | &lt;LeftExpr&gt; | { '(' &lt;Expr&gt; ')' }
    """


@attrs.define(slots=False)
class ConstExpr(Value):
    """Defined on grammar line 724"""

    const_token: Token


@attrs.define(slots=False)
class BoolLiteral(ConstExpr):
    """Defined on grammar line 731

    'True' | 'False'
    """


@attrs.define(slots=False)
class IntLiteral(ConstExpr):
    """Defined on grammar line 734

    LITERAL_INT | LITERAL_HEX | LITERAL_OCT
    """


@attrs.define(slots=False)
class Nothing(ConstExpr):
    """Defined on grammar line 738

    'Nothing' | 'Null' | 'Empty'
    """


@attrs.define(slots=False)
class ExtendedID:
    """Defined on grammar line 513"""

    id_token: Token


@attrs.define(slots=False)
class QualifiedID:
    """Defined on grammar line 443"""

    id_tokens: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class IndexOrParams:
    """Defined of grammar line 519"""

    expr_list: typing.List[typing.Optional[Expr]] = attrs.field(
        default=attrs.Factory(list)
    )
    dot: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class LeftExprTail:
    """Defined on grammar line 436"""

    qual_id_tail: QualifiedID
    index_or_params: typing.List[IndexOrParams] = attrs.field(
        default=attrs.Factory(list)
    )


@attrs.define(slots=False)
class LeftExpr(Value):
    """Defined on grammar line 430"""

    qual_id: QualifiedID
    index_or_params: typing.List[IndexOrParams] = attrs.field(
        default=attrs.Factory(list)
    )
    tail: typing.List[LeftExprTail] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class GlobalStmt:
    """Defined on grammar line 357

    Could be one of:
    - OptionExplicit
    - ClassDecl
    - FieldDecl
    - ConstDecl
    - SubDecl
    - FunctionDecl
    - BlockStmt
    """


@attrs.define(slots=False)
class OptionExplicit(GlobalStmt):
    """Defined on grammar line 393

    'Option' 'Explicit' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class MethodStmt:
    """Defined on grammar line 365

    &lt;ConstDecl&gt; | &lt;BlockStmt&gt;
    """


@attrs.define(slots=False)
class BlockStmt(GlobalStmt, MethodStmt):
    """Defined on grammar line 368

    If InlineStmt, must be:
    &lt;InlineStmt&gt; &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class RedimStmt(BlockStmt):
    """Defined on grammar line 539

    'Redim' [ 'Preserve' ] &lt;RedimDeclList&gt; &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class IfStmt(BlockStmt):
    """Defined on grammar line 549

    Two possible definitions:

    'If' &lt;Expr&gt; 'Then' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; &lt;ElseStmtList&gt; 'End' 'If' &lt;NEWLINE&gt;

    'If' &lt;Expr&gt; 'Then' &lt;InlineStmt&gt; <br />
    [ 'Else' &lt;InlineStmt&gt; ] [ 'End' 'If' ] &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class WithStmt(BlockStmt):
    """Defined on grammar line 566

    'With' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'End' 'With' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class SelectStmt(BlockStmt):
    """Defined on grammar line 588

    'Select' 'Case' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;CaseStmtList&gt; 'End' 'Select' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class LoopStmt(BlockStmt):
    """Defined on grammar line 570

    Several possible definitions:

    'Do' { 'While' | 'Until' } &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' &lt;NEWLINE&gt;

    'Do' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' { 'While' | 'Until' } &lt;Expr&gt; &lt;NEWLINE&gt;

    'Do' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' &lt;NEWLINE&gt;

    'While' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'WEnd' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class ForStmt(BlockStmt):
    """Defined on grammar line 580

    Two possible definitions:

    'For' &lt'ExtendedID&gt; '=' &lt;Expr&gt; 'To' &lt;Expr&gt;
    [ 'Step' &lt;Expr&gt; ] &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;

    'For 'Each' &lt;ExtendedID&gt; 'In' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class InlineStmt(BlockStmt):
    """Defined on grammar line 377"""


@attrs.define(slots=False)
class AssignStmt(InlineStmt):
    """Defined on grammar line 404

    Two possible definitions:

    &lt;LeftExpr&gt; '=' &lt;Expr&gt;

    'Set' &lt;LeftExpr&gt; '=' { &lt;Expr&gt; | 'New' &lt;LeftExpr&gt; }
    """

    # left side of '='
    target_expr: Expr
    # right side of '='
    assign_expr: Expr
    is_new: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class CallStmt(InlineStmt):
    """Defined on grammar line 428

    'Call' &lt;LeftExpr&gt;
    """

    left_expr: LeftExpr


@attrs.define(slots=False)
class SubCallStmt(InlineStmt):
    """Defined on grammar line 414"""


@attrs.define(slots=False)
class ErrorStmt(InlineStmt):
    """Defined on grammar line 395

    'On' 'Error' { 'Resume' 'Next' | 'GoTo' IntLiteral }

    If 'GoTo' specified, IntLiteral must be 0
    """

    resume_next: bool = attrs.field(default=False, kw_only=True)
    goto_spec: typing.Optional[Token] = attrs.field(default=None, kw_only=True)


@attrs.define(slots=False)
class ExitStmt(InlineStmt):
    """Defined on grammar line 398

    'Exit' { 'Do' | 'For' | 'Function' | 'Property' | 'Sub' }
    """

    exit_token: Token


@attrs.define(slots=False)
class EraseStmt(InlineStmt):
    """Part of InlineStmt definition on line 382

    'Erase' &lt;ExtendedID&gt;
    """

    extended_id: ExtendedID


@attrs.define(slots=False)
class MemberDecl:
    """Defined on grammar line 278"""


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


@attrs.define
class Program:
    """The starting symbol for the VBScript grammar.
    Defined on grammar line 267

    Attributes
    ----------
    global_stmt_list : List[GlobalStmt], default=[]
    """

    global_stmt_list: typing.List[GlobalStmt] = attrs.field(default=attrs.Factory(list))
