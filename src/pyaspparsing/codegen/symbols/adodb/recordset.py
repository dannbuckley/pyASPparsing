"""ADODB Recordset object"""

from typing import Optional
import attrs
from ..asp_object import ASPObject
from ..symbol import prepare_symbol_name
from .base import Query
from ...codegen_state import CodegenState


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Recordset(ASPObject):
    """"""

    query: Optional[Query] = attrs.field(default=None, init=False)

    def addnew(
        self, cg_state: CodegenState, param_fieldlist=None, param_values=None, /
    ):
        """"""

    def cancel(self, cg_state: CodegenState):
        """"""

    def cancelbatch(self, cg_state: CodegenState, param_affectrec=None, /):
        """"""

    def cancelupdate(self, cg_state: CodegenState):
        """"""

    def clone(self, cg_state: CodegenState, param_locktype=None, /):
        """"""

    def close(self, cg_state: CodegenState):
        """"""

    def comparebookmarks(self, cg_state: CodegenState, param_mark1, param_mark2, /):
        """"""

    def delete(self, cg_state: CodegenState, param_affectrecords, /):
        """"""

    def find(
        self,
        cg_state: CodegenState,
        param_criteria,
        param_skiprows=None,
        param_direction=None,
        param_start=None,
        /,
    ):
        """"""

    def getrows(
        self,
        cg_state: CodegenState,
        param_rows=None,
        param_start=None,
        param_fields=None,
        /,
    ):
        """"""

    def getstring(
        self,
        cg_state: CodegenState,
        param_format=None,
        param_n=None,
        param_coldel=None,
        param_rowdel=None,
        param_nullexpr=None,
        /,
    ):
        """"""

    def move(self, cg_state: CodegenState, param_numrec, param_start=None, /):
        """"""

    def movefirst(self, cg_state: CodegenState):
        """"""

    def movelast(self, cg_state: CodegenState):
        """"""

    def movenext(self, cg_state: CodegenState):
        """"""

    def moveprevious(self, cg_state: CodegenState):
        """"""

    def nextrecordset(self, cg_state: CodegenState, param_ra=None, /):
        """"""

    def open(
        self,
        cg_state: CodegenState,
        param_source=None,
        param_actconn=None,
        param_cursortyp=None,
        param_locktyp=None,
        param_opt=None,
        /,
    ):
        """"""

    def requery(self, cg_state: CodegenState, param_options=None, /):
        """"""

    def resync(
        self,
        cg_state: CodegenState,
        param_affectrecords=None,
        param_resyncvalues=None,
        /,
    ):
        """"""

    def save(
        self,
        cg_state: CodegenState,
        param_destination=None,
        param_persistformat=None,
        /,
    ):
        """"""

    def seek(self, cg_state: CodegenState, param_keyvalues, param_seekoption, /):
        """"""

    def supports(self, cg_state: CodegenState, param_cursoroptions):
        """"""

    def update(self, cg_state: CodegenState, param_fields=None, param_values=None, /):
        """"""

    def updatebatch(self, cg_state: CodegenState, param_affectrecords=None, /):
        """"""
