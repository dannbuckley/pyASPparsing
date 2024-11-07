"""Helper types for ADODB objects"""

from typing import Optional
import attrs
from ....ast.ast_types.base import Expr, FormatterMixin


@attrs.define(repr=False, slots=False)
class Database(FormatterMixin):
    """
    Attributes
    ----------
    connectionstring : Expr
    userid : Expr | None
    password : Expr | None
    options : Expr | None
    """

    connectionstring: Expr
    userid: Optional[Expr]
    password: Optional[Expr]
    options: Optional[Expr]


@attrs.define(repr=False, slots=False)
class Query(FormatterMixin):
    """
    Attributes
    ----------
    db : Database
    commandtext : Expr
    ra : Expr | None
    options : Expr | None
    """

    db: Database
    commandtext: Expr
    ra: Optional[Expr]
    options: Optional[Expr]
