"""ADODB Connection object"""

import attrs
from ..symbol import ASPObject, prepare_symbol_name


@prepare_symbol_name
@attrs.define(slots=False)
class Connection(ASPObject):
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
                raise ValueError("Invalid call on Connection object") from ex

    def begintrans(self):
        """"""

    def cancel(self):
        """"""

    def close(self):
        """"""

    def committrans(self):
        """"""

    def execute(self, param_commandtext, param_ra=None, param_options=None, /):
        """"""

    def open(
        self,
        param_connectionstring,
        param_userid=None,
        param_password=None,
        param_options=None,
        /,
    ):
        """"""

    def openschema(self, param_querytype, param_criteria=None, param_schemaid=None, /):
        """"""

    def rollbacktrans(self):
        """"""
