"""Function base class"""

from collections.abc import Callable
import inspect
import attrs
from attrs.validators import deep_iterable, instance_of
from ..symbol import Symbol


@attrs.define(repr=False, slots=False)
class ASPFunction(Symbol):
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


@attrs.define(repr=False, slots=False)
class UserFunction(Symbol):
    """User-defined function created somewhere in the script"""

    func_scope_id: int = attrs.field(validator=instance_of(int))
    arg_names: list[str] = attrs.field(
        default=attrs.Factory(list), validator=deep_iterable(instance_of(str))
    )

    def __repr__(self):
        return (
            f"<UserFunction {self.symbol_name}({', '.join(self.arg_names)}); "
            f"func_scope_id={repr(self.func_scope_id)}>"
        )


@attrs.define(repr=False, slots=False)
class UserSub(Symbol):
    """User-defined subprocedure created somewhere in the script"""

    sub_scope_id: int = attrs.field(validator=instance_of(int))
    arg_names: list[str] = attrs.field(
        default=attrs.Factory(list), validator=deep_iterable(instance_of(str))
    )

    def __repr__(self):
        return (
            f"<UserSub {self.symbol_name}({', '.join(self.arg_names)}); "
            f"sub_scope_id={repr(self.sub_scope_id)}>"
        )
