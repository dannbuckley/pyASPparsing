"""ASP Server object"""

import attrs
from .symbol import ASPObject, prepare_symbol_name


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

    def createobject(self, param_progid, /):
        """"""

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
