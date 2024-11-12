"""MSWC PageCounter object"""

from typing import Optional
import attrs
from ....ast.ast_types.base import Expr
from ..symbol import ASPObject, prepare_symbol_name


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class PageCounter(ASPObject):
    """"""

    def hits(self, param_page: Optional[Expr] = None, /):
        """"""

    def pagehit(self):
        """"""

    def reset(self, param_page: Optional[Expr] = None, /):
        """"""
