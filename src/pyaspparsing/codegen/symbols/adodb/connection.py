"""ADODB Connection object"""

from typing import Optional, List
import attrs
from ....ast.ast_types.base import Expr
from ..symbol import ASPObject, prepare_symbol_name
from .base import Database, Query
from .recordset import Recordset


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Connection(ASPObject):
    """"""

    db: Optional[Database] = attrs.field(default=None, init=False)
    db_queries: List[Query] = attrs.field(default=attrs.Factory(list), init=False)

    def begintrans(self):
        """"""

    def cancel(self):
        """"""

    def close(self):
        """"""

    def committrans(self):
        """"""

    def execute(
        self,
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
            ret_recordset.query = Query(
                self.db, param_commandtext, param_ra, param_options
            )
            self.db_queries.append(ret_recordset.query)
            return ret_recordset
        except AssertionError as ex:
            raise ValueError("Invalid input in Connection.Execute") from ex

    def open(
        self,
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
            assert isinstance(
                param_connectionstring, Expr
            ), "connectionstring must be an expression"
            if param_userid is not None:
                assert isinstance(param_userid, Expr), "userid must be an expression"
            if param_password is not None:
                assert isinstance(
                    param_password, Expr
                ), "password must be an expression"
            if param_options is not None:
                assert isinstance(param_options, Expr), "options must be an expression"

            # "open" a database connection
            self.db = Database(
                param_connectionstring, param_userid, param_password, param_options
            )
        except AssertionError as ex:
            raise ValueError("Invalid input in Connection.Open") from ex

    def openschema(self, param_querytype, param_criteria=None, param_schemaid=None, /):
        """"""

    def rollbacktrans(self):
        """"""
