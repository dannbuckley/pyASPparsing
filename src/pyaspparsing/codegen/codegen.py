"""codegen module"""

import sys
import typing
import attrs
from ..ast.tokenizer.state_machine import Tokenizer
from ..ast.ast_types import *
from .linker import Linker, generate_linked_program
from .symbols import SymbolTable, ValueSymbol, ArraySymbol, Response, Request, Server
from .symbols.functions import vbscript_builtin as vb_blt


@attrs.define(slots=False)
class Codegen:
    """
    Attributes
    ----------
    sym_table : SymbolTable
    lnk : Linker
    """

    sym_table: SymbolTable = attrs.field(default=attrs.Factory(SymbolTable), init=False)
    lnk: Linker = attrs.field(default=attrs.Factory(Linker), init=False)

    def __attrs_post_init__(self):
        self.sym_table.add_symbol(Response())
        self.sym_table.add_symbol(Request())
        self.sym_table.add_symbol(Server())
        for blt in filter(lambda x: x.find("builtin_", 0, 8) == 0, dir(vb_blt)):
            self.sym_table.add_symbol(getattr(vb_blt, blt)())

    def consume_program(
        self,
        codeblock: str,
        suppress_exc: bool = True,
        output_file: typing.IO = sys.stdout,
    ):
        """
        Parameters
        ----------
        codeblock : str
        suppress_exc : bool, default=True
        output_file : IO, default=sys.stdout
        """
        with Tokenizer(codeblock, suppress_exc, output_file) as tkzr:
            for glob_st in generate_linked_program(tkzr, self.lnk):
                if isinstance(glob_st, OptionExplicit):
                    self.sym_table.set_explicit()
                elif isinstance(glob_st, VarDecl):
                    for var_name in glob_st.var_name:
                        self.sym_table.add_symbol(
                            ValueSymbol.from_var_name(var_name)
                            if len(var_name.array_rank_list) == 0
                            else ArraySymbol.from_var_name(var_name)
                        )
                elif isinstance(glob_st, AssignStmt):
                    self.sym_table.assign(glob_st)
                else:
                    print(type(glob_st))
