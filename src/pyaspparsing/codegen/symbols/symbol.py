"""Symbol base class"""

from functools import wraps
from inspect import signature
import attrs


@attrs.define(slots=False)
class Symbol:
    """
    Attributes
    ----------
    symbol_name : str
    """

    symbol_name: str = attrs.field(validator=attrs.validators.instance_of(str))


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
