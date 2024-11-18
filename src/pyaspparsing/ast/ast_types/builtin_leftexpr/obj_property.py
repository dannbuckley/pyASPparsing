"""Special left expression for handling ASP object properties"""

from typing import Any
import attrs
from ..expressions import LeftExpr


@attrs.define(repr=False, slots=False)
class PropertyExpr(LeftExpr):
    """
    Methods
    -------
    from_retrieval(left_expr)
        Make a property get expression
    from_assignment(stmt)
        Make a property set expression
    """

    @property
    def object_property(self) -> LeftExpr:
        """A left expression representing the object property

        Returns
        -------
        LeftExpr
        """
        return self.call_args[1][0]

    @property
    def assign_value(self):
        """A value to assign to the object property

        Returns
        -------
        Any
        """
        if (asgn_args := self.call_args.get(2, None)) is not None:
            return asgn_args[0]
        return None

    @staticmethod
    def from_retrieval(left_expr: LeftExpr):
        """
        Parameters
        ----------
        left_expr : LeftExpr

        Returns
        -------
        PropertyExpr
        """
        return (
            PropertyExpr(left_expr.sym_name)
            .get_subname("__get_property")(left_expr)
            .track_index_or_param()
        )

    @staticmethod
    def from_assignment(target_expr: LeftExpr, assign_val: Any):
        """
        Parameters
        ----------
        stmt : AssignStmt

        Returns
        -------
        PropertyExpr
        """
        return (
            PropertyExpr(target_expr.sym_name)
            .get_subname("__set_property")(target_expr)
            .track_index_or_param()(assign_val)
            .track_index_or_param()
        )
