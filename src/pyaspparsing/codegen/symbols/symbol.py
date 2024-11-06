"""Symbol base class"""

from functools import wraps
from inspect import signature
import typing
import attrs
from ...ast.ast_types.base import FormatterMixin
from ...ast.ast_types.declarations import VarName
from ...ast.ast_types.expressions import LeftExpr
from ...ast.ast_types.optimize import EvalExpr
from ...ast.ast_types.statements import AssignStmt


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
    """
    Attributes
    ----------
    value : Any, default=None
    """

    value: typing.Any = attrs.field(default=None)

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

    rank_list: typing.List[int] = attrs.field(
        default=attrs.Factory(list),
        validator=attrs.validators.deep_iterable(attrs.validators.instance_of(int)),
    )
    array_data: typing.Dict[typing.Tuple[int, ...], typing.Any] = attrs.field(
        default=attrs.Factory(dict), init=False
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

    def insert(self, idx: typing.Tuple[int, ...], value: typing.Any):
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


@attrs.define(repr=False, slots=False)
class SymbolTable(FormatterMixin):
    """
    Attributes
    ----------
    sym_table : Dict[str, Symbol]
    """

    sym_table: typing.Dict[str, Symbol] = attrs.field(
        default=attrs.Factory(dict), init=False
    )
    option_explicit: bool = attrs.field(default=False, init=False)

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
        self.sym_table[symbol.symbol_name] = symbol
        return True

    def assign(self, asgn: AssignStmt):
        """
        Parameters
        ----------
        asgn : AssignStmt
        """
        left_expr = asgn.target_expr
        assert isinstance(left_expr, LeftExpr)
        # value_expr = asgn.assign_expr
        if left_expr.sym_name not in self.sym_table:
            assert (
                not self.option_explicit
            ), "Option Explicit is set, variables must be defined before use"
            self.add_symbol(ValueSymbol(left_expr.sym_name, asgn.assign_expr))
        else:
            if isinstance(self.sym_table[left_expr.sym_name], ValueSymbol):
                self.sym_table[left_expr.sym_name].value = asgn.assign_expr
            elif isinstance(self.sym_table[left_expr.sym_name], ArraySymbol):

                def _get_array_idx():
                    nonlocal left_expr
                    assert isinstance(left_expr, LeftExpr)
                    assert len(left_expr.subnames) == 0
                    assert left_expr.call_args.get(0, None) is not None
                    for idx in left_expr.call_args[0]:
                        assert isinstance(idx, EvalExpr) and isinstance(
                            idx.expr_value, int
                        )
                        yield idx.expr_value

                self.sym_table[left_expr.sym_name].insert(
                    tuple(_get_array_idx()), asgn.assign_expr
                )
            elif isinstance(self.sym_table[left_expr.sym_name], ASPObject):
                pass


def prepare_symbol_name(symbol_type: type[Symbol]):
    """
    Parameters
    ----------
    symbol_type : type[Symbol]

    Returns
    -------
    partial[Symbol]

    Raises
    ------
    AssertionError
        If symbol_type is not a subclass of Symbol
    """
    assert issubclass(symbol_type, Symbol), "symbol_type must be a subclass of Symbol"

    @wraps(symbol_type)
    def wrapper(*args, **kwargs):
        # generate symbol name from casefolded class name
        return symbol_type(symbol_type.__name__.casefold(), *args, **kwargs)

    sig = signature(symbol_type)
    wrapper.__signature__ = sig.replace(parameters=tuple(sig.parameters.values())[1:])

    return wrapper
