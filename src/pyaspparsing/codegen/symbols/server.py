"""ASP Server object"""

import typing
import attrs
from ...ast.ast_types.optimize import EvalExpr
from .symbol import ASPObject, prepare_symbol_name
from .adodb import Connection, Recordset

server_object_types: typing.Dict[str, typing.Dict[str, type[ASPObject]]] = {
    "adodb": {"connection": Connection, "recordset": Recordset}
}


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Server(ASPObject):
    """"""

    def createobject(self, param_progid, /) -> ASPObject:
        """NOT CALLED DIRECTLY

        Called indirectly by `__call__(..., name="createobject")`

        Parameters
        ----------
        param_progid

        Returns
        -------
        ASPObject

        Raises
        ------
        ValueError

        AssertionError
        """
        if not isinstance(param_progid, EvalExpr) or not isinstance(
            param_progid.expr_value, str
        ):
            raise ValueError("Server.CreateObject expects a string for progid")
        parts = param_progid.expr_value.split(".")
        assert len(parts) == 2, "progid should match 'Vendor.Component'"
        try:
            return server_object_types[parts[0].casefold()][parts[1].casefold()]()
        except KeyError as ex:
            raise ValueError(
                f"Could not determine type of component: '{param_progid.expr_value}'"
            ) from ex

    def execute(self, param_path, /):
        """"""

    def getlasterror(self):
        """"""

    def htmlencode(self, param_string, /):
        """"""

    def mappath(self, param_path, /):
        """"""

    def transfer(self, param_path, /):
        """"""

    def urlencode(self, param_string, /):
        """"""
