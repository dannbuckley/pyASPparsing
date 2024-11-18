"""Symbol base class"""

from functools import partial
from typing import Optional, Any
import attrs
from ...ast.ast_types.base import Expr, AccessModifierType
from ...ast.ast_types.declarations import VarName, FieldName
from ...ast.ast_types.expressions import LeftExpr
from ...ast.ast_types.optimize import EvalExpr


@attrs.define(repr=False, slots=False)
class Symbol:
    """
    Attributes
    ----------
    symbol_name : str
    """

    symbol_name: str = attrs.field(validator=attrs.validators.instance_of(str))

    def __repr__(self):
        return f"<{self.__class__.__name__} {repr(self.symbol_name)}>"


@attrs.define(repr=False, slots=False)
class ValueSymbol(Symbol):
    """Simple variable created by a VarDecl object

    Attributes
    ----------
    value : Any, default=None
    access_mod : AccessModifierType | None, default=None
    """

    value: Any = attrs.field(default=None)
    access_mod: Optional[AccessModifierType] = attrs.field(default=None, kw_only=True)

    def __repr__(self):
        match self.access_mod:
            case AccessModifierType.PRIVATE:
                access_str = "Private "
            case AccessModifierType.PUBLIC:
                access_str = "Public "
            case _:
                access_str = ""
        base_repr = f"<{access_str}ValueSymbol {repr(self.symbol_name)}"
        if self.value is None:
            return base_repr + ">"
        if isinstance(self.value, EvalExpr):
            return base_repr + f"; value={repr(self.value.expr_value)}>"
        return base_repr + f"; value of type {repr(type(self.value).__name__)}>"

    @staticmethod
    def from_field_name(field_name: FieldName, access_mod: AccessModifierType):
        """
        Parameters
        ----------
        field_name : FieldName
        access_mod : AccessModifierType

        Returns
        -------
        ValueSymbol
        """
        return ValueSymbol(field_name.field_id.id_code, access_mod=access_mod)

    @staticmethod
    def from_var_name(
        var_name: VarName, *, access_mod: Optional[AccessModifierType] = None
    ):
        """
        Parameters
        ----------
        var_name : VarName
        access_mod : AccessModifierType | None, default=None

        Returns
        -------
        ValueSymbol
        """
        return ValueSymbol(var_name.extended_id.id_code, access_mod=access_mod)


@attrs.define(repr=False, slots=False)
class LocalAssignmentSymbol(ValueSymbol):
    """Symbol representing assignment to a variable defined in an enclosing scope

    This symbol treats the original value symbol as
    a special symbol inside the narrower scope
    """

    def __repr__(self):
        match self.access_mod:
            case AccessModifierType.PRIVATE:
                access_str = "Private "
            case AccessModifierType.PUBLIC:
                access_str = "Public "
            case _:
                access_str = ""
        base_repr = f"<{access_str}LocalAssignmentSymbol {repr(self.symbol_name)}"
        if self.value is None:
            return base_repr + ">"
        if isinstance(self.value, EvalExpr):
            return base_repr + f"; value={repr(self.value.expr_value)}>"
        return base_repr + f"; value of type {repr(type(self.value).__name__)}>"

    @staticmethod
    def from_value_symbol(val_symbol: ValueSymbol):
        """
        Parameters
        ----------
        val_symbol : ValueSymbol
        orig_scope : int

        Returns
        -------
        LocalAssignmentSymbol
        """
        assert isinstance(val_symbol, ValueSymbol)
        return LocalAssignmentSymbol(
            val_symbol.symbol_name,
            val_symbol.value,
            access_mod=val_symbol.access_mod,
        )


@attrs.define(repr=False, slots=False)
class ArraySymbol(Symbol):
    """Array variable created by a VarDecl object

    Attributes
    ----------
    rank_list : List[int], default=[]
    array_data : Dict[Tuple[int, ...], Any], default={}
    access_mod : AccessModifierType | None, default=None
    """

    rank_list: list[int] = attrs.field(
        default=attrs.Factory(list),
        validator=attrs.validators.deep_iterable(attrs.validators.instance_of(int)),
    )
    array_data: dict[tuple[int, ...], Any] = attrs.field(
        default=attrs.Factory(dict), init=False
    )
    access_mod: Optional[AccessModifierType] = attrs.field(default=None, kw_only=True)

    def __repr__(self):
        match self.access_mod:
            case AccessModifierType.PRIVATE:
                access_str = "Private "
            case AccessModifierType.PUBLIC:
                access_str = "Public "
            case _:
                access_str = ""
        return (
            f"<{access_str}ArraySymbol {repr(self.symbol_name)}; "
            f"rank_list={repr(self.rank_list)}>"
        )

    @staticmethod
    def from_field_name(field_name: FieldName, access_mod: AccessModifierType):
        """
        Parameters
        ----------
        field_name : FieldName
        access_mod : AccessModifierType

        Returns
        -------
        ArraySymbol
        """
        return ArraySymbol(
            field_name.field_id.id_code,
            field_name.array_rank_list,
            access_mod=access_mod,
        )

    @staticmethod
    def from_var_name(
        var_name: VarName, *, access_mod: Optional[AccessModifierType] = None
    ):
        """
        Parameters
        ----------
        var_name : VarName
        access_mod : AccessModifierType | None, default=None

        Returns
        -------
        ArraySymbol
        """
        return ArraySymbol(
            var_name.extended_id.id_code,
            var_name.array_rank_list,
            access_mod=access_mod,
        )

    def insert(self, idx: tuple[int, ...], value: Any):
        """
        Parameters
        ----------
        idx : Tuple[int, ...]
        value : Any
        """
        if not len(idx) == len(self.rank_list) or not all(
            map(lambda x: isinstance(x, int), idx)
        ):
            return
            # raise ValueError(
            #     "idx must be a tuple of integers that is the same length as the array's rank list"
            # )
        if not all(map(lambda ival: 0 <= ival[0] <= ival[1], zip(idx, self.rank_list))):
            # raise ValueError("Each idx[i] must be in the range [0, rank_list[i]]")
            return
        self.array_data[idx] = value

    def retrieve(self, left_expr: LeftExpr) -> Any:
        """
        Parameters
        ----------
        left_expr : LeftExpr

        Returns
        -------
        Any

        Raises
        ------
        AssertionError
        """
        assert left_expr.sym_name == self.symbol_name, "Symbol names must match"
        assert (
            left_expr.end_idx == 1
            and (idx := left_expr.call_args.get(0, None)) is not None
        ), "left_expr must match 'sym_name(...)'"

        def _unwrap_eval_expr():
            nonlocal idx
            for item in idx:
                if isinstance(item, EvalExpr):
                    yield item.expr_value
                else:
                    yield item

        idx = tuple(_unwrap_eval_expr())
        assert len(idx) == len(self.rank_list) and all(
            map(lambda x: isinstance(x, int), idx)
        ), "idx must be a tuple of integers that is the same length as the array's rank list"
        return self.array_data[idx]


@attrs.define(repr=False, slots=False)
class ConstantSymbol(Symbol):
    """
    Attributes
    ----------
    access_mod : AccessModifierType
    const_value : Any
    """

    access_mod: AccessModifierType
    const_value: Any

    def __repr__(self):
        match self.access_mod:
            case AccessModifierType.PRIVATE:
                access_str = "Private "
            case AccessModifierType.PUBLIC:
                access_str = "Public "
        return (
            f"<{access_str}ConstantSymbol {repr(self.symbol_name)};"
            f" value={repr(self.const_value)}>"
        )


@attrs.define(repr=False, slots=False)
class ValueMethodArgument(Symbol):
    """Argument in a method that is given by value
    (i.e., a copy of the value is made and given to the method)

    Used in: FunctionDecl, SubDecl, PropertyDecl

    Attributes
    ----------
    value : Any, default=None
    """

    value: Any = attrs.field(default=None)

    def __repr__(self):
        base_repr = f"<ValueMethodArgument {repr(self.symbol_name)}"
        if self.value is None:
            return base_repr + ">"
        if isinstance(self.value, EvalExpr):
            return base_repr + f"; value={repr(self.value.expr_value)}>"
        return base_repr + f"; value of type {repr(type(self.value).__name__)}>"


@attrs.define(repr=False, slots=False)
class ReferenceMethodArgument(Symbol):
    """Argument in a method that is given by reference
    (i.e., referring to a value defined in an enclosing scope)

    Used in: FunctionDecl, SubDecl, PropertyDecl

    Attributes
    ----------
    ref_scope : int | None, default=None
    ref_name : str | None, default=None
    """

    # scope of original symbol
    ref_scope: Optional[int] = attrs.field(default=None)
    # name of original symbol
    ref_name: Optional[str] = attrs.field(default=None)

    def __repr__(self):
        base_repr = f"<ReferenceMethodArgument {repr(self.symbol_name)}"
        if self.ref_scope is None and self.ref_name is None:
            return base_repr + ">"
        return (
            base_repr + f"; refers to {repr(self.ref_name)} in scope {self.ref_scope}>"
        )


@attrs.define(repr=False, slots=False)
class FunctionReturnSymbol(Symbol):
    """When inside a function, a value assigned to the function name
    will be returned when the function finishes

    This symbol treats the function name as a special symbol inside a function scope

    The following function will return "Hello, world!":
    ```
    Function my_function()
        my_function = "Hello, world!"
    End Function
    ```
    """

    return_value: Any = attrs.field(default=None)

    def __repr__(self):
        base_repr = f"<FunctionReturnSymbol {repr(self.symbol_name)}"
        if self.return_value is None:
            return base_repr + ">"
        return (
            base_repr
            + f"; return value of type {repr(type(self.return_value).__name__)}>"
        )


@attrs.define(repr=False, slots=False)
class ForLoopRangeTargetSymbol(Symbol):
    """Symbol representing the target variable in a '=' 'To' for loop

    This symbol treats the target as a special symbol inside a for loop scope

    Attributes
    ----------
    range_from : Expr
    range_to : Expr
    range_step : Expr | None
    """

    range_from: Expr
    range_to: Expr
    range_step: Optional[Expr]

    def __repr__(self):
        from_repr = (
            repr(self.range_from.expr_value)
            if isinstance(self.range_from, EvalExpr)
            else f"object of type {repr(type(self.range_from).__name__)}"
        )
        to_repr = (
            repr(self.range_to.expr_value)
            if isinstance(self.range_to, EvalExpr)
            else f"object of type {repr(type(self.range_to).__name__)}"
        )
        if self.range_step is None:
            step_repr = "1"
        else:
            step_repr = (
                repr(self.range_step.expr_value)
                if isinstance(self.range_step, EvalExpr)
                else f"object of type {repr(type(self.range_step).__name__)}"
            )
        return (
            f"<For loop target {repr(self.symbol_name)}; "
            f"range_from={from_repr}, "
            f"range_to={to_repr}, "
            f"range_step={step_repr}>"
        )

    @property
    def constant_evaluation(self):
        """
        Returns
        -------
        bool
            True if the for loop definition contains only constant,
            pre-evaluated expressions
        """
        return (
            isinstance(self.range_from, EvalExpr)
            and isinstance(self.range_to, EvalExpr)
            and (self.range_step is None or isinstance(self.range_step, EvalExpr))
        )


@attrs.define(repr=False, slots=False)
class ForLoopIteratorTargetSymbol(Symbol):
    """Symbol representing the target variable in an 'Each' 'In' for loop

    This symbol treats the target as a special symbol inside a for loop scope

    Attributes
    ----------
    loop_iterator : Expr
    """

    loop_iterator: Expr

    def __repr__(self):
        return (
            f"<For loop target {repr(self.symbol_name)}; "
            f"loop_iterator=object of type {repr(type(self.loop_iterator).__name__)}>"
        )


def prepare_symbol_name[T](symbol_type: type[T]) -> partial[T]:
    """Auto-generate symbol name from casefolded class name

    Parameters
    ----------
    symbol_type : type[Symbol]

    Returns
    -------
    Wrapped Symbol (sub)class

    Raises
    ------
    AssertionError
        If symbol_type is not a subclass of Symbol
    """
    assert issubclass(symbol_type, Symbol), "symbol_type must be a subclass of Symbol"
    return partial(symbol_type, symbol_type.__name__.casefold())
