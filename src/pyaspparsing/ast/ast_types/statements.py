"""Statement AST classes"""

import typing

import attrs

from ..tokenizer.token_types import Token
from .base import GlobalStmt, Expr, BlockStmt, InlineStmt
from .expressions import LeftExpr

__all__ = [
    "ExtendedID",
    "OptionExplicit",
    "RedimDecl",
    "RedimStmt",
    "ElseStmt",
    "IfStmt",
    "WithStmt",
    "CaseStmt",
    "SelectStmt",
    "LoopStmt",
    "ForStmt",
    "AssignStmt",
    "CallStmt",
    "SubCallStmt",
    "ErrorStmt",
    "ExitStmt",
    "EraseStmt",
]


@attrs.define(slots=False)
class ExtendedID:
    """Defined on grammar line 513"""

    id_token: Token


@attrs.define(slots=False)
class OptionExplicit(GlobalStmt):
    """Defined on grammar line 393

    'Option' 'Explicit' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class RedimDecl:
    """Defined on grammar line 545

    &lt;ExtendedID&gt; '(' &lt;ExprList&gt; ')'
    """

    extended_id: ExtendedID
    expr_list: typing.List[Expr] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class RedimStmt(BlockStmt):
    """Defined on grammar line 539

    'Redim' [ 'Preserve' ] &lt;RedimDeclList&gt; &lt;NEWLINE&gt;
    """

    redim_decl_list: typing.List[RedimDecl] = attrs.field(default=attrs.Factory(list))
    preserve: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class ElseStmt:
    """Defined on grammar line 552

    Two possible definitions:

    'ElseIf' &lt;Expr&gt; 'Then'
    { &lt;NEWLINE&gt; &lt;BlockStmtList&gt; | &lt;InLineStmt&gt; &lt;NEWLINE&gt; }
    &lt;ElseStmtList&gt;

    'Else'
    { &lt;InlineStmt&gt; &lt;NEWLINE&gt; | &lt;NEWLINE&gt; &lt;BlockStmtList&gt; }
    """

    stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    elif_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)
    # use bool flag instead of doing a "elif_expr is None" check
    is_else: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class IfStmt(BlockStmt):
    """Defined on grammar line 549

    Two possible definitions:

    'If' &lt;Expr&gt; 'Then' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; &lt;ElseStmtList&gt; 'End' 'If' &lt;NEWLINE&gt;

    'If' &lt;Expr&gt; 'Then' &lt;InlineStmt&gt; <br />
    [ 'Else' &lt;InlineStmt&gt; ] [ 'End' 'If' ] &lt;NEWLINE&gt;
    """

    if_expr: Expr
    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    else_stmt_list: typing.List[ElseStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class WithStmt(BlockStmt):
    """Defined on grammar line 566

    'With' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'End' 'With' &lt;NEWLINE&gt;
    """

    with_expr: Expr
    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class CaseStmt:
    """Defined on grammar line 590

    Two possible definitions:

    'Case' &lt;ExprList&gt; [ &lt;NEWLINE&gt; ] <br />
    &lt;BlockStmtList&gt; &lt;CaseStmtList&gt;

    'Case' 'Else' [ &lt;NEWLINE&gt; ] <br />
    &lt;BlockStmtList&gt;
    """

    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    case_expr_list: typing.List[Expr] = attrs.field(default=attrs.Factory(list))
    is_else: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class SelectStmt(BlockStmt):
    """Defined on grammar line 588

    'Select' 'Case' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;CaseStmtList&gt; 'End' 'Select' &lt;NEWLINE&gt;
    """

    select_case_expr: Expr
    case_stmt_list: typing.List[CaseStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class LoopStmt(BlockStmt):
    """Defined on grammar line 570

    Several possible definitions:

    'Do' { 'While' | 'Until' } &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' &lt;NEWLINE&gt;

    'Do' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' { 'While' | 'Until' } &lt;Expr&gt; &lt;NEWLINE&gt;

    'Do' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' &lt;NEWLINE&gt;

    'While' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'WEnd' &lt;NEWLINE&gt;
    """

    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    # 'While' or 'Until'
    loop_type: typing.Optional[Token] = attrs.field(default=None, kw_only=True)
    loop_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)


@attrs.define(slots=False)
class ForStmt(BlockStmt):
    """Defined on grammar line 580

    Two possible definitions:

    'For' &lt'ExtendedID&gt; '=' &lt;Expr&gt; 'To' &lt;Expr&gt;
    [ 'Step' &lt;Expr&gt; ] &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;

    'For 'Each' &lt;ExtendedID&gt; 'In' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;
    """

    target_id: ExtendedID
    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))

    # 'For' target_id '=' eq_expr 'To' to_expr [ 'Step' step_expr ]
    eq_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)
    to_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)
    step_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)

    # 'For' 'Each' target_id 'In' each_in_expr
    each_in_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)

    def __attrs_post_init__(self):
        """Verify that the for statement is either
        a '=' 'To' type or an 'Each' 'In' type, but not both

        Raises
        ------
        AssertionError
        """
        assert (
            (self.each_in_expr is None)
            and (
                self.eq_expr is not None
                and self.to_expr is not None
                # step_expr is optional
            )
        ) or (
            (self.each_in_expr is not None)
            and (
                self.eq_expr is None and self.to_expr is None and self.step_expr is None
            )
        ), "For statement can only be a '=' 'To' type or an 'Each' 'In' type, but not both"


@attrs.define(slots=False)
class AssignStmt(InlineStmt):
    """Defined on grammar line 404

    Two possible definitions:

    &lt;LeftExpr&gt; '=' &lt;Expr&gt;

    'Set' &lt;LeftExpr&gt; '=' { &lt;Expr&gt; | 'New' &lt;LeftExpr&gt; }
    """

    # left side of '='
    target_expr: Expr
    # right side of '='
    assign_expr: Expr
    is_new: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class CallStmt(InlineStmt):
    """Defined on grammar line 428

    'Call' &lt;LeftExpr&gt;
    """

    left_expr: LeftExpr


@attrs.define(slots=False)
class SubCallStmt(InlineStmt):
    """Defined on grammar line 414"""

    left_expr: Expr
    sub_safe_expr: typing.Optional[Expr] = attrs.field(default=None)
    comma_expr_list: typing.List[typing.Optional[Expr]] = attrs.field(
        default=attrs.Factory(list)
    )


@attrs.define(slots=False)
class ErrorStmt(InlineStmt):
    """Defined on grammar line 395

    'On' 'Error' { 'Resume' 'Next' | 'GoTo' IntLiteral }

    If 'GoTo' specified, IntLiteral must be 0
    """

    resume_next: bool = attrs.field(default=False, kw_only=True)
    goto_spec: typing.Optional[Token] = attrs.field(default=None, kw_only=True)


@attrs.define(slots=False)
class ExitStmt(InlineStmt):
    """Defined on grammar line 398

    'Exit' { 'Do' | 'For' | 'Function' | 'Property' | 'Sub' }
    """

    exit_token: Token


@attrs.define(slots=False)
class EraseStmt(InlineStmt):
    """Part of InlineStmt definition on line 382

    'Erase' &lt;ExtendedID&gt;
    """

    extended_id: ExtendedID
