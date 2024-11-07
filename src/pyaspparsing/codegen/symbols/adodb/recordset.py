"""ADODB Recordset object"""

from typing import Optional
import attrs
from ..symbol import ASPObject, prepare_symbol_name
from .base import Query


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Recordset(ASPObject):
    """"""

    query: Optional[Query] = attrs.field(default=None, init=False)

    def addnew(self, param_fieldlist=None, param_values=None, /):
        """"""

    def cancel(self):
        """"""

    def cancelbatch(self, param_affectrec=None, /):
        """"""

    def cancelupdate(self):
        """"""

    def clone(self, param_locktype=None, /):
        """"""

    def close(self):
        """"""

    def comparebookmarks(self, param_mark1, param_mark2, /):
        """"""

    def delete(self, param_affectrecords, /):
        """"""

    def find(
        self,
        param_criteria,
        param_skiprows=None,
        param_direction=None,
        param_start=None,
        /,
    ):
        """"""

    def getrows(self, param_rows=None, param_start=None, param_fields=None, /):
        """"""

    def getstring(
        self,
        param_format=None,
        param_n=None,
        param_coldel=None,
        param_rowdel=None,
        param_nullexpr=None,
        /,
    ):
        """"""

    def move(self, param_numrec, param_start=None, /):
        """"""

    def movefirst(self):
        """"""

    def movelast(self):
        """"""

    def movenext(self):
        """"""

    def moveprevious(self):
        """"""

    def nextrecordset(self, param_ra=None, /):
        """"""

    def open(
        self,
        param_source=None,
        param_actconn=None,
        param_cursortyp=None,
        param_locktyp=None,
        param_opt=None,
        /,
    ):
        """"""

    def requery(self, param_options=None, /):
        """"""

    def resync(self, param_affectrecords=None, param_resyncvalues=None, /):
        """"""

    def save(self, param_destination=None, param_persistformat=None, /):
        """"""

    def seek(self, param_keyvalues, param_seekoption, /):
        """"""

    def supports(self, param_cursoroptions):
        """"""

    def update(self, param_fields=None, param_values=None, /):
        """"""

    def updatebatch(self, param_affectrecords=None, /):
        """"""
