"""Expression AST classes"""

import enum
from typing import Optional, Any, Self

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

    id_tokens: list[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class IndexOrParams(FormatterMixin):
    """Defined of grammar line 519

    Attributes
    ----------
    expr_list : List[Expr | None], default=[]
    dot : bool, default=False
    """

    expr_list: list[Optional[Expr]] = attrs.field(default=attrs.Factory(list))
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
    index_or_params: list[IndexOrParams] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class LeftExpr(FormatterMixin, Value):
    """Defined on grammar line 430

    Attributes
    ----------
    sym_name : str
        Top-level name of the symbol
    subnames : Dict[int, str]
        Subnames that have been requested from this symbol
    call_args : Dict[int, Tuple[Any, ...]]
        Record of procedure calls for this symbol,
        either for the top-level name or for subnames

    Methods
    -------
    get_subname(subname)
        Request a subname from the main symbol
    """

    sym_name: str = attrs.field(validator=attrs.validators.instance_of(str))
    subnames: dict[int, str] = attrs.field(default=attrs.Factory(dict), init=False)
    call_args: dict[int, tuple[Any, ...]] = attrs.field(
        default=attrs.Factory(dict), init=False
    )
    end_idx: int = attrs.field(default=0, init=False, eq=False)
    num_index_or_param: int = attrs.field(default=0, init=False, eq=False)
    num_tail: int = attrs.field(default=0, init=False, eq=False)

    def track_index_or_param(self) -> Self:
        """Increment count of IndexOrParams objects parsed

        Returns
        -------
        LeftExpr
            The current LeftExpr instance
        """
        self.num_index_or_param += 1
        return self

    def track_tail(self) -> Self:
        """Increment count of LeftExprTail objects parsed

        Returns
        -------
        LeftExpr
            The current LeftExpr instance
        """
        self.num_tail += 1
        return self

    def get_subname(self, subname: str) -> Self:
        """
        Parameters
        ----------
        subname : str

        Returns
        -------
        LeftExpr
            The current LeftExpr instance
        """
        if not isinstance(subname, str):
            raise ValueError("subname must be a string")
        self.subnames[self.end_idx] = subname
        self.end_idx += 1
        # return self for method-chaining
        return self

    def __call__(self, *args: Any) -> Self:
        """Current name has an IndexOrParams object

        Parameters
        ----------
        *args : Any

        Returns
        -------
        LeftExpr
            The current LeftExpr instance
        """
        self.call_args[self.end_idx] = args
        self.end_idx += 1
        # return self for method-chaining
        return self
