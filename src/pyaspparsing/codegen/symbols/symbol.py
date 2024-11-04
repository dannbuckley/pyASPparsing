"""Symbol base class"""

from functools import wraps
from inspect import signature
import typing
import attrs


@attrs.define(slots=False)
class Symbol:
    """
    Attributes
    ----------
    symbol_name : str
    """

    symbol_name: str = attrs.field(validator=attrs.validators.instance_of(str))


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
