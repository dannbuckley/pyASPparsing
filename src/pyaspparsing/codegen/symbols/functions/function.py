"""Function base class"""

from collections.abc import Callable
import attrs
from ..symbol import Symbol


@attrs.define(slots=False)
class Function(Symbol):
    """"""

    func: Callable

    def __call__(self, *args):
        try:
            return self.func(*args)
        except TypeError as ex:
            raise ValueError("Invalid number of arguments") from ex
