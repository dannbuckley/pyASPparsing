"""Symbol table"""

import attrs
from ...ast.ast_types import AssignStmt, LeftExpr
from .symbol import Symbol


@attrs.define
class SymbolScope:
    """
    Attributes
    ----------
    sym_table : dict[str, Symbol], default={}

    Methods
    -------
    add_symbol(symbol)
    assign(asgn)
    call(left_expr)
    """

    sym_table: dict[str, Symbol] = attrs.field(default=attrs.Factory(dict), init=False)

    # how many times has the symbol been retrieved?
    _sym_get: dict[str, int] = attrs.field(
        default=attrs.Factory(dict), repr=False, init=False
    )
    # how many times has the symbol been assigned to?
    _sym_set: dict[str, int] = attrs.field(
        default=attrs.Factory(dict), repr=False, init=False
    )

    def __getitem__(self, key: str) -> Symbol:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        # don't catch KeyError
        ret = self.sym_table[key]
        # record retrieval for later use
        self._sym_get[key] = self._sym_get.get(key, 0) + 1
        return ret

    def __setitem__(self, key: str, value: Symbol) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not isinstance(value, Symbol):
            raise TypeError("value must be a subclass of Symbol")
        self.sym_table[key] = value
        # record assignment for later use
        self._sym_set[key] = self._sym_set.get(key, 0) + 1

    def add_symbol(self, symbol: Symbol) -> bool:
        """Add a new symbol to the symbol table

        Does nothing if the name already exists

        Parameters
        ----------
        symbol : Symbol

        Returns
        -------
        bool
            False if name already exists
        """
        if symbol.symbol_name in self.sym_table:
            return False
        # don't track this as assignment
        self.sym_table[symbol.symbol_name] = symbol
        return True

    def assign(self, asgn: AssignStmt):
        """"""

    def call(self, left_expr: LeftExpr):
        """"""


@attrs.define
class SymbolTable:
    """
    Attributes
    ----------
    sym_scopes : dict[int, SymbolScope], default={}
    option_explicit : bool, default=False

    Methods
    -------
    set_explicit()
    add_symbol(symbol, scope)
    """

    sym_scopes: dict[int, SymbolScope] = attrs.field(
        default=attrs.Factory(dict), init=False
    )
    option_explicit: bool = attrs.field(default=False, init=False)

    def set_explicit(self):
        """Register the Option Explicit statement with the symbol table"""
        assert not self.option_explicit, "Option Explicit can only be set once"
        self.option_explicit = True

    def add_symbol(self, symbol: Symbol, scope: int) -> bool:
        """Add a new symbol under the given scope

        Parameters
        ----------
        symbol : Symbol
        scope : int
        """
        if not scope in self.sym_scopes:
            self.sym_scopes[scope] = SymbolScope()
        return self.sym_scopes[scope].add_symbol(symbol)
