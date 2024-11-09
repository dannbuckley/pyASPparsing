"""AST types for Request left expressions"""

import typing
import attrs
from ..expressions import LeftExpr

# ===== COLLECTIONS =====


@attrs.define(repr=False, slots=False)
class RequestClientCertificateExpr(LeftExpr):
    """"""


@attrs.define(repr=False, slots=False)
class RequestCookiesExpr(LeftExpr):
    """"""

    @property
    def cookie_name(self):
        """"""
        return

    @property
    def cookie_key(self):
        """"""
        return

    @property
    def cookie_attribute(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class RequestFormExpr(LeftExpr):
    """"""

    @property
    def element(self):
        """"""
        return

    @property
    def index(self):
        """"""
        return

    @property
    def has_count(self) -> bool:
        """"""
        return False


@attrs.define(repr=False, slots=False)
class RequestQueryStringExpr(LeftExpr):
    """"""

    @property
    def variable(self):
        """"""
        return

    @property
    def index(self):
        """"""
        return

    @property
    def has_count(self) -> bool:
        """"""
        return False


@attrs.define(repr=False, slots=False)
class RequestServerVariablesExpr(LeftExpr):
    """"""

    @property
    def server_variable(self):
        """"""
        return


# ===== PROPERTIES =====


@attrs.define(repr=False, slots=False)
class RequestTotalBytesExpr(LeftExpr):
    """"""


# ===== METHODS =====


@attrs.define(repr=False, slots=False)
class RequestBinaryReadExpr(LeftExpr):
    """"""

    @property
    def param_count(self):
        """"""
        return
