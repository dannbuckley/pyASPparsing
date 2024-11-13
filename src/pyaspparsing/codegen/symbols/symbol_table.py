"""Symbol table"""

from typing import Generator
import attrs
from ...ast.ast_types import AssignStmt, Expr, LeftExpr, EvalExpr
from .symbol import (
    Symbol,
    UnresolvedExternalSymbol,
    ValueSymbol,
    ArraySymbol,
    ASPObject,
)
from .functions.function import ASPFunction


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
        if isinstance((val_sym := self.sym_table[target_expr.sym_name]), ValueSymbol):
            if target_expr.end_idx == 0:
                # simple variable assignment
                # overwrite value with assignment expression
                self[target_expr.sym_name] = ValueSymbol(
                    target_expr.sym_name,
                    assign_expr,
                )
            elif len(target_expr.subnames) > 0 and isinstance(val_sym.value, ASPObject):
                # property assignment
                pass
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
        elif isinstance(self.sym_table[target_expr.sym_name], ASPObject):
            # TODO: establish appropriate assign target (properties?)
            pass


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

    def assign(
        self, asgn: AssignStmt, curr_env: list[int], *, function_sub_body: bool = False
    ):
        """
        Parameters
        ----------
        asgn : AssignStmt
        curr_env : list[int]

        Raises
        ------
        AssertionError
        """
        right_expr = asgn.assign_expr
        if isinstance(right_expr, LeftExpr):
            # try to evaluate expression before assigning to target
            found = False
            for scp in reversed(curr_env):
                if (
                    scp_sym := self.sym_scopes.get(scp, None)
                ) is not None and right_expr.sym_name in scp_sym.sym_table:
                    right_sym = scp_sym.sym_table[right_expr.sym_name]
                    if isinstance(right_sym, ValueSymbol) and isinstance(
                        right_sym.value, ASPObject
                    ):
                        # object created in script
                        right_expr = scp_sym[right_expr.sym_name].value(right_expr)
                    elif isinstance(right_sym, ASPObject):
                        # builtin object
                        right_expr = scp_sym[right_expr.sym_name](right_expr)
                    elif isinstance(right_sym, ASPFunction):
                        # builtin function
                        assert (
                            right_args := right_expr.call_args.get(0, None)
                        ) is not None, (
                            "Function call must have call record in left expression"
                        )
                        right_expr = scp_sym[right_expr.sym_name](*right_args)
                    found = True
                    break
            if not found and not function_sub_body:
                raise ValueError(
                    "Could not find symbol associated with assignment expression"
                )

        left_expr = asgn.target_expr
        for scp in reversed(curr_env):
            if (
                scp_sym := self.sym_scopes.get(scp, None)
            ) is not None and left_expr.sym_name in scp_sym.sym_table:
                scp_sym.assign(left_expr, right_expr)
                return
        # did not find symbol
        if function_sub_body:
            self.add_symbol(UnresolvedExternalSymbol(left_expr.sym_name), curr_env[-1])
            return
        assert (
            not self.option_explicit
        ), "Option Explicit is set, variables must be defined before use"
        # TODO: how to handle subnames of symbol that doesn't exist?
        assert left_expr.end_idx == 0
        self.add_symbol(
            ValueSymbol(left_expr.sym_name, asgn.assign_expr),
            # add new name to the current scope
            curr_env[-1],
        )
        self.sym_scopes[curr_env[-1]].track_assign(left_expr.sym_name)

    def call(
        self,
        left_expr: LeftExpr,
        curr_env: list[int],
        *,
        function_sub_body: bool = False,
    ):
        """
        Parameters
        ----------
        left_expr : LeftExpr
        curr_env : list[int]

        Raises
        ------
        ValueError
        """
        for scp in reversed(curr_env):
            if (scp_sym := self.sym_scopes.get(scp, None)) is not None and (
                call_sym := scp_sym.sym_table.get(left_expr.sym_name, None)
            ) is not None:
                if isinstance(call_sym, ASPObject):
                    # builtin object
                    call_sym(left_expr)
                elif isinstance(call_sym, ValueSymbol) and isinstance(
                    call_sym.value, ASPObject
                ):
                    # object created in script
                    call_sym.value(left_expr)
                elif isinstance(call_sym, ASPFunction):
                    # TODO: symbol is a function?
                    pass
                return
        if not function_sub_body:
            raise ValueError("Invalid symbol name in left_expr")
        # add a placeholder in the current scope
        self.add_symbol(UnresolvedExternalSymbol(left_expr.sym_name), curr_env[-1])
