"""ASP Request object"""

import attrs
from .symbol import ASPObject, prepare_symbol_name


@prepare_symbol_name
@attrs.define(slots=False)
class Request(ASPObject):
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
                raise ValueError("Invalid call on Request object") from ex

    def binaryread(self, param_count, /):
        """"""
