"""Helper types for ADODB objects"""

from typing import Optional, Any
import attrs
from attrs.validators import deep_mapping, instance_of
from ...ast.ast_types.base import Expr, FormatterMixin


@attrs.define(repr=False, slots=False)
class Database(FormatterMixin):
    """
    Attributes
    ----------
    connectionstring : dict[str, str]
    userid : Expr | None
    password : Expr | None
    options : Expr | None
    """

    connectionstring: dict[str, str] = attrs.field(
        validator=deep_mapping(instance_of(str), instance_of(str))
    )
    userid: Optional[Expr]
    password: Optional[Expr]
    options: Optional[Expr]


@attrs.define(repr=False, slots=False)
class Query(FormatterMixin):
    """
    Attributes
    ----------
    db : int
        ID of existing database connection
    commandtext : Expr
    ra : Expr | None
    options : Expr | None
    """

    db: int = attrs.field(validator=instance_of(int))
    commandtext: Expr
    ra: Optional[Expr]
    options: Optional[Expr]


@attrs.define(repr=False, slots=False)
class RecordField(FormatterMixin):
    """
    Attributes
    ----------
    query : int
        ID of existing database query
    column : Any
    """

    query: int = attrs.field(validator=instance_of(int))
    column: Any
