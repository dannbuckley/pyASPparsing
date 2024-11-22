"""MSWC PageCounter object"""

from typing import Optional
import attrs
from ....ast.ast_types.base import Expr
from ..asp_object import ASPObject
from ..symbol import prepare_symbol_name
from ...generators.codegen_state import CodegenState


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class PageCounter(ASPObject):
    """"""

    def hits(self, cg_state: CodegenState, param_page: Optional[Expr] = None, /):
        """"""

    def pagehit(self, cg_state: CodegenState):
        """"""

    def reset(self, cg_state: CodegenState, param_page: Optional[Expr] = None, /):
        """"""
