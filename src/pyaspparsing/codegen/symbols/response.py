"""ASP Response object"""

import attrs
from .symbol import ASPObject, prepare_symbol_name


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Response(ASPObject):
    """"""

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
