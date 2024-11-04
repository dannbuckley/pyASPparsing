"""ASP Server object"""

import attrs
from .symbol import Symbol, prepare_symbol_name


@prepare_symbol_name
@attrs.define(slots=False)
class Server(Symbol):
    """"""
