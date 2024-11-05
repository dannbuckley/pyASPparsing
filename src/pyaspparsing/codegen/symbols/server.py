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
@attrs.define(slots=False)
class Server(ASPObject):
    """"""

    def __call__(self, *args, name: str):
        assert isinstance(name, str), "name must be a string"
        try:
            ex = None
            return self.__getattribute__(name.casefold())(*args)
        except AttributeError as ex_wrong_name:
            ex = ex_wrong_name
        except TypeError as ex_wrong_sig:
            ex = ex_wrong_sig
        finally:
            if ex is not None:
                raise ValueError("Invalid call on Server object") from ex

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
            raise ValueError("Server.CreateObject expects a string for param_progid")
        parts = param_progid.expr_value.split(".")
        assert len(parts) == 2, "param_progid should match 'Vendor.Component'"
        try:
            return server_object_types[parts[0]][parts[1]]()
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
