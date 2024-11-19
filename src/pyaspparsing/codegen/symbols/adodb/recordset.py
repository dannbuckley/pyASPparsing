"""ADODB Recordset object"""

from typing import Optional
import attrs
from ....ast.ast_types.builtin_leftexpr.obj_property import PropertyExpr
from ..asp_object import ASPObject
from ..symbol import prepare_symbol_name, FunctionReturnSymbol
from ...codegen_state import CodegenState
from ...scope import ScopeType


@prepare_symbol_name
@attrs.define(repr=False, slots=False)
class Recordset(ASPObject):
    """
    Attributes
    ----------
    query : Query | None, default=None
    """

    query: Optional[int] = attrs.field(default=None, init=False)

    def handle_property_expr(self, prop_expr: PropertyExpr, cg_state: CodegenState):
        """
        Parameters
        ----------
        prop_expr : PropertyExpr
        cg_state : CodegenState
        """
        assert isinstance(prop_expr, PropertyExpr)
        if prop_expr.assign_value is None:
            left_expr = prop_expr.object_property
            if (
                left_expr.end_idx == 1
                and (cargs := left_expr.call_args.get(0, None)) is not None
            ):
                assert len(cargs) == 1
                assert self.query is not None
                with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
                    cg_state.add_symbol(
                        FunctionReturnSymbol(
                            "fields", cg_state.add_query_field(self.query, cargs[0])
                        )
                    )
                    cg_state.add_function_return(
                        cg_state.scope_mgr.current_scope, "fields"
                    )
            elif (
                left_expr.end_idx == 2
                and (prop_name := left_expr.subnames.get(0, None)) is not None
                and (cargs := left_expr.call_args.get(1, None)) is not None
            ):
                assert prop_name == "fields"
                assert len(cargs) == 1
                assert self.query is not None
                with cg_state.scope_mgr.temporary_scope(ScopeType.SCOPE_FUNCTION_CALL):
                    cg_state.add_symbol(
                        FunctionReturnSymbol(
                            "fields", cg_state.add_query_field(self.query, cargs[0])
                        )
                    )
                    cg_state.add_function_return(
                        cg_state.scope_mgr.current_scope, "fields"
                    )

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
