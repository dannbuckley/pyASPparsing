"""AST types for Response left expressions"""

import re
import attrs
from ..expressions import LeftExpr
from .base import ValidateBuiltinLeftExpr


response_expr_types: dict[str, type[LeftExpr | ValidateBuiltinLeftExpr]] = {}


@attrs.define(repr=False, slots=False)
class ResponseExpr(LeftExpr):
    """Base class for left expressions that represent Response
    methods, properties, and collections

    Use `ResponseExpr.from_left_expr` to wrap a left expression with
    the appropriate subclass

    Methods
    -------
    from_left_expr(left_expr)
    """

    def __init_subclass__(cls, /):
        """Register response expression type under casefolded subname"""
        # validate subclass bases
        assert issubclass(cls, LeftExpr) and issubclass(
            cls, ValidateBuiltinLeftExpr
        ), "cls must be a subclass of both LeftExpr and ValidateBuiltinLeftExpr"
        # validate subclass name against pattern
        assert (
            cls_match := re.match(
                r"Response(?P<subname>[A-Z][a-zA-Z]+)Expr", cls.__name__
            )
        ) is not None, (
            "Subclass name does not match response expression class name pattern"
        )
        # abstract methods must be overriden
        for abc_method in ValidateBuiltinLeftExpr.__abstractmethods__:
            assert getattr(ValidateBuiltinLeftExpr, abc_method) != getattr(
                cls, abc_method
            ), "Subclass must override abstract method(s) from ValidateBuiltinLeftExpr"
        # register response expression type
        response_expr_types[cls_match.groupdict()["subname"].casefold()] = cls

    @staticmethod
    def from_left_expr(left_expr: LeftExpr, *, is_subcall: bool = False):
        """
        Parameters
        ----------
        left_expr : LeftExpr
        is_subcall : bool, default=False

        Returns
        -------
        Subclass of ResponseExpr
        """
        assert (
            left_expr.sym_name == "response"
        ), "Symbol name of left expression must match 'response'"
        assert (
            left_expr.end_idx >= 1
            and (subname := left_expr.subnames.get(0, None)) is not None
        ), "First element of left expression must be a subname"
        assert (
            response_type := response_expr_types.get(subname, None)
        ) is not None, "No response expression types match subname"
        # copy left expression data into new response expression
        new_resp = response_type.__new__(response_type)
        left_attr: attrs.Attribute
        for left_attr in LeftExpr.__attrs_attrs__:
            setattr(new_resp, left_attr.name, getattr(left_expr, left_attr.name))
        # ensure left expression matches response expression structure
        new_resp.validate_builtin_expr(is_subcall)
        return new_resp


# ===== COLLECTIONS =====


@attrs.define(repr=False, slots=False)
class ResponseCookiesExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Cookies collection"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert not is_subcall, "Response.Cookies cannot appear in a sub-call statement"
        # name
        assert (name := self.call_args.get(1, None)) is not None and len(name) == 1
        if self.end_idx == 3:
            # optional key or attribute
            assert (
                (key := self.call_args.get(2, None)) is not None and len(key) == 1
            ) or (
                self.subnames.get(2, None)
                in ["domain", "expires", "haskeys", "path", "secure"]
            )
        else:
            assert self.end_idx == 2

    @property
    def cookie_name(self):
        """
        Returns
        -------
        First call argument
        """
        return self.call_args[1][0]

    @property
    def cookie_key(self):
        """
        Returns
        -------
        Second call argument (if available)
        """
        if (key_args := self.call_args.get(2, None)) is not None:
            return key_args[0]
        return None

    @property
    def cookie_attribute(self):
        """
        Returns
        -------
        Cookie attribute if available (last subname after call argument)
        """
        return self.subnames.get(2, None)


# ===== PROPERTIES =====


@attrs.define(repr=False, slots=False)
class ResponseBufferExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Buffer property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseCacheControlExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.CacheControl property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseCharsetExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Charset property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseContentTypeExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.ContentType property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseExpiresExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Expires property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseExpiresAbsoluteExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.ExpiresAbsolute property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseIsClientConnectedExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.IsClientConnected property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponsePICSExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.PICS property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert self.call_args.get(1, None) is not None
        assert self.end_idx == 2


@attrs.define(repr=False, slots=False)
class ResponseStatusExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Status property"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert not is_subcall and self.end_idx == 1


# ===== METHODS =====


@attrs.define(repr=False, slots=False)
class ResponseAddHeaderExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.AddHeaderm method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert (cargs := self.call_args.get(1, None)) is not None and len(cargs) == 2
        assert self.end_idx == 2

    @property
    def param_name(self):
        """
        Returns
        -------
        First call argument
        """
        return self.call_args[1][0]

    @property
    def param_value(self):
        """
        Returns
        -------
        Second call argument
        """
        return self.call_args[1][1]


@attrs.define(repr=False, slots=False)
class ResponseAppendToLogExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.AppendToLog method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert (cargs := self.call_args.get(1, None)) is not None and len(cargs) == 1
        assert self.end_idx == 2

    @property
    def param_string(self):
        """
        Returns
        -------
        First call argument
        """
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ResponseBinaryWriteExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.BinaryWrite method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert (cargs := self.call_args.get(1, None)) is not None and len(cargs) == 1
        assert self.end_idx == 2

    @property
    def param_data(self):
        """
        Returns
        -------
        First call argument
        """
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ResponseClearExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Clear method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        if (cargs := self.call_args.get(1, None)) is not None:
            assert len(cargs) == 0
            assert self.end_idx == 2
        else:
            assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseEndExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.End method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        if (cargs := self.call_args.get(1, None)) is not None:
            assert len(cargs) == 0
            assert self.end_idx == 2
        else:
            assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseFlushExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Flush method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        if (cargs := self.call_args.get(1, None)) is not None:
            assert len(cargs) == 0
            assert self.end_idx == 2
        else:
            assert self.end_idx == 1


@attrs.define(repr=False, slots=False)
class ResponseRedirectExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Redirect method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert (cargs := self.call_args.get(1, None)) is not None and len(cargs) == 1
        assert self.end_idx == 2

    @property
    def param_url(self):
        """
        Returns
        -------
        First call argument
        """
        return self.call_args[1][0]


@attrs.define(repr=False, slots=False)
class ResponseWriteExpr(ResponseExpr, ValidateBuiltinLeftExpr):
    """Response.Write method"""

    def validate_builtin_expr(self, is_subcall: bool = False):
        assert (cargs := self.call_args.get(1, None)) is not None and len(cargs) == 1
        assert self.end_idx == 2

    @property
    def param_variant(self):
        """
        Returns
        -------
        First call argument
        """
        return self.call_args[1][0]
