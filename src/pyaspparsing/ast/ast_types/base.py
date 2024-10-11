"""Base AST types"""

import enum
import attrs

__all__ = [
    "FormatterMixin",
    "AccessModifierType",
    "CompareExprType",
    "Expr",
    "Value",
    "GlobalStmt",
    "MethodStmt",
    "BlockStmt",
    "InlineStmt",
    "MemberDecl",
]


@attrs.define(repr=False, slots=False)
class FormatterMixin:
    def __repr__(self) -> str:
        indent = " " * 2
        repr_lines = [f"{self.__class__.__name__}("]
        num_attrs = len(self.__dict__)
        for i, (attr_name, attr_val) in enumerate(self.__dict__.items()):
            try:
                # check if attr_val is a list
                attr_val_iter = iter(attr_val)
                attr_val_len = len(attr_val)
                if attr_val_len == 0:
                    repr_lines.append(
                        f"{indent}{attr_name}=[]{',' if i < num_attrs - 1 else ''}"
                    )
                    continue
                repr_lines.append(f"{indent}{attr_name}=[")
                # apply repr to each element of attr_val individually
                obj_idx: int = 0
                while (attr_val_obj := next(attr_val_iter, None)) is not None:
                    obj_repr = repr(attr_val_obj).splitlines()
                    if len(obj_repr) > 1:
                        repr_lines.extend(
                            map(lambda x: f"{indent * 2}{x}", obj_repr[:-1])
                        )
                    repr_lines.append(
                        f"{indent * 2}{obj_repr[-1]}{',' if obj_idx < attr_val_len - 1 else ''}"
                    )
                    obj_idx += 1
                    del obj_repr
                repr_lines.append(f"{indent}]{',' if i < num_attrs - 1 else ''}")
            except TypeError:
                # attr_val is not iterable
                attr_repr = repr(attr_val).splitlines()
                repr_lines.append(
                    f"{indent}{attr_name}={attr_repr[0]}{',' if (len(attr_repr) == 1) and (i < num_attrs - 1) else ''}"
                )
                if len(attr_repr) > 1:
                    repr_lines.extend(map(lambda x: f"{indent}{x}", attr_repr[1:-1]))
                    repr_lines.append(
                        f"{indent}{attr_repr[-1]}{',' if i < num_attrs - 1 else ''}"
                    )
                del attr_repr
        repr_lines.append(")")
        return "\n".join(repr_lines)


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class AccessModifierType(enum.Enum):
    """Enumeration of valid access modifiers"""

    PRIVATE = enum.auto()
    PUBLIC = enum.auto()
    # using an enum because PUBLIC DEFAULT is two tokens
    PUBLIC_DEFAULT = enum.auto()


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class CompareExprType(enum.Enum):
    """Enumeration of valid operators that can appear
    in a comparison expresssion (CompareExpr)"""

    COMPARE_IS = enum.auto()
    COMPARE_ISNOT = enum.auto()
    COMPARE_GTEQ = enum.auto()
    COMPARE_EQGT = enum.auto()
    COMPARE_LTEQ = enum.auto()
    COMPARE_EQLT = enum.auto()
    COMPARE_GT = enum.auto()
    COMPARE_LT = enum.auto()
    COMPARE_LTGT = enum.auto()
    COMPARE_EQ = enum.auto()


class Expr:
    """Defined on grammar line 664

    &lt;ImpExpr&gt;
    """


class Value(Expr):
    """Defined on grammar line 720

    &lt;ConstExpr&gt; | &lt;LeftExpr&gt; | { '(' &lt;Expr&gt; ')' }
    """


class GlobalStmt:
    """Defined on grammar line 357

    Could be one of:
    - OptionExplicit
    - ClassDecl
    - FieldDecl
    - ConstDecl
    - SubDecl
    - FunctionDecl
    - BlockStmt
    """


class MethodStmt:
    """Defined on grammar line 365

    &lt;ConstDecl&gt; | &lt;BlockStmt&gt;
    """


class BlockStmt(GlobalStmt, MethodStmt):
    """Defined on grammar line 368

    If InlineStmt, must be:
    &lt;InlineStmt&gt; &lt;NEWLINE&gt;
    """


class InlineStmt(BlockStmt):
    """Defined on grammar line 377"""


class MemberDecl:
    """Defined on grammar line 278"""
