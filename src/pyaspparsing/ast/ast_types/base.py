"""Base AST types"""

# pylint: disable=R0903

import enum
import attrs


@attrs.define(repr=False, slots=False)
class FormatterMixin:
    """Pretty-printing formatter mixin for AST types

    Overrides __repr__ and uses the __dict__ of the subclass
    """

    def __repr__(self) -> str:
        if len(self.__dict__) == 0:
            # class has no attributes
            return f"{self.__class__.__name__}()\n"
        indent = " " * 2
        repr_lines = [f"{self.__class__.__name__}("]
        num_attrs = len(self.__dict__)
        for i, (attr_name, attr_val) in enumerate(self.__dict__.items()):
            try:
                if isinstance(attr_val, str):
                    # don't iterate through string
                    raise TypeError
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
                    f"{indent}{attr_name}={attr_repr[0]}"
                    f"{',' if (len(attr_repr) == 1) and (i < num_attrs - 1) else ''}"
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
    COMPARE_LTEQ = enum.auto()
    COMPARE_GT = enum.auto()
    COMPARE_LT = enum.auto()
    COMPARE_LTGT = enum.auto()
    COMPARE_EQ = enum.auto()


class Expr:
    """Expression base class

    Defined on grammar line 664

    &lt;ImpExpr&gt;
    """


class Value(Expr):
    """Value expression base class

    Defined on grammar line 720

    &lt;ConstExpr&gt; | &lt;LeftExpr&gt; | { '(' &lt;Expr&gt; ')' }
    """


class GlobalStmt:
    """Global statement base class

    Defined on grammar line 357

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
    """Method statement base class

    Defined on grammar line 365

    &lt;ConstDecl&gt; | &lt;BlockStmt&gt;
    """


class BlockStmt(GlobalStmt, MethodStmt):
    """Block statement base class

    Defined on grammar line 368

    Could be one of:
    - VarDecl
    - RedimStmt
    - IfStmt
    - WithStmt
    - SelectStmt
    - LoopStmt
    - ForStmt
    - InlineStmt
    """


class InlineStmt(BlockStmt):
    """Inline statement base class

    Defined on grammar line 377

    Could be one of:
    - AssignStmt
    - CallStmt
    - SubCallStmt
    - ErrorStmt
    - ExitStmt
    - EraseStmt
    """


class MemberDecl:
    """Member declaration base class

    Defined on grammar line 278

    Could be one of:
    - FieldDecl
    - VarDecl
    - ConstDecl
    - SubDecl
    - FunctionDecl
    - PropertyDecl
    """
