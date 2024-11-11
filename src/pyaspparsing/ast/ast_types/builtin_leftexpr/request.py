"""AST types for Request left expressions"""

import re
import attrs
from ..expressions import LeftExpr
from .base import ValidateBuiltinLeftExpr


request_expr_types: dict[str, type[LeftExpr | ValidateBuiltinLeftExpr]] = {}


@attrs.define(repr=False, slots=False)
class RequestExpr(LeftExpr):
    """Base class for left expressions that represent Request
    methods, properties, and collections

    Use `RequestExpr.from_left_expr` to wrap a left expression with
    the appropriate subclass

    Methods
    -------
    from_left_expr(left_expr)
    """

    def __init_subclass__(cls, /):
        """Register request expression type under casefolded subname"""
        # validate subclass bases
        assert issubclass(cls, LeftExpr) and issubclass(
            cls, ValidateBuiltinLeftExpr
        ), "cls must be a subclass of both LeftExpr and ValidateBuiltinLeftExpr"
        # validate subclass name against pattern
        assert (
            cls_match := re.match(
                r"Request(?P<subname>[A-Z][a-zA-Z]+)Expr", cls.__name__
            )
        ) is not None, (
            "Subclass name does not match request expression class name pattern"
        )
        # abstract methods must be overriden
        for abc_method in ValidateBuiltinLeftExpr.__abstractmethods__:
            assert getattr(ValidateBuiltinLeftExpr, abc_method) != getattr(
                cls, abc_method
            ), "Subclass must override abstract method(s) from ValidateBuiltinLeftExpr"
        # register request expression type
        request_expr_types[cls_match.groupdict()["subname"].casefold()] = cls

    @staticmethod
    def from_left_expr(left_expr: LeftExpr, *, is_subcall: bool = False):
        """
        Parameters
        ----------
        left_expr : LeftExpr
        is_subcall : bool, default=False

        Returns
        -------
        Subclass of RequestExpr
        """
        assert (
            left_expr.sym_name == "request"
        ), "Symbol name of left expression must match 'request'"
        assert (
            left_expr.end_idx >= 1
        ), "Left expression must have more elements than just the symbol name"
        subname = left_expr.subnames.get(0, "anonymous")
        assert (
            request_type := request_expr_types.get(subname, None)
        ) is not None, "No request expression types match subname"
        # copy left expression data into new request expression
        new_req = request_type.__new__(request_type)
        left_attr: attrs.Attribute
        for left_attr in LeftExpr.__attrs_attrs__:
            setattr(new_req, left_attr.name, getattr(left_expr, left_attr.name))
        # ensure left expression matches request expression structure
        new_req.validate_builtin_expr(is_subcall)
        return new_req


@attrs.define(repr=False, slots=False)
class RequestAnonymousExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """Request expression that accesses a collection
    without specifying the collection name: `Request(variable)`

    The collections are searched in the following order:
    1. QueryString
    2. Form
    3. Cookies
    4. ClientCertificate
    5. ServerVariables
    """

    def validate_builtin_expr(self, is_subcall=False):
        assert not is_subcall


# ===== COLLECTIONS =====


@attrs.define(repr=False, slots=False)
class RequestClientCertificateExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert not is_subcall
        if self.end_idx == 2:
            assert (cargs := self.call_args.get(1, None)) is not None and len(
                cargs
            ) == 1
        else:
            assert self.end_idx == 1

    @property
    def cert_key(self):
        """"""
        if (key_args := self.call_args.get(1, None)) is not None:
            return key_args[0]
        return None


@attrs.define(repr=False, slots=False)
class RequestCookiesExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert not is_subcall
        # name
        assert (name := self.call_args.get(1, None)) is not None and len(name) == 1
        if self.end_idx == 3:
            # optional key or attribute
            assert (
                (key := self.call_args.get(2, None)) is not None and len(key) == 1
            ) or (self.subnames.get(2, None) == "haskeys")
        else:
            assert self.end_idx == 2

    @property
    def cookie_name(self):
        """"""
        return self.call_args[1][0]

    @property
    def cookie_key(self):
        """"""
        if (key_args := self.call_args.get(2, None)) is not None:
            return key_args[0]
        return None

    @property
    def cookie_attribute(self):
        """"""
        return self.subnames.get(2, None)


@attrs.define(repr=False, slots=False)
class RequestFormExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert not is_subcall
        # element
        assert (element := self.call_args.get(1, None)) is not None and len(
            element
        ) == 1
        if self.end_idx == 3:
            # optional index arg or count subname
            assert (
                (index := self.call_args.get(2, None)) is not None and len(index) == 1
            ) or (self.subnames.get(2, None) == "count")
        else:
            assert self.end_idx == 2

    @property
    def element(self):
        """"""
        return self.call_args[1][0]

    @property
    def index(self):
        """"""
        if (index_args := self.call_args.get(2, None)) is not None:
            return index_args[0]
        return None

    @property
    def has_count(self) -> bool:
        """"""
        return self.subnames.get(2, None) == "count"


@attrs.define(repr=False, slots=False)
class RequestQueryStringExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert not is_subcall
        # variable
        assert (variable := self.call_args.get(1, None)) is not None and len(
            variable
        ) == 1
        if self.end_idx == 3:
            # optional index arg or count subname
            assert (
                (index := self.call_args.get(2, None)) is not None and len(index) == 1
            ) or (self.subnames.get(2, None) == "count")
        else:
            assert self.end_idx == 2

    @property
    def variable(self):
        """"""
        return self.call_args[1][0]

    @property
    def index(self):
        """"""
        if (index_args := self.call_args.get(2, None)) is not None:
            return index_args[0]
        return None

    @property
    def has_count(self) -> bool:
        """"""
        return self.subnames.get(2, None) == "count"


@attrs.define(repr=False, slots=False)
class RequestServerVariablesExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert not is_subcall
        if self.end_idx == 2:
            assert (variable := self.call_args.get(1, None)) is not None and len(
                variable
            ) == 1
        else:
            assert self.end_idx == 1

    @property
    def server_variable(self):
        """"""
        if (variable := self.call_args.get(1, None)) is not None:
            return variable[0]
        return None


# ===== PROPERTIES =====


@attrs.define(repr=False, slots=False)
class RequestTotalBytesExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert self.end_idx == 1


# ===== METHODS =====


@attrs.define(repr=False, slots=False)
class RequestBinaryReadExpr(RequestExpr, ValidateBuiltinLeftExpr):
    """"""

    def validate_builtin_expr(self, is_subcall=False):
        assert (count := self.call_args.get(1, None)) is not None and len(count) == 1
        assert self.end_idx == 2

    @property
    def param_count(self):
        """"""
        return self.call_args[1][0]
