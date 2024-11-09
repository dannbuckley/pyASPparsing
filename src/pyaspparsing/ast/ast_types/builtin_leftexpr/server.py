"""AST types for Server left expressions"""

import typing
import attrs
from ..expressions import LeftExpr


# ===== PROPERTIES =====


@attrs.define(repr=False, slots=False)
class ServerScriptTimeoutExpr(LeftExpr):
    """"""


# ===== METHODS =====


@attrs.define(repr=False, slots=False)
class ServerCreateObjectExpr(LeftExpr):
    """"""

    @property
    def param_progid(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ServerExecuteExpr(LeftExpr):
    """"""

    @property
    def param_path(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ServerGetLastErrorExpr(LeftExpr):
    """"""


@attrs.define(repr=False, slots=False)
class ServerHTMLEncodeExpr(LeftExpr):
    """"""

    @property
    def param_string(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ServerMapPathExpr(LeftExpr):
    """"""

    @property
    def param_path(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ServerTransferExpr(LeftExpr):
    """"""

    @property
    def param_path(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ServerURLEncodeExpr(LeftExpr):
    """"""

    @property
    def param_string(self):
        """"""
        return
