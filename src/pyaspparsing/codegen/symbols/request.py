"""ASP Request object"""

import attrs
from .symbol import ASPObject, prepare_symbol_name


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Request(ASPObject):
    """"""

    def binaryread(self, param_count, /):
        """"""
