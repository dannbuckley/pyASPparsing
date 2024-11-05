"""Symbol base class"""

from functools import wraps
from inspect import signature
import typing
import attrs
from ...ast.ast_types.declarations import VarName


@attrs.define(slots=False)
class Symbol:
    """
    Attributes
    ----------
    symbol_name : str
    """

    symbol_name: str = attrs.field(validator=attrs.validators.instance_of(str))


@attrs.define(slots=False)
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


@attrs.define(slots=False)
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


@attrs.define(slots=False)
class SymbolTable:
    """
    Attributes
    ----------
    sym_table : Dict[str, Symbol]
    """

    sym_table: typing.Dict[str, Symbol] = attrs.field(
        default=attrs.Factory(dict), init=False
    )

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
