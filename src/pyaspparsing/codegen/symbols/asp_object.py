"""ASP object symbol type"""

from typing import Any
from ...ast.ast_types import (
    LeftExpr,
    ResponseExpr,
    RequestExpr,
    ServerExpr,
    PropertyExpr,
)
from .symbol import Symbol
from ..codegen_state import CodegenState


class ASPObject(Symbol):
    """An ASP object that may have methods, properties, or collections"""

    def __call__(self, left_expr: LeftExpr, cg_state: CodegenState) -> Any:
        """
        Parameters
        ----------
        left_expr : LeftExpr
        cg_state : CodegenState

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
            if isinstance(left_expr, PropertyExpr):
                return self.__getattribute__("handle_property_expr")(
                    left_expr, cg_state
                )
            if isinstance(left_expr, (ResponseExpr, RequestExpr, ServerExpr)):
                return self.__getattribute__("handle_builtin_left_expr")(
                    left_expr, cg_state
                )
            idx = 0
            ret_obj = self
            try:
                while idx < left_expr.end_idx:
                    if (l_subname := left_expr.subnames.get(idx, None)) is not None:
                        ret_obj = ret_obj.__getattribute__(l_subname)
                    elif (l_callargs := left_expr.call_args.get(idx, None)) is not None:
                        ret_obj = ret_obj(cg_state, *l_callargs)
                    else:
                        # don't catch, something is seriously wrong
                        raise RuntimeError(
                            f"Index {idx} of left expression is not valid"
                        )
                    idx += 1
                return ret_obj
            except (AttributeError, ValueError):
                # retry as a get property
                return self.__getattribute__("handle_property_expr")(
                    PropertyExpr.from_retrieval(left_expr), cg_state
                )
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
