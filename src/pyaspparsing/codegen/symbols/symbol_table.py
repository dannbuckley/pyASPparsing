"""Symbol table"""

from typing import Optional, Generator, Any
import attrs
from ...ast.ast_types import Expr, LeftExpr, EvalExpr
from .symbol import (
    Symbol,
    ValueSymbol,
    LocalAssignmentSymbol,
    ArraySymbol,
)


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

    def track_assign(self, key: str):
        """
        Parameters
        ----------
        key : str

        Raises
        ------
        ValueError
        """
        if not isinstance(key, str):
            raise ValueError("key must be a string")
        # record assignment for later use
        self._sym_set[key] = self._sym_set.get(key, 0) + 1

    def __setitem__(self, key: str, value: Symbol) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not isinstance(value, Symbol):
            raise TypeError("value must be a subclass of Symbol")
        self.sym_table[key] = value
        self.track_assign(key)

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

    def assign(self, target_expr: LeftExpr, assign_expr: Expr):
        """
        Parameters
        ----------
        target_expr : LeftExpr
        assign_expr : Expr

        Raises
        ------
        AssertionError
        """
        # symbol should already exist, but check just in case
        assert (
            target_expr.sym_name in self.sym_table
        ), "Symbol does not exist in the current scope"
        # what type is the target expression?
        if isinstance(
            (val_sym := self.sym_table[target_expr.sym_name]),
            (ValueSymbol, LocalAssignmentSymbol),
        ):
            if target_expr.end_idx == 0:
                # simple variable assignment
                # overwrite value with assignment expression
                self[target_expr.sym_name] = type(val_sym)(
                    target_expr.sym_name,
                    assign_expr,
                )
            else:
                raise RuntimeError
        elif isinstance(self.sym_table[target_expr.sym_name], ArraySymbol):
            # array item assignment
            def _get_array_idx() -> Generator[int, None, None]:
                """Extract array indices from target expression

                Yields
                ------
                int
                    Array index

                Raises
                ------
                AssertionError
                """
                nonlocal target_expr
                assert (
                    len(target_expr.subnames) == 0
                ), "Target of array assignment cannot have subnames"
                assert (
                    len(target_expr.call_args) == 1
                    and (array_rank := target_expr.call_args.get(0, None)) is not None
                ), "Target of array assignment must have exactly one non-None call record"
                assert (
                    len(array_rank) >= 1
                ), "Call record in array assignment must have at least one value"
                for idx in target_expr.call_args[0]:
                    if isinstance(idx, EvalExpr) and isinstance(idx.expr_value, int):
                        yield idx.expr_value
                    else:
                        # TODO: array index is a left expression
                        yield None

            self.sym_table[target_expr.sym_name].insert(
                tuple(_get_array_idx()), assign_expr
            )


@attrs.define
class ResolvedSymbol:
    """
    Attributes
    ----------
    scope : int
    symbol : Symbol
    """

    scope: int
    symbol: Symbol


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
        """Register the Option Explicit statement with the symbol table

        Raises
        ------
        AssertionError
        """
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

    def copy_scope(self, src_scope: int, dest_scope: int) -> bool:
        """Copy symbols from one scope into another

        Parameters
        ----------
        src_scope : int
            Source scope to copy symbols from
        dest_scope : int
            Destination scope to copy symbols into

        Returns
        -------
        bool
            False if `src_scope` does not exist in the symbol table

        Raises
        ------
        AssertionError
            If a symbol from `src_scope` already exists in `dest_scope`
        """
        if src_scope not in self.sym_scopes:
            return False
        for src_name in self.sym_scopes[src_scope].sym_table:
            assert self.add_symbol(
                self.sym_scopes[src_scope].sym_table[src_name], dest_scope
            ), f"Symbol {src_name} already exists in destination scope"
        return True

    def resolve_symbol(
        self, left_expr: LeftExpr, curr_env: Optional[list[int]] = None
    ) -> list[ResolvedSymbol]:
        """
        Parameters
        ----------
        left_expr : LeftExpr
        curr_env : list[int] | None, default=None
            If None, will search for symbol in all scopes

        Returns
        -------
        list[ResolvedSymbol]
        """
        ret_syms: list[ResolvedSymbol] = []
        if curr_env is None:
            # search for symbol in all scopes
            for scp in self.sym_scopes.keys():
                if (scp_sym := self.sym_scopes.get(scp, None)) is not None and (
                    left_sym := scp_sym.sym_table.get(left_expr.sym_name, None)
                ) is not None:
                    ret_syms.append(ResolvedSymbol(scp, left_sym))
        else:
            # search for symbol in current environment
            assert len(curr_env) > 0, "curr_env must not be empty"
            for scp in curr_env:
                # ^ order of scope resolution doesn't matter since
                # we're searching the entire environment
                if (scp_sym := self.sym_scopes.get(scp, None)) is not None and (
                    left_sym := scp_sym.sym_table.get(left_expr.sym_name, None)
                ) is not None:
                    ret_syms.append(ResolvedSymbol(scp, left_sym))
        return ret_syms

    def try_resolve_args(self, call_args: tuple[Any, ...], curr_env: list[int]):
        """Try to resolve left expressions passed as call arguments

        Parameters
        ----------
        call_args : tuple[Any, ...]
        curr_env : list[int]

        Returns
        -------
        tuple[Any, ...]
            A tuple of the same length as `call_args`
        """

        def _resolve_helper():
            nonlocal self, call_args, curr_env
            for arg in call_args:
                if isinstance(arg, LeftExpr):
                    found = False
                    for scp in reversed(curr_env):
                        if (
                            scp_sym := self.sym_scopes.get(scp, None)
                        ) is not None and arg.sym_name in scp_sym.sym_table:
                            arg_sym = scp_sym.sym_table[arg.sym_name]
                            if isinstance(arg_sym, ValueSymbol):
                                yield arg_sym.value
                            else:
                                yield arg_sym
                            found = True
                            break
                    if found:
                        continue
                # did not find symbol or arg is not a left expression
                yield arg

        return tuple(_resolve_helper())
