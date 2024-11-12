"""Symbol base class"""

from functools import partial
from typing import Any, Generator
import attrs
from ...ast.ast_types.base import FormatterMixin
from ...ast.ast_types.declarations import VarName
from ...ast.ast_types.expressions import LeftExpr
from ...ast.ast_types.optimize import EvalExpr
from ...ast.ast_types.statements import AssignStmt
from ...ast.ast_types.builtin_leftexpr import ResponseExpr, RequestExpr, ServerExpr


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
class UnresolvedExternalSymbol(Symbol):
    """Symbol type for names used in function or sub declarations

    If the name is not yet defined, use this as a placeholder
    """


@attrs.define(repr=False, slots=False)
class ValueSymbol(Symbol):
    """
    Attributes
    ----------
    value : Any, default=None
    """

    value: Any = attrs.field(default=None)

    def __repr__(self):
        base_repr = f"<ValueSymbol {repr(self.symbol_name)}"
        if self.value is None:
            return base_repr + ">"
        if isinstance(self.value, EvalExpr):
            return base_repr + f"; value={repr(self.value.expr_value)}>"
        return base_repr + f"; value of type {repr(type(self.value).__name__)}>"

    @staticmethod
    def from_var_name(var_name: VarName):
        """
        Parameters
        ----------
        var_name : VarName

        Returns
        -------
        ValueSymbol
        """
        return ValueSymbol(var_name.extended_id.id_code)


@attrs.define(repr=False, slots=False)
class ArraySymbol(Symbol):
    """
    Attributes
    ----------
    rank_list : List[int], default=[]
    """

    rank_list: list[int] = attrs.field(
        default=attrs.Factory(list),
        validator=attrs.validators.deep_iterable(attrs.validators.instance_of(int)),
    )
    array_data: dict[tuple[int, ...], Any] = attrs.field(
        default=attrs.Factory(dict), init=False
    )

    def __repr__(self):
        return (
            f"<ArraySymbol {repr(self.symbol_name)}; rank_list={repr(self.rank_list)}>"
        )

    @staticmethod
    def from_var_name(var_name: VarName):
        """
        Parameters
        ----------
        var_name : VarName

        Returns
        -------
        ArraySymbol
        """
        return ArraySymbol(var_name.extended_id.id_code, var_name.array_rank_list)

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
            raise ValueError(
                "idx must be a tuple of integers that is the same length as the array's rank list"
            )
        if not all(map(lambda ival: 0 <= ival[0] <= ival[1], zip(idx, self.rank_list))):
            raise ValueError("Each idx[i] must be in [0, rank_list[i]]")
        self.array_data[idx] = value


class ASPObject(Symbol):
    """An ASP object that may have methods, properties, or collections"""

    def __call__(self, left_expr: LeftExpr) -> Any:
        """
        Parameters
        ----------
        left_expr : LeftExpr

        Returns
        -------
        Any
        """
        try:
            ex = None
            assert isinstance(
                left_expr, LeftExpr
            ), f"left_expr must be a valid left expression, got {repr(type(left_expr))}"
            assert left_expr.end_idx >= 1, "left_expr cannot contain only symbol name"
            if isinstance(left_expr, (ResponseExpr, RequestExpr, ServerExpr)):
                return self.__getattribute__("handle_builtin_left_expr")(left_expr)
            idx = 0
            ret_obj = self
            while idx < left_expr.end_idx:
                if (l_subname := left_expr.subnames.get(idx, None)) is not None:
                    ret_obj = ret_obj.__getattribute__(l_subname)
                elif (l_callargs := left_expr.call_args.get(idx, None)) is not None:
                    ret_obj = ret_obj(*l_callargs)
                else:
                    # don't catch, something is seriously wrong
                    raise RuntimeError(f"Index {idx} of left expression is not valid")
                idx += 1
            return ret_obj
        except AssertionError as ex_wrong_type:
            ex = ex_wrong_type
        except AttributeError as ex_wrong_name:
            ex = ex_wrong_name
        except TypeError as ex_wrong_sig:
            ex = ex_wrong_sig
        finally:
            if ex is not None:
                raise ValueError(
                    f"Invalid call on {self.__class__.__name__} object symbol"
                ) from ex


@attrs.define(repr=False, slots=False)
class SymbolTable(FormatterMixin):
    """
    Attributes
    ----------
    sym_table : Dict[str, Symbol]
    """

    sym_table: dict[str, Symbol] = attrs.field(default=attrs.Factory(dict), init=False)
    option_explicit: bool = attrs.field(default=False, init=False)

    # how many times has the symbol been retrieved?
    _sym_get: dict[str, int] = attrs.field(default=attrs.Factory(dict), init=False)
    # how many times has the symbol been assigned to?
    _sym_set: dict[str, int] = attrs.field(default=attrs.Factory(dict), init=False)

    def __getitem__(self, key: str) -> Symbol:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        # don't catch KeyError
        ret = self.sym_table[key]
        # record retrieval for later use
        self._sym_get[key] = self._sym_get.get(key, 0) + 1
        return ret

    def __setitem__(self, key: str, value: Symbol) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not isinstance(value, Symbol):
            raise TypeError("value must be a subclass of Symbol")
        self.sym_table[key] = value
        # record assignment for later use
        self._sym_set[key] = self._sym_set.get(key, 0) + 1

    def set_explicit(self):
        """Register the Option Explicit statement with the symbol table"""
        assert not self.option_explicit, "Option Explicit can only be set once"
        self.option_explicit = True

    def add_symbol(self, symbol: Symbol) -> bool:
        """Add a new symbol to the symbol table

        Does nothing if the name already exists

        Parameters
        ----------
        symbol : Symbol

        Returns
        -------
        bool
            False if name already exists
        """
        if symbol.symbol_name in self.sym_table:
            return False
        # don't track this as assignment
        self.sym_table[symbol.symbol_name] = symbol
        return True

    def assign(self, asgn: AssignStmt):
        """
        Parameters
        ----------
        asgn : AssignStmt
        """
        left_expr = asgn.target_expr
        if left_expr.sym_name not in self.sym_table:
            assert (
                not self.option_explicit
            ), "Option Explicit is set, variables must be defined before use"
            # TODO: how to handle subnames of symbol that doesn't exist?
            assert left_expr.end_idx == 0
            self.add_symbol(ValueSymbol(left_expr.sym_name, asgn.assign_expr))
            self._sym_set[left_expr.sym_name] = (
                self._sym_set.get(left_expr.sym_name, 0) + 1
            )
        else:
            if isinstance(self.sym_table[left_expr.sym_name], ValueSymbol):
                if left_expr.end_idx == 0:
                    # simple variable assignment
                    # overwrite value with assignment expression
                    self[left_expr.sym_name] = ValueSymbol(
                        left_expr.sym_name,
                        (
                            # assignment expression should be evaluated
                            (
                                self[asgn.assign_expr.sym_name].value(asgn.assign_expr)
                                if isinstance(
                                    self.sym_table[asgn.assign_expr.sym_name],
                                    ValueSymbol,
                                )
                                and isinstance(
                                    self.sym_table[asgn.assign_expr.sym_name].value,
                                    ASPObject,
                                )
                                else self[asgn.assign_expr.sym_name](asgn.assign_expr)
                            )
                            if isinstance(asgn.assign_expr, LeftExpr)
                            else
                            # use assignment expression as-is
                            asgn.assign_expr
                        ),
                    )
                elif len(left_expr.subnames) > 0 and isinstance(
                    self.sym_table[left_expr.sym_name].value, ASPObject
                ):
                    # property assignment
                    pass
                else:
                    raise RuntimeError
            elif isinstance(self.sym_table[left_expr.sym_name], ArraySymbol):
                # array item assignment
                def _get_array_idx() -> Generator[int, None, None]:
                    """Extract array indices from target expression

                    Yields
                    ------
                    int
                        Array index

                    Raises
                    ------
                    AssertionError
                    """
                    nonlocal left_expr
                    assert (
                        len(left_expr.subnames) == 0
                    ), "Target of array assignment cannot have subnames"
                    assert (
                        len(left_expr.call_args) == 1
                        and (array_rank := left_expr.call_args.get(0, None)) is not None
                    ), "Target of array assignment must have exactly one non-None call record"
                    assert (
                        len(array_rank) >= 1
                    ), "Call record in array assignment must have at least one value"
                    for idx in left_expr.call_args[0]:
                        assert isinstance(idx, EvalExpr) and isinstance(
                            idx.expr_value, int
                        ), "Item in call record of array assignment target must be an integer"
                        yield idx.expr_value

                self.sym_table[left_expr.sym_name].insert(
                    tuple(_get_array_idx()), asgn.assign_expr
                )
            elif isinstance(self.sym_table[left_expr.sym_name], ASPObject):
                # TODO: establish appropriate assign target (properties?)
                pass

    def call(self, left_expr: LeftExpr):
        """
        Parameters
        ----------
        left_expr : LeftExpr
        """
        try:
            sym = self[left_expr.sym_name]
            if isinstance(sym, ASPObject):
                sym(left_expr)
            elif isinstance(sym, ValueSymbol) and isinstance(sym.value, ASPObject):
                sym.value(left_expr)
            # TODO: symbol is a function?
        except KeyError as ex:
            raise ValueError("Invalid symbol name in left_expr") from ex


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
