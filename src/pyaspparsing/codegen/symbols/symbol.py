"""Symbol base class"""

from functools import partial
from typing import Any
import attrs
from ...ast.ast_types.declarations import VarName
from ...ast.ast_types.expressions import LeftExpr
from ...ast.ast_types.optimize import EvalExpr
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
    """Simple variable created by a VarDecl object

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
    """Array variable created by a VarDecl object

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
            raise ValueError("Each idx[i] must be in the range [0, rank_list[i]]")
        self.array_data[idx] = value


@attrs.define(repr=False, slots=False)
class ValueMethodArgument(Symbol):
    """Argument in a method that is given by value
    (i.e., a copy of the value is made and given to the method)

    Used in: FunctionDecl, SubDecl, PropertyDecl
    """


@attrs.define(repr=False, slots=False)
class ReferenceMethodArgument(Symbol):
    """Argument in a method that is given by reference
    (i.e., referring to a value defined in an enclosing scope)

    Used in: FunctionDecl, SubDecl, PropertyDecl
    """


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
