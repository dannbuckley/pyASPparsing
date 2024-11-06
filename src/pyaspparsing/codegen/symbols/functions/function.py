"""Function base class"""

from collections.abc import Callable
import inspect
import attrs
from ..symbol import Symbol


@attrs.define(repr=False, slots=False)
class Function(Symbol):
    """
    Attributes
    ----------
    func : Callable
    """

    func: Callable

    def __call__(self, *args):
        try:
            return self.func(*args)
        except TypeError as ex:
            raise ValueError("Invalid number of arguments") from ex

    def __repr__(self):
        sig = inspect.signature(self.func)
        return f"<Function {self.symbol_name}({', '.join(sig.parameters.keys())})>"
