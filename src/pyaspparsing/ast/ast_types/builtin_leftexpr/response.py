"""AST types for Response left expressions"""

from abc import ABCMeta, abstractmethod
import re
import attrs
from ..expressions import LeftExpr


class ValidateResponse(metaclass=ABCMeta):
    """
    Methods
    -------
    validate_response_expr()
    """

    @abstractmethod
    def validate_response_expr(self, is_subcall: bool = False):
        """Validate the response expression structure after
        initialization from an existing left expression object"""


response_expr_types: dict[str, type[LeftExpr | ValidateResponse]] = {}


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
            cls, ValidateResponse
        ), "cls must be a subclass of both LeftExpr and ValidateResponse"
        # validate subclass name against pattern
        assert (
            cls_match := re.match(
                r"Response(?P<subname>[A-Z][a-zA-Z]+)Expr", cls.__name__
            )
        ) is not None, (
            "Subclass name does not match response expression class name pattern"
        )
        # abstract methods must be overriden
        for abc_method in ValidateResponse.__abstractmethods__:
            assert getattr(ValidateResponse, abc_method) != getattr(
                cls, abc_method
            ), "Subclass must override abstract method(s) from ValidateResponse"
        # register response expression type
        response_expr_types[cls_match.groupdict()["subname"].casefold()] = cls

    @staticmethod
    def from_left_expr(left_expr: LeftExpr, *, is_subcall: bool = False):
        """
        Parameters
        ----------
        left_expr : LeftExpr

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
        new_resp.validate_response_expr(is_subcall)
        return new_resp


# ===== COLLECTIONS =====


@attrs.define(repr=False, slots=False)
class ResponseCookiesExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
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
        """"""
        return self.call_args[1]

    @property
    def cookie_key(self):
        """"""
        return self.call_args.get(2, None)

    @property
    def cookie_attribute(self):
        """"""
        return self.subnames.get(2, None)


# ===== PROPERTIES =====


@attrs.define(repr=False, slots=False)
class ResponseBufferExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseCacheControlExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseCharsetExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseContentTypeExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseExpiresExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseExpiresAbsoluteExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseIsClientConnectedExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponsePicsExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseStatusExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


# ===== METHODS =====


@attrs.define(repr=False, slots=False)
class ResponseAddHeaderExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return

    @property
    def param_name(self):
        """"""
        return

    @property
    def param_value(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ResponseAppendToLogExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return

    @property
    def param_string(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ResponseBinaryWriteExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return

    @property
    def param_data(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ResponseClearExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseEndExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseFlushExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return


@attrs.define(repr=False, slots=False)
class ResponseRedirectExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return

    @property
    def param_url(self):
        """"""
        return


@attrs.define(repr=False, slots=False)
class ResponseWriteExpr(ResponseExpr, ValidateResponse):
    """"""

    def validate_response_expr(self, is_subcall: bool = False):
        return

    @property
    def param_variant(self):
        """"""
        return
