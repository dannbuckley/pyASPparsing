"""Expression AST classes"""

import typing

import attrs

from ..tokenizer.token_types import Token
from .base import Expr, Value, CompareExprType

__all__ = [
    "ImpExpr",
    "EqvExpr",
    "XorExpr",
    "OrExpr",
    "AndExpr",
    "NotExpr",
    "CompareExpr",
    "ConcatExpr",
    "AddExpr",
    "ModExpr",
    "IntDivExpr",
    "MultExpr",
    "UnaryExpr",
    "ExpExpr",
    "ConstExpr",
    "BoolLiteral",
    "IntLiteral",
    "Nothing",
    "QualifiedID",
    "IndexOrParams",
    "LeftExprTail",
    "LeftExpr",
]


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
