"""ADODB Connection object"""

import re
from typing import Optional

import attrs

from ....ast.ast_types.base import Expr
from ....ast.ast_types.optimize import EvalExpr
from ....ast.ast_types.builtin_leftexpr.obj_property import PropertyExpr
from ..asp_object import ASPObject
from ..symbol import prepare_symbol_name, FunctionReturnSymbol
from .recordset import Recordset
from ...scope import ScopeType
from ...codegen_state import CodegenState


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Connection(ASPObject):
    """"""

    db: Optional[int] = attrs.field(default=None, init=False)
    db_queries: list[int] = attrs.field(default=attrs.Factory(list), init=False)

    def handle_property_expr(self, prop_expr: PropertyExpr, cg_state: CodegenState):
        """
        Parameters
        ----------
        prop_expr : PropertyExpr
        cg_state : CodegenState
        """
        assert isinstance(prop_expr, PropertyExpr)

    def begintrans(self, cg_state: CodegenState):
        """"""

    def cancel(self, cg_state: CodegenState):
        """"""

    def close(self, cg_state: CodegenState):
        """"""

    def committrans(self, cg_state: CodegenState):
        """"""

    def execute(
        self,
        cg_state: CodegenState,
        param_commandtext: Expr,
        param_ra: Optional[Expr] = None,
        param_options: Optional[Expr] = None,
        /,
    ) -> Recordset:
        """
        Parameters
        ----------
        param_commandtext
        param_ra : Expr | None, default=None
        param_options : Expr | None, default=None

        Returns
        -------
        Recordset
        """
        assert (
            self.db is not None
        ), "Must call Connection.Open before Connection.Execute"
        try:
            assert isinstance(
                param_commandtext, Expr
            ), "commandtext must be an expression"
            if param_ra is not None:
                assert isinstance(param_ra, Expr), "ra must be an expression"
            if param_options is not None:
                assert isinstance(param_options, Expr), "options must be an expression"

            ret_recordset = Recordset()
            ret_recordset.query = cg_state.add_database_query(
                self.db, param_commandtext, param_ra, param_options
            )
            self.db_queries.append(ret_recordset.query)
            with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
                cg_state.add_symbol(FunctionReturnSymbol("execute", ret_recordset))
                cg_state.add_function_return(
                    cg_state.scope_mgr.current_scope, "execute"
                )
        except AssertionError as ex:
            raise ValueError("Invalid input in Connection.Execute") from ex

    def open(
        self,
        cg_state: CodegenState,
        param_connectionstring: Expr,
        param_userid: Optional[Expr] = None,
        param_password: Optional[Expr] = None,
        param_options: Optional[Expr] = None,
        /,
    ) -> None:
        """
        Parameters
        ----------
        param_connectionstring : Expr
        param_userid : Expr | None, default=None
        param_password : Expr | None, default=None
        param_options : Expr | None, default=None
        """
        try:
            if param_userid is not None:
                assert isinstance(param_userid, Expr), "userid must be an expression"
            if param_password is not None:
                assert isinstance(
                    param_password, Expr
                ), "password must be an expression"
            if param_options is not None:
                assert isinstance(param_options, Expr), "options must be an expression"

            assert isinstance(param_connectionstring, EvalExpr) and isinstance(
                param_connectionstring.expr_value, str
            ), "connectionstring must be a string"
            cxn_dict = dict(
                re.findall(
                    # assume connection string is already valid
                    # just break into key-value pairs
                    r"([^=]+)=([^;]+);",
                    param_connectionstring.expr_value,
                )
            )

            # "open" a database connection
            self.db = cg_state.add_database_cxn(
                cxn_dict, param_userid, param_password, param_options
            )
        except AssertionError as ex:
            raise ValueError("Invalid input in Connection.Open") from ex

    def openschema(
        self,
        cg_state: CodegenState,
        param_querytype,
        param_criteria=None,
        param_schemaid=None,
        /,
    ):
        """"""
        with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
            cg_state.add_symbol(FunctionReturnSymbol("openschema"))
            cg_state.add_function_return(cg_state.scope_mgr.current_scope, "openschema")

    def rollbacktrans(self, cg_state: CodegenState):
        """"""
