"""ASP Response object"""

import attrs
from .symbol import ASPObject, prepare_symbol_name


@prepare_symbol_name
@attrs.define(slots=False)
class Response(ASPObject):
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
                raise ValueError("Invalid call on Response object") from ex

    def addheader(self, param_name, param_value, /):
        """"""

    def appendtolog(self, param_string, /):
        """"""

    def binarywrite(self, param_data, /):
        """"""

    def clear(self):
        """"""

    def end(self):
        """"""

    def flush(self):
        """"""

    def redirect(self, param_url, /):
        """"""

    def write(self, param_variant, /):
        """"""
