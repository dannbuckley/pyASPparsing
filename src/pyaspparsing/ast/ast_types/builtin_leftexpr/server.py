"""AST types for Server left expressions"""

import re
import attrs
from ..expressions import LeftExpr
from .base import ValidateBuiltinLeftExpr

server_expr_types: dict[str, type[LeftExpr | ValidateBuiltinLeftExpr]] = {}


@attrs.define(repr=False, slots=False)
class ServerExpr(LeftExpr):
    """Base class for left expressions that represent Server
    methods, properties, and collections

    Use `ServerExpr.from_left_expr` to wrap a left expression with
    the appropriate subclass

    Methods
    -------
    from_left_expr(left_expr)
    """

    def __init_subclass__(cls, /):
        """Register server expression type under casefolded subname"""
        # validate subclass bases
        assert issubclass(cls, LeftExpr) and issubclass(
            cls, ValidateBuiltinLeftExpr
        ), "cls must be a subclass of both LeftExpr and ValidateBuiltinLeftExpr"
        # validate subclass name against pattern
        assert (
            cls_match := re.match(
                r"Server(?P<subname>[A-Z][a-zA-Z]+)Expr", cls.__name__
            )
        ) is not None, (
            "Subclass name does not match server expression class name pattern"
        )
        # abstract methods must be overriden
        for abc_method in ValidateBuiltinLeftExpr.__abstractmethods__:
            assert getattr(ValidateBuiltinLeftExpr, abc_method) != getattr(
                cls, abc_method
            ), "Subclass must override abstract method(s) from ValidateBuiltinLeftExpr"
        # register server expression type
        server_expr_types[cls_match.groupdict()["subname"].casefold()] = cls

    @staticmethod
    def from_left_expr(left_expr: LeftExpr, *, is_subcall: bool = False):
        """
        Parameters
        ----------
        left_expr : LeftExpr
        is_subcall : bool, default=False

        Returns
        -------
        Subclass of ServerExpr
        """
        assert (
            left_expr.sym_name == "server"
        ), "Symbol name of left expression must match 'server'"
        assert (
            left_expr.end_idx >= 1
            and (subname := left_expr.subnames.get(0, None)) is not None
        ), "First element of left expression must be a subname"
        assert (
            server_type := server_expr_types.get(subname, None)
        ) is not None, "No server expression types match subname"
        # copy left expression data into new server expression
        new_serv = server_type.__new__(server_type)
        left_attr: attrs.Attribute
        for left_attr in LeftExpr.__attrs_attrs__:
            setattr(new_serv, left_attr.name, getattr(left_expr, left_attr.name))
        # ensure left expression matches server expression structure
        new_serv.validate_builtin_expr(is_subcall)
        return new_serv


# ===== PROPERTIES =====


@attrs.define(repr=False, slots=False)
class ServerScriptTimeoutExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert not is_subcall
        assert self.end_idx == 1


# ===== METHODS =====


@attrs.define(repr=False, slots=False)
class ServerCreateObjectExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert (progid := self.call_args.get(1, None)) is not None and len(progid) == 1
        assert self.end_idx == 2

    @property
    def param_progid(self):
        """"""
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ServerExecuteExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert (path := self.call_args.get(1, None)) is not None and len(path) == 1
        assert self.end_idx == 2

    @property
    def param_path(self):
        """"""
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ServerGetLastErrorExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        if self.end_idx == 2:
            assert (cargs := self.call_args.get(1, None)) is not None and len(
                cargs
            ) == 0
        else:
            assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ServerHTMLEncodeExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert (cargs := self.call_args.get(1, None)) is not None and len(cargs) == 1
        assert self.end_idx == 2

    @property
    def param_string(self):
        """"""
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ServerMapPathExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert (path := self.call_args.get(1, None)) is not None and len(path) == 1
        assert self.end_idx == 2

    @property
    def param_path(self):
        """"""
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ServerTransferExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert (path := self.call_args.get(1, None)) is not None and len(path) == 1
        assert self.end_idx == 2

    @property
    def param_path(self):
        """"""
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ServerURLEncodeExpr(ServerExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert (cargs := self.call_args.get(1, None)) is not None and len(cargs) == 1
        assert self.end_idx == 2

    @property
    def param_string(self):
        """"""
        return self.call_args[1][0]
