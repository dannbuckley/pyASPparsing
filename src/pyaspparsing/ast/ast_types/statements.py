"""Statement AST classes"""

import typing

import attrs

from ... import ParserError
from ..tokenizer.token_types import Token, TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import FormatterMixin, GlobalStmt, Expr, BlockStmt, InlineStmt
from .expressions import LeftExpr
from .expression_parser import ExpressionParser


@attrs.define(repr=False, slots=False)
class ExtendedID(FormatterMixin):
    """Extended identifier AST type

    Defined on grammar line 513

    Attributes
    ----------
    id_code : str

    Methods
    -------
    from_tokenizer(tkzr)
    """

    id_code: str = attrs.field(validator=attrs.validators.instance_of(str))

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        ExtendedID
        """
        if (safe_kw := tkzr.try_safe_keyword_id()) is not None:
            tkzr.advance_pos()  # consume safe keyword
            return ExtendedID(tkzr.get_identifier_code(True, tok=safe_kw))
        if tkzr.try_token_type(TokenType.IDENTIFIER):
            id_token = tkzr.current_token
            tkzr.advance_pos()  # consume identifier
            return ExtendedID(tkzr.get_identifier_code(True, tok=id_token))
        raise ParserError(
            "Expected an identifier token for the extended identifier symbol"
        )


@attrs.define(repr=False, slots=False)
class OptionExplicit(FormatterMixin, GlobalStmt):
    """Explicit variable specification AST type

    Defined on grammar line 393

    'Option' 'Explicit' &lt;NEWLINE&gt;

    Methods
    -------
    from_tokenizer(tkzr)
    """

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        OptionExplicit
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "option")
        tkzr.assert_consume(TokenType.IDENTIFIER, "explicit")
        tkzr.assert_newline_or_script_end()
        return OptionExplicit()


@attrs.define(repr=False, slots=False)
class RedimDecl(FormatterMixin):
    """Redefinition declaration AST type

    Defined on grammar line 545

    &lt;ExtendedID&gt; '(' &lt;ExprList&gt; ')'

    Attributes
    ----------
    extended_id : ExtendedID
    expr_list : List[Expr], default=[]
    """

    extended_id: ExtendedID
    expr_list: typing.List[Expr] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class RedimStmt(FormatterMixin, BlockStmt):
    """Redefinition statement AST type

    Defined on grammar line 539

    'Redim' [ 'Preserve' ] &lt;RedimDeclList&gt; &lt;NEWLINE&gt;

    Attributes
    ----------
    redim_decl_list : List[RedimDecl], default=[]
    preserve : bool, default=False

    Methods
    -------
    from_tokenizer(tkzr)
    """

    redim_decl_list: typing.List[RedimDecl] = attrs.field(default=attrs.Factory(list))
    preserve: bool = attrs.field(default=False, kw_only=True)

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        RedimStmt
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "redim")
        preserve = tkzr.try_consume(TokenType.IDENTIFIER, "preserve")
        redim_decl_list: typing.List[RedimDecl] = []
        while not tkzr.try_multiple_token_type(
            [TokenType.NEWLINE, TokenType.DELIM_END]
        ):
            redim_id = ExtendedID.from_tokenizer(tkzr)
            tkzr.assert_consume(TokenType.SYMBOL, "(")
            redim_expr: typing.List[Expr] = []
            while not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ")"
            ):
                redim_expr.append(ExpressionParser.parse_expr(tkzr))
                tkzr.try_consume(TokenType.SYMBOL, ",")
            tkzr.assert_consume(TokenType.SYMBOL, ")")
            redim_decl_list.append(RedimDecl(redim_id, redim_expr))
            tkzr.try_consume(TokenType.SYMBOL, ",")
            del redim_id, redim_expr
        tkzr.assert_newline_or_script_end()
        return RedimStmt(redim_decl_list, preserve=preserve)


@attrs.define(repr=False, slots=False)
class ElseStmt(FormatterMixin):
    """Else statement AST type (part of the 'If' statement)

    Defined on grammar line 552

    Two possible definitions:

    'ElseIf' &lt;Expr&gt; 'Then'
    { &lt;NEWLINE&gt; &lt;BlockStmtList&gt; | &lt;InLineStmt&gt; &lt;NEWLINE&gt; }
    &lt;ElseStmtList&gt;

    'Else'
    { &lt;InlineStmt&gt; &lt;NEWLINE&gt; | &lt;NEWLINE&gt; &lt;BlockStmtList&gt; }

    Attributes
    ----------
    stmt_list : List[BlockStmt], default=[]
    elif_expr : Expr | None, default=None
    is_else : bool, default=False
    """

    stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    elif_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)
    # use bool flag instead of doing a "elif_expr is None" check
    is_else: bool = attrs.field(default=False, kw_only=True)


@attrs.define(repr=False, slots=False)
class IfStmt(FormatterMixin, BlockStmt):
    """If statement AST type

    Defined on grammar line 549

    Two possible definitions:

    'If' &lt;Expr&gt; 'Then' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; &lt;ElseStmtList&gt; 'End' 'If' &lt;NEWLINE&gt;

    'If' &lt;Expr&gt; 'Then' &lt;InlineStmt&gt; <br />
    [ 'Else' &lt;InlineStmt&gt; ] [ 'End' 'If' ] &lt;NEWLINE&gt;

    Attributes
    ----------
    if_expr : Expr
    block_stmt_list : List[BlockStmt], default=[]
    else_stmt_list : List[ElseStmt], default=[]
    """

    if_expr: Expr
    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    else_stmt_list: typing.List[ElseStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class WithStmt(FormatterMixin, BlockStmt):
    """With statement AST type

    Defined on grammar line 566

    'With' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'End' 'With' &lt;NEWLINE&gt;

    Attributes
    ----------
    with_expr : Expr
    block_stmt_list : List[BlockStmt], default=[]
    """

    with_expr: Expr
    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class CaseStmt(FormatterMixin):
    """Case statement AST type (part of the 'Select' statement)

    Defined on grammar line 590

    Two possible definitions:

    'Case' &lt;ExprList&gt; [ &lt;NEWLINE&gt; ] <br />
    &lt;BlockStmtList&gt; &lt;CaseStmtList&gt;

    'Case' 'Else' [ &lt;NEWLINE&gt; ] <br />
    &lt;BlockStmtList&gt;

    Attributes
    ----------
    block_stmt_list : List[BlockStmt], default=[]
    case_expr_list : List[Expr], default=[]
    is_else : bool, default=False
    """

    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    case_expr_list: typing.List[Expr] = attrs.field(default=attrs.Factory(list))
    is_else: bool = attrs.field(default=False, kw_only=True)


@attrs.define(repr=False, slots=False)
class SelectStmt(FormatterMixin, BlockStmt):
    """Select statement AST type

    Defined on grammar line 588

    'Select' 'Case' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;CaseStmtList&gt; 'End' 'Select' &lt;NEWLINE&gt;

    Attributes
    ----------
    select_case_expr : Expr
    case_stmt_list : List[CaseStmt], default=[]
    """

    select_case_expr: Expr
    case_stmt_list: typing.List[CaseStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define(repr=False, slots=False)
class LoopStmt(FormatterMixin, BlockStmt):
    """Loop statement AST type

    Defined on grammar line 570

    Several possible definitions:

    'Do' { 'While' | 'Until' } &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' &lt;NEWLINE&gt;

    'Do' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' { 'While' | 'Until' } &lt;Expr&gt; &lt;NEWLINE&gt;

    'Do' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Loop' &lt;NEWLINE&gt;

    'While' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'WEnd' &lt;NEWLINE&gt;

    Attributes
    ----------
    block_stmt_list : List[BlockStmt], default=[]
    loop_type : Token | None, default=None
    loop_expr : Expr | None, default=None
    """

    block_stmt_list: typing.List[BlockStmt] = attrs.field(default=attrs.Factory(list))
    # 'While' or 'Until'
    loop_type: typing.Optional[Token] = attrs.field(default=None, kw_only=True)
    loop_expr: typing.Optional[Expr] = attrs.field(default=None, kw_only=True)


@attrs.define(repr=False, slots=False)
class ForStmt(FormatterMixin, BlockStmt):
    """For statement AST type

    Defined on grammar line 580

    Two possible definitions:

    'For' &lt'ExtendedID&gt; '=' &lt;Expr&gt; 'To' &lt;Expr&gt;
    [ 'Step' &lt;Expr&gt; ] &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;

    'For 'Each' &lt;ExtendedID&gt; 'In' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;

    Attributes
    ----------
    target_id : ExtendedID
    block_stmt_list : List[BlockStmt], default=[]
    eq_expr : Expr | None, default=None
    to_expr : Expr | None, default=None
    step_expr : Expr | None, default=None
    each_in_expr : Expr | None, default=None
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


@attrs.define(repr=False, slots=False)
class AssignStmt(FormatterMixin, InlineStmt):
    """Assignment statement AST type

    Defined on grammar line 404

    Two possible definitions:

    &lt;LeftExpr&gt; '=' &lt;Expr&gt;

    'Set' &lt;LeftExpr&gt; '=' { &lt;Expr&gt; | 'New' &lt;LeftExpr&gt; }

    Attributes
    ----------
    target_expr : Expr
    assign_expr : Expr
    is_new : bool, default=False

    Methods
    -------
    from_tokenizer(tkzr)
    """

    # left side of '='
    target_expr: LeftExpr
    # right side of '='
    assign_expr: Expr
    is_new: bool = attrs.field(default=False, kw_only=True)

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        AssignStmt
        """
        # 'Set' is optional, don't throw if missing
        tkzr.try_consume(TokenType.IDENTIFIER, "set")
        target_expr = ExpressionParser.parse_left_expr(tkzr)
        # check for '='
        tkzr.assert_consume(TokenType.SYMBOL, "=")
        # check for 'New'
        is_new = tkzr.try_consume(TokenType.IDENTIFIER, "new")
        # parse assignment expression
        assign_expr = (
            ExpressionParser.parse_left_expr(tkzr)
            if is_new
            else ExpressionParser.parse_expr(tkzr)
        )
        return AssignStmt(target_expr, assign_expr, is_new=is_new)


@attrs.define(repr=False, slots=False)
class CallStmt(FormatterMixin, InlineStmt):
    """Function call statement AST type

    Defined on grammar line 428

    'Call' &lt;LeftExpr&gt;

    Attributes
    ----------
    left_expr : LeftExpr

    Methods
    -------
    from_tokenizer(tkzr)
    """

    left_expr: LeftExpr

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        CallStmt
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "call")
        return CallStmt(ExpressionParser.parse_left_expr(tkzr))


@attrs.define(repr=False, slots=False)
class SubCallStmt(FormatterMixin, InlineStmt):
    """Sub-procedure call statement AST type

    Defined on grammar line 414

    Attributes
    ----------
    left_expr : Expr

    Methods
    -------
    from_tokenizer(tkzr, left_expr, ...)
    """

    left_expr: LeftExpr

    @staticmethod
    def from_tokenizer(
        tkzr: Tokenizer,
        left_expr: LeftExpr,
        terminal_type: typing.Optional[TokenType] = None,
        terminal_code: typing.Optional[str] = None,
        terminal_casefold: bool = True,
        *,
        terminal_pairs: typing.Optional[
            typing.List[typing.Tuple[TokenType, typing.Optional[str]]]
        ] = None,
    ):
        """
        Parameters
        ----------
        tkzr : Tokenizer
        left_expr : LeftExpr
        terminal_type : TokenType | None, default=None
        terminal_code : str | None, default=None
        terminal_casefold : bool, default=True
        terminal_pairs : List[Tuple[TokenType, str | None]] | None, default=None

        Returns
        -------
        SubCallStmt
        """
        if terminal_pairs is None:
            terminal_pairs = []
        assert (len(terminal_pairs) > 0) or (
            terminal_type is not None
        ), "Expected at least one terminal type or type/code pair"

        def _check_terminal() -> bool:
            """Check for the terminal token

            Returns
            -------
            bool
                True if the current token is the terminal token
            """
            nonlocal tkzr, terminal_type, terminal_code, terminal_casefold, terminal_pairs
            if len(terminal_pairs) > 0:
                return any(
                    map(
                        lambda tpair: tkzr.try_token_type(tpair[0])
                        and (
                            (tpair[1] is None)
                            or (tkzr.get_token_code(terminal_casefold) == tpair[1])
                        ),
                        terminal_pairs,
                    )
                )
            return tkzr.try_token_type(terminal_type) and (
                (terminal_code is None)
                or (tkzr.get_token_code(terminal_casefold) == terminal_code)
            )

        sub_safe_expr = None
        if left_expr.num_index_or_param == 0 or left_expr.num_tail >= 1:
            # left_expr = <QualifiedID>
            # or (
            #   left_expr = <QualifiedID> <IndexOrParamsList> '.' <LeftExprTail>
            #   or
            #   left_expr = <QualifiedID> <IndexOrParamsListDot> <LeftExprTail>
            # )
            # try to parse sub safe expression
            if not (
                _check_terminal()
                or (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and (tkzr.get_token_code() == ",")
                )
            ):
                sub_safe_expr = ExpressionParser.parse_expr(tkzr, True)
        else:
            # left_expr = <QualifiedID> <IndexOrParamsList>
            # make sure it matches:
            #   <QualifiedID> '(' [ <Expr> ] ')'
            assert (
                left_expr.num_index_or_param == 1
                and 0 <= len(left_expr.call_args[left_expr.end_idx - 1]) <= 1
                and left_expr.num_tail == 0
            ), "Expected left expression to have the form: <QualifiedID> '(' [ <Expr> ] ')'"

        # try to parse comma expression list
        comma_expr_list: typing.List[typing.Optional[Expr]] = []
        found_expr: bool = True  # fix: prevents erroneous None on first iteration
        while not _check_terminal():
            if tkzr.try_consume(TokenType.SYMBOL, ","):
                # was the previous entry not empty?
                if found_expr:
                    found_expr = False
                else:
                    comma_expr_list.append(None)
            else:
                # interpret as expression
                comma_expr_list.append(
                    ExpressionParser.parse_expr(tkzr)
                )  # don't need sub_safe here
                found_expr = True
        # DON'T CONSUME TERMINAL, LEAVE FOR CALLER
        del found_expr

        return SubCallStmt(
            # no additional arguments provided in subcall statement
            left_expr
            if sub_safe_expr is None and len(comma_expr_list) == 0
            else
            # pass additional arguments to left expression
            left_expr(sub_safe_expr, *comma_expr_list)
        )


@attrs.define(repr=False, slots=False)
class ErrorStmt(FormatterMixin, InlineStmt):
    """Error handling specification AST type

    Defined on grammar line 395

    'On' 'Error' { 'Resume' 'Next' | 'GoTo' IntLiteral }

    If 'GoTo' specified, IntLiteral must be 0

    Attributes
    ----------
    resume_next : bool, default=False
    goto_spec : Token | None, default=None

    Methods
    -------
    from_tokenizer(tkzr)
    """

    resume_next: bool = attrs.field(default=False, kw_only=True)
    goto_spec: typing.Optional[Token] = attrs.field(default=None, kw_only=True)

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        ErrorStmt
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "on")
        tkzr.assert_consume(TokenType.IDENTIFIER, "error")
        # check for 'Resume'
        if tkzr.try_consume(TokenType.IDENTIFIER, "resume"):
            tkzr.assert_consume(TokenType.IDENTIFIER, "next")
            return ErrorStmt(resume_next=True)
        # check for 'GoTo'
        if tkzr.try_consume(TokenType.IDENTIFIER, "goto"):
            assert tkzr.try_token_type(
                TokenType.LITERAL_INT
            ), "Expected an integer literal after 'On Error GoTo'"
            goto_spec = tkzr.current_token
            tkzr.advance_pos()  # consume int literal
            return ErrorStmt(goto_spec=goto_spec)
        raise ParserError(
            "Expected either 'Resume Next' or 'GoTo <int>' after 'On Error'"
        )


@attrs.define(repr=False, slots=False)
class ExitStmt(FormatterMixin, InlineStmt):
    """Exit statement AST type

    Defined on grammar line 398

    'Exit' { 'Do' | 'For' | 'Function' | 'Property' | 'Sub' }

    Attributes
    ----------
    exit_token : Token

    Methods
    -------
    from_tokenizer(tkzr)
    """

    exit_token: Token

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        ExitStmt
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "exit")
        assert tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() in [
            "do",
            "for",
            "function",
            "property",
            "sub",
        ], "Invalid token in 'Exit' statement"
        exit_tok = tkzr.current_token
        tkzr.advance_pos()  # consume exit type token
        return ExitStmt(exit_tok)


@attrs.define(repr=False, slots=False)
class EraseStmt(FormatterMixin, InlineStmt):
    """Erase statement AST type

    Part of InlineStmt definition on line 382

    'Erase' &lt;ExtendedID&gt;

    Attributes
    ----------
    extended_id : ExtendedID

    Methods
    -------
    from_tokenizer(tkzr)
    """

    extended_id: ExtendedID

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        EraseStmt
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "erase")
        return EraseStmt(ExtendedID.from_tokenizer(tkzr))
