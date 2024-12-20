"""Code generator state classes"""

from itertools import groupby
from operator import itemgetter
import re
import sys
from typing import Optional, Any, IO

import attrs
from jinja2 import Environment

from ...ast.ast_types import Expr, EvalExpr, ConcatExpr, MethodStmt
from ..linker import Linker
from ..scope import ScopeType, ScopeManager
from ..symbols.symbol import Symbol, FunctionReturnSymbol
from ..symbols.symbol_table import SymbolTable
from ..symbols.functions.function import UserFunction, UserSub
from ..symbols.adodb_base import Database, Query, RecordField


@attrs.define
class FunctionReturnPointer:
    """
    Attributes
    ----------
    call_scope : int
    symbol_name : str
    """

    call_scope: int
    symbol_name: str


@attrs.define
class CodegenState:
    """
    Attributes
    ----------
    jinja_env : jinja2.Environment
    lnk : Linker
    script_file : IO
    template_file : IO
    error_file : IO
    scope_mgr : ScopeManager
    sym_table : SymbolTable
    func_returns : list[tuple[int, str]]

    Methods
    -------
    start_script_block()
        Create a new script output block
    end_script_block()
        End the current script output block
    """

    jinja_env: Environment
    lnk: Linker
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

    _func_returns: list[FunctionReturnPointer] = attrs.field(
        default=attrs.Factory(list), init=False
    )

    output_exprs: dict[int, Expr] = attrs.field(default=attrs.Factory(dict), init=False)
    _curr_output_id: int = attrs.field(default=-1, repr=False, init=False)

    db_cxns: list[Database] = attrs.field(default=attrs.Factory(list), init=False)
    db_queries: list[Query] = attrs.field(default=attrs.Factory(list), init=False)
    db_query_fields: list[RecordField] = attrs.field(
        default=attrs.Factory(list), init=False
    )
    _cxn_to_query: list[tuple[int, int]] = attrs.field(
        default=attrs.Factory(list), repr=False, init=False
    )
    _query_to_field: list[tuple[int, int]] = attrs.field(
        default=attrs.Factory(list), repr=False, init=False
    )

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

    @property
    def function_return_symbols(self) -> list[FunctionReturnSymbol]:
        """List of resolved symbols for function return values

        Returns
        -------
        list[FunctionReturnSymbol]
        """
        return [
            self.sym_table.sym_scopes[ret_pnt.call_scope].sym_table[ret_pnt.symbol_name]
            for ret_pnt in self._func_returns
        ]

    @property
    def have_returned(self) -> bool:
        """True if there are function return values in the state

        Returns
        -------
        bool
        """
        return len(self._func_returns) > 0

    @property
    def database_query_map(self) -> dict[int, set[int]]:
        """Compute a dictionary of {database: {queries from database}} pairs

        Returns
        -------
        dict[int, set[int]]
        """
        return {
            _db: set(map(itemgetter(1), _queries))
            for _db, _queries in groupby(
                sorted(self._cxn_to_query, key=itemgetter(0)), itemgetter(0)
            )
        }

    @property
    def query_field_map(self) -> dict[int, set[int]]:
        """Compute a dictionary of {query: {fields requested from query}} pairs

        Returns
        -------
        dict[int, set[int]]
        """
        return {
            _query: set(map(itemgetter(1), _fields))
            for _query, _fields in groupby(
                sorted(self._query_to_field, key=itemgetter(0)), itemgetter(0)
            )
        }

    def pop_function_return(self):
        """Pop the latest function return symbol from the state"""
        self._func_returns.pop()

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

    def add_user_function_symbol(
        self, func_name: str, arg_names: list[str], func_body: list[MethodStmt]
    ) -> bool:
        """
        Parameters
        ----------
        func_name : str
        arg_names : list[str]
        func_body : list[MethodStmt]

        Returns
        -------
        bool

        Raises
        ------
        AssertionError
        """
        assert (
            self.scope_mgr.scope_registry.nodes[self.scope_mgr.current_scope][
                "scope_type"
            ]
            == ScopeType.SCOPE_FUNCTION_DEFINITION
        ), "Function must be defined within a function definition scope"
        assert (
            len(curr_env := self.scope_mgr.current_environment) >= 2
        ), "Function definition scope must be within an enclosing scope"
        assert isinstance(func_name, str)
        assert isinstance(arg_names, list) and all(
            map(lambda x: isinstance(x, str), arg_names)
        )
        assert isinstance(func_body, list) and all(
            map(lambda x: isinstance(x, MethodStmt), func_body)
        )
        return self.sym_table.add_symbol(
            UserFunction(func_name, self.scope_mgr.current_scope, arg_names, func_body),
            curr_env[-2],
        )

    def add_user_sub_symbol(
        self, sub_name: str, arg_names: list[str], sub_body: list[MethodStmt]
    ) -> bool:
        """
        Parameters
        ----------
        sub_name : str
        arg_names : list[str]
        sub_body : list[MethodStmt]

        Returns
        -------
        bool

        Raises
        ------
        AssertionError
        """
        assert (
            self.scope_mgr.scope_registry.nodes[self.scope_mgr.current_scope][
                "scope_type"
            ]
            == ScopeType.SCOPE_SUB_DEFINITION
        ), "Sub must be defined within a sub definition scope"
        assert (
            len(curr_env := self.scope_mgr.current_environment) >= 2
        ), "Sub definition scope must be within an enclosing scope"
        assert isinstance(sub_name, str)
        assert isinstance(arg_names, list) and all(
            map(lambda x: isinstance(x, str), arg_names)
        )
        assert isinstance(sub_body, list) and all(
            map(lambda x: isinstance(x, MethodStmt), sub_body)
        )
        return self.sym_table.add_symbol(
            UserSub(sub_name, self.scope_mgr.current_scope, arg_names, sub_body),
            curr_env[-2],
        )

    def add_function_return(self, call_scope: int, symbol_name: str):
        """Add a pointer to a function return value

        Parameters
        ----------
        call_scope : int
            The ID of a function call scope
        symbol_name : str
            The name of a `FunctionReturnSymbol` object within `call_scope`

        Raises
        ------
        AssertionError
        """
        assert (
            call_scope in self.scope_mgr.scope_registry
            and self.scope_mgr.scope_registry.nodes[call_scope]["scope_type"]
            == ScopeType.SCOPE_FUNCTION_CALL
        ), "call_scope must point to a function call scope"
        assert (
            (scp_sym := self.sym_table.sym_scopes.get(call_scope, None)) is not None
            and (ret_sym := scp_sym.sym_table.get(symbol_name, None)) is not None
            and isinstance(ret_sym, FunctionReturnSymbol)
        )
        self._func_returns.append(FunctionReturnPointer(call_scope, symbol_name))

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

    def add_database_cxn(
        self,
        connectionstring: dict[str, str],
        userid: Optional[Expr] = None,
        password: Optional[Expr] = None,
        options: Optional[Expr] = None,
    ) -> int:
        """
        Parameters
        ----------
        connectionstring : dict[str, str]
        userid : Expr | None, default=None
        password : Expr | None, default=None
        options : Expr | None, default=None

        Returns
        -------
        int
            ID of new database connection
        """
        self.db_cxns.append(Database(connectionstring, userid, password, options))
        return len(self.db_cxns) - 1

    @staticmethod
    def handle_sql_concat(concat_expr: ConcatExpr) -> tuple[str, list[Expr]]:
        """
        Parameters
        ----------
        concat_expr : ConcatExpr

        Returns
        -------
        tuple[str, list[Expr]]
        """
        if not isinstance(concat_expr, ConcatExpr):
            return ("?", [concat_expr])

        stmt: Optional[EvalExpr] = None
        params: list[Expr] = []

        def _append_stmt(eval_expr: EvalExpr):
            nonlocal stmt
            if stmt is None:
                stmt = eval_expr
            else:
                stmt += eval_expr

        def _handle_expr(child_expr: Expr):
            nonlocal params
            if isinstance(child_expr, EvalExpr):
                _append_stmt(child_expr)
            else:
                params.append(child_expr)
                _append_stmt(EvalExpr("?"))

        def _recursion_helper(_concat_expr: ConcatExpr):
            (
                _recursion_helper
                if isinstance(_concat_expr.left, ConcatExpr)
                else _handle_expr
            )(_concat_expr.left)
            (
                _recursion_helper
                if isinstance(_concat_expr.right, ConcatExpr)
                else _handle_expr
            )(_concat_expr.right)

        _recursion_helper(concat_expr)
        assert stmt is not None and isinstance(
            stmt.expr_value, str
        ), "Expected text in SQL statement, but stmt was None"
        return (re.sub(r"'[?]'", "?", stmt.expr_value).strip(), params)

    def add_database_query(
        self,
        db: int,
        commandtext: Expr,
        ra: Optional[Expr] = None,
        options: Optional[Expr] = None,
    ) -> int:
        """
        Parameters
        ----------
        db : int
            ID of database connection
        commandtext : Expr
        ra : Expr | None, default=None
        options : Expr | None, default=None

        Returns
        -------
        int
            ID of new database query
        """
        try:
            assert 0 <= db < len(self.db_cxns)
            command = (
                (commandtext.expr_value, [])
                if isinstance(commandtext, EvalExpr)
                else CodegenState.handle_sql_concat(commandtext)
            )
            self.db_queries.append(Query(db, *command, ra, options))
            query_id = len(self.db_queries) - 1
            self._cxn_to_query.append((db, query_id))
            return query_id
        except IndexError as ex:
            raise ValueError("Database connection does not exist") from ex

    def add_query_field(self, query: int, column: Any) -> RecordField:
        """
        Parameters
        ----------
        query : int
            ID of database query
        column : Any

        Returns
        -------
        ID of new query field
        """
        try:
            assert 0 <= query < len(self.db_queries)
            self.db_query_fields.append(RecordField(query, column))
            self._query_to_field.append((query, len(self.db_query_fields) - 1))
            return self.db_query_fields[-1]
        except AssertionError as ex:
            raise ValueError("Database query does not exist") from ex

    def start_script_block(self):
        """Create a new script output block"""
        assert not self._in_script_block
        self._in_script_block = True
        self._script_blocks.append(f"__script_block_{len(self._script_blocks)}")
        print(
            self.jinja_env.variable_start_string
            + f"- {self.current_script_block} -"
            + self.jinja_env.variable_end_string,
            end="",  # don't add newline after template variable
            file=self.template_file,
        )
        print(f"START {self.current_script_block}", file=self.script_file)

    def end_script_block(self):
        """End the current script output block"""
        assert self._in_script_block and self.current_script_block is not None
        self._in_script_block = False
        print(f"END {self.current_script_block}\n", file=self.script_file)
