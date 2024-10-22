"""Expression AST classes"""

import enum
import typing

import attrs

from ..tokenizer.token_types import Token
from .base import FormatterMixin, Expr, Value, CompareExprType


@attrs.define(repr=False, slots=False)
class ImpExpr(FormatterMixin, Expr):
    """Implication expression AST type

    Defined on grammar line 666

    [ &lt;ImpExpr&gt; 'Imp' ] &lt;EqvExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class EqvExpr(FormatterMixin, Expr):
    """Equivalence expression AST type

    Defined on grammar line 669

    [ &lt;EqvExpr&gt; 'Eqv' ] &lt;XorExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class XorExpr(FormatterMixin, Expr):
    """Exclusive disjunction expression AST type

    Defined on grammar line 672

    [ &lt;XorExpr&gt; 'Xor' ] &lt;OrExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class OrExpr(FormatterMixin, Expr):
    """Inclusive disjunction expression AST type

    Defined on grammar line 675

    [ &lt;OrExpr&gt; 'Or' ] &lt;AndExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class AndExpr(FormatterMixin, Expr):
    """Conjunction expression AST type

    Defined on grammar line 678

    [ &lt;AndExpr&gt; 'And' ] &lt;NotExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class NotExpr(FormatterMixin, Expr):
    """Complement expression AST type

    Defined on grammar line 681

    { 'Not' &lt;NotExpr&gt; | &lt;CompareExpr&gt; }

    Attributes
    ----------
    term : Expr
    """

    term: Expr


@attrs.define(repr=False, slots=False)
class CompareExpr(FormatterMixin, Expr):
    """Comparison expression AST type

    Defined on grammar line 684

    [
        &lt;CompareExpr&gt;
        { 'Is' [ 'Not' ] | '>=' | '=>' | '<=' | '=<' | '>' | '<' | '<>' | '=' }
    ] &lt;ConcatExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    cmp_type : CompareExprType
    """

    left: Expr
    right: Expr
    cmp_type: CompareExprType


@attrs.define(repr=False, slots=False)
class ConcatExpr(FormatterMixin, Expr):
    """String concatenation expression AST type

    Defined on grammar line 696

    [ &lt;ConcatExpr&gt; '&' ] &lt;AddExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class AddExpr(FormatterMixin, Expr):
    """Addition/subtraction expression AST type

    Defined on grammar line 699

    [ &lt;AddExpr&gt; { '+' | '-' } ] &lt;ModExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class ModExpr(FormatterMixin, Expr):
    """Modulo expression AST type

    Defined on grammar line 703

    [ &lt;ModExpr&gt; 'Mod' ] &lt;IntDivExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class IntDivExpr(FormatterMixin, Expr):
    """Integer division expression AST type

    Defined on grammar line 706

    [ &lt;IntDivExpr&gt; '&#92;' ] &lt;MultExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class MultExpr(FormatterMixin, Expr):
    """Multiplication/division expression AST type

    Defined on grammar line 709

    [ &lt;MultExpr&gt; { '*' | '/' } ] &lt;UnaryExpr&gt;

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class UnarySign(enum.IntEnum):
    """Enumeration of valid signs for unary expression"""

    SIGN_POS = enum.auto()
    SIGN_NEG = enum.auto()


@attrs.define(repr=False, slots=False)
class UnaryExpr(FormatterMixin, Expr):
    """Unary signed expression AST type

    Defined on grammar line 713

    { { '-' | '+' } &lt;UnaryExpr&gt; | &lt;ExpExpr&gt; }

    Attributes
    ----------
    sign : UnarySign
    term : Expr
    """

    sign: UnarySign
    term: Expr


@attrs.define(repr=False, slots=False)
class ExpExpr(FormatterMixin, Expr):
    """Exponentiation expression AST type

    Defined on grammar line 717

    &lt;Value&gt; [ '^' &lt;ExpExpr&gt; ]

    Attributes
    ----------
    left : Expr
    right : Expr
    """

    left: Expr
    right: Expr


@attrs.define(repr=False, slots=False)
class ConstExpr(FormatterMixin, Value):
    """Constant expression AST type

    Defined on grammar line 724

    Attributes
    ----------
    const_token : Token
    """

    const_token: Token


# repr=False -> repr is inherited from ConstExpr (FormatterMixin.__repr__)
@attrs.define(repr=False, slots=False)
class BoolLiteral(ConstExpr):
    """Boolean literal constant expression AST type

    Defined on grammar line 731

    'True' | 'False'
    """


# repr=False -> repr is inherited from ConstExpr (FormatterMixin.__repr__)
@attrs.define(repr=False, slots=False)
class IntLiteral(ConstExpr):
    """Integer literal constant expression AST type

    Defined on grammar line 734

    LITERAL_INT | LITERAL_HEX | LITERAL_OCT
    """


# repr=False -> repr is inherited from ConstExpr (FormatterMixin.__repr__)
@attrs.define(repr=False, slots=False)
class Nothing(ConstExpr):
    """Nothing constant expression AST type

    Defined on grammar line 738

    'Nothing' | 'Null' | 'Empty'
    """


@attrs.define(repr=False, slots=False)
class QualifiedID(FormatterMixin):
    """Qualified identifier AST type

    Defined on grammar line 443

    Attributes
    ----------
    id_tokens : List[Token], default=[]
    """

    id_tokens: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class IndexOrParams(FormatterMixin):
    """Defined of grammar line 519

    Attributes
    ----------
    expr_list : List[Expr | None], default=[]
    dot : bool, default=False
    """

    expr_list: typing.List[typing.Optional[Expr]] = attrs.field(
        default=attrs.Factory(list)
    )
    dot: bool = attrs.field(default=False, kw_only=True)


@attrs.define(repr=False, slots=False)
class LeftExprTail(FormatterMixin):
    """Defined on grammar line 436

    Attributes
    ----------
    qual_id_tail : QualifiedID
    index_or_params : List[IndexOrParams], default=[]
    """

    qual_id_tail: QualifiedID
    index_or_params: typing.List[IndexOrParams] = attrs.field(
        default=attrs.Factory(list)
    )


@attrs.define(repr=False, slots=False)
class LeftExpr(FormatterMixin, Value):
    """Defined on grammar line 430

    Attributes
    ----------
    qual_id : QualifiedID
    index_or_params : List[IndexOrParams], default=[]
    tail : List[LeftExprTail], default=[]
    """

    qual_id: QualifiedID
    index_or_params: typing.List[IndexOrParams] = attrs.field(
        default=attrs.Factory(list)
    )
    tail: typing.List[LeftExprTail] = attrs.field(default=attrs.Factory(list))
