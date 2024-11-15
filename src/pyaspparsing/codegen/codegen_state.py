"""Code generator state classes"""

import sys
from typing import Optional, IO

import attrs
from jinja2 import Environment

from ..ast.ast_types import Expr
from .scope import ScopeType, ScopeManager
from .symbols import Response, Request, Server
from .symbols.symbol import Symbol
from .symbols.symbol_table import SymbolTable
from .symbols.functions.function import UserFunction, UserSub
from .symbols.functions import vbscript_builtin as vb_blt


@attrs.define
class CodegenState:
    """
    Attributes
    ----------
    jinja_env : jinja2.Environment
    script_file : IO
    template_file : IO
    error_file : IO
    in_script_block : bool
    current_script_block : str | None

    Methods
    -------
    start_script_block()
        Create a new script output block
    end_script_block()
        End the current script output block
    """

    jinja_env: Environment
    script_file: IO
    template_file: IO
    error_file: IO = attrs.field(default=sys.stderr)
    scope_mgr: ScopeManager = attrs.field(
        default=attrs.Factory(ScopeManager), init=False
    )

    sym_table: SymbolTable = attrs.field(default=attrs.Factory(SymbolTable), init=False)
    _in_script_block: bool = attrs.field(default=False, repr=False, init=False)
    _script_blocks: list[str] = attrs.field(
        default=attrs.Factory(list), repr=False, init=False
    )

    output_exprs: dict[int, Expr] = attrs.field(default=attrs.Factory(dict), init=False)
    _curr_output_id: int = attrs.field(default=-1, repr=False, init=False)

    def __attrs_post_init__(self):
        # initialize script scope with built-in symbols
        self.add_symbol(Response())
        self.add_symbol(Request())
        self.add_symbol(Server())
        for blt in filter(lambda x: x.find("builtin_", 0, 8) == 0, dir(vb_blt)):
            self.add_symbol(getattr(vb_blt, blt)())
        # all script data should be handled in a separate "user" scope
        self.scope_mgr.enter_scope(ScopeType.SCOPE_SCRIPT_USER)

    @property
    def in_script_block(self) -> bool:
        """Flag indicating whether the previous global statement was
        part of a script block (as opposed to a global output block)

        Returns
        -------
        bool
        """
        return self._in_script_block

    @property
    def current_script_block(self) -> Optional[str]:
        """Name of the current script block;
        returns None if no script blocks have been started yet

        Returns
        -------
        str | None
        """
        if len(self._script_blocks) == 0:
            return None
        return self._script_blocks[-1]

    def add_symbol(self, symbol: Symbol) -> bool:
        """Add a new symbol to the symbol table under the current scope

        Parameters
        ----------
        symbol : Symbol

        Returns
        -------
        bool
        """
        return self.sym_table.add_symbol(symbol, self.scope_mgr.current_scope)

    def add_function_symbol(self, func_name: str) -> bool:
        """
        Parameters
        ----------
        func_name : str

        Returns
        -------
        bool
        """
        assert (
            self.scope_mgr.scope_registry.nodes[self.scope_mgr.current_scope][
                "scope_type"
            ]
            == ScopeType.SCOPE_FUNCTION
        )
        assert len(curr_env := self.scope_mgr.current_environment) >= 2
        assert isinstance(func_name, str)
        return self.sym_table.add_symbol(
            UserFunction(func_name, self.scope_mgr.current_scope), curr_env[-2]
        )

    def add_sub_symbol(self, sub_name: str) -> bool:
        """
        Parameters
        ----------
        sub_name : str

        Returns
        -------
        bool
        """
        assert (
            self.scope_mgr.scope_registry.nodes[self.scope_mgr.current_scope][
                "scope_type"
            ]
            == ScopeType.SCOPE_SUB
        )
        assert len(curr_env := self.scope_mgr.current_environment) >= 2
        assert isinstance(sub_name, str)
        return self.sym_table.add_symbol(
            UserSub(sub_name, self.scope_mgr.current_scope), curr_env[-2]
        )

    def add_output_expr(self, output_expr: Expr) -> str:
        """Add a new direct-output expression

        Parameters
        ----------
        output_expr : Expr
            Expression found in an OutputDirective object

        Returns
        -------
        str
            Template-style name for the new expression
        """
        assert isinstance(output_expr, Expr), "output_expr must be a valid expression"
        self._curr_output_id += 1
        self.output_exprs[self._curr_output_id] = output_expr
        return f"__output_expr_{self._curr_output_id}"

    def start_script_block(self):
        """Create a new script output block"""
        assert not self._in_script_block
        self._in_script_block = True
        self._script_blocks.append(f"__script_block_{len(self._script_blocks)}")
        print(
            self.jinja_env.variable_start_string
            + f"- {self.current_script_block} -"
            + self.jinja_env.variable_end_string,
            file=self.template_file,
        )
        print(f"START {self.current_script_block}", file=self.script_file)

    def end_script_block(self):
        """End the current script output block"""
        assert self._in_script_block and self.current_script_block is not None
        self._in_script_block = False
        print(f"END {self.current_script_block}\n", file=self.script_file)
