"""Parser for classic ASP code"""

import enum
import sys
import traceback
import typing

import attrs

from . import ParserError, TokenizerError
from .tokenizer import TokenType, Token, Tokenizer


@attrs.define(slots=False)
class Expr:
    """Defined on grammar line 664

    &lt;ImpExpr&gt;
    """


@attrs.define(slots=False)
class ImpExpr(Expr):
    """Defined on grammar line 666

    [ &lt;ImpExpr&gt; 'Imp' ] &lt;EqvExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class EqvExpr(Expr):
    """Defined on grammar line 669

    [ &lt;EqvExpr&gt; 'Eqv' ] &lt;XorExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class XorExpr(Expr):
    """Defined on grammar line 672

    [ &lt;XorExpr&gt; 'Xor' ] &lt;OrExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class OrExpr(Expr):
    """Defined on grammar line 675

    [ &lt;OrExpr&gt; 'Or' ] &lt;AndExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class AndExpr(Expr):
    """Defined on grammar line 678

    [ &lt;AndExpr&gt; 'And' ] &lt;NotExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class NotExpr(Expr):
    """Defined on grammar line 681

    { 'Not' &lt;NotExpr&gt; | &lt;CompareExpr&gt; }
    """

    term: Expr


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class CompareExprType(enum.Enum):
    COMPARE_IS = 0
    COMPARE_ISNOT = 1
    COMPARE_GTEQ = 2
    COMPARE_EQGT = 3
    COMPARE_LTEQ = 4
    COMPARE_EQLT = 5
    COMPARE_GT = 6
    COMPARE_LT = 7
    COMPARE_LTGT = 8
    COMPARE_EQ = 9


@attrs.define(slots=False)
class CompareExpr(Expr):
    """Defined on grammar line 684

    [
        &lt;CompareExpr&gt;
        { 'Is' [ 'Not' ] | '>=' | '=>' | '<=' | '=<' | '>' | '<' | '<>' | '=' }
    ] &lt;ConcatExpr&gt;
    """

    cmp_type: CompareExprType
    left: Expr
    right: Expr


@attrs.define(slots=False)
class ConcatExpr(Expr):
    """Defined on grammar line 696

    [ &lt;ConcatExpr&gt; '&' ] &lt;AddExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class AddExpr(Expr):
    """Defined on grammar line 699

    [ &lt;AddExpr&gt; { '+' | '-' } ] &lt;ModExpr&gt;
    """

    op: Token
    left: Expr
    right: Expr


@attrs.define(slots=False)
class ModExpr(Expr):
    """Defined on grammar line 703

    [ &lt;ModExpr&gt; 'Mod' ] &lt;IntDivExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class IntDivExpr(Expr):
    """Defined on grammar line 706

    [ &lt;IntDivExpr&gt; '\\\\' ] &lt;MultExpr&gt;
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class MultExpr(Expr):
    """Defined on grammar line 709

    [ &lt;MultExpr&gt; { '*' | '/' } ] &lt;UnaryExpr&gt;
    """

    op: Token
    left: Expr
    right: Expr


@attrs.define(slots=False)
class UnaryExpr(Expr):
    """Defined on grammar line 713

    { { '-' | '+' } &lt;UnaryExpr&gt; | &lt;ExpExpr&gt; }
    """

    sign: Token
    term: Expr


@attrs.define(slots=False)
class ExpExpr(Expr):
    """Defined on grammar line 717

    &lt;Value&gt; [ '^' &lt;ExpExpr&gt; ]
    """

    left: Expr
    right: Expr


@attrs.define(slots=False)
class Value(Expr):
    """Defined on grammar line 720

    &lt;ConstExpr&gt; | &lt;LeftExpr&gt; | { '(' &lt;Expr&gt; ')' }
    """


@attrs.define(slots=False)
class ConstExpr(Value):
    """Defined on grammar line 724"""

    const_token: Token


@attrs.define(slots=False)
class BoolLiteral(ConstExpr):
    """Defined on grammar line 731

    'True' | 'False'
    """


@attrs.define(slots=False)
class IntLiteral(ConstExpr):
    """Defined on grammar line 734

    LITERAL_INT | LITERAL_HEX | LITERAL_OCT
    """


@attrs.define(slots=False)
class Nothing(ConstExpr):
    """Defined on grammar line 738

    'Nothing' | 'Null' | 'Empty'
    """


@attrs.define(slots=False)
class ExtendedID:
    """"""

    id_token: Token


@attrs.define(slots=False)
class QualifiedID:
    """"""

    id_tokens: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class IndexOrParams:
    """"""

    expr_list: typing.List[typing.Optional[Expr]] = attrs.field(
        default=attrs.Factory(list)
    )
    dot: bool = attrs.field(default=False, kw_only=True)


@attrs.define(slots=False)
class LeftExprTail:
    """"""

    qual_id_tail: QualifiedID
    index_or_params: typing.List[IndexOrParams] = attrs.field(
        default=attrs.Factory(list)
    )


@attrs.define(slots=False)
class LeftExpr(Value):
    """"""

    qual_id: QualifiedID
    index_or_params: typing.List[IndexOrParams] = attrs.field(
        default=attrs.Factory(list)
    )
    tail: typing.List[LeftExprTail] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
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


@attrs.define(slots=False)
class OptionExplicit(GlobalStmt):
    """Defined on grammar line 393

    'Option' 'Explicit' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class BlockStmt(GlobalStmt):
    """Defined on grammar line 368

    If InlineStmt, must be:
    &lt;InlineStmt&gt; &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class RedimStmt(BlockStmt):
    """Defined on grammar line 539

    'Redim' [ 'Preserve' ] &lt;RedimDeclList&gt; &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class IfStmt(BlockStmt):
    """Defined on grammar line 549

    Two possible definitions:

    'If' &lt;Expr&gt; 'Then' &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; &lt;ElseStmtList&gt; 'End' 'If' &lt;NEWLINE&gt;

    'If' &lt;Expr&gt; 'Then' &lt;InlineStmt&gt; <br />
    [ 'Else' &lt;InlineStmt&gt; ] [ 'End' 'If' ] &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class WithStmt(BlockStmt):
    """Defined on grammar line 566

    'With' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'End' 'With' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class SelectStmt(BlockStmt):
    """Defined on grammar line 588

    'Select' 'Case' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;CaseStmtList&gt; 'End' 'Select' &lt;NEWLINE&gt;
    """


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


@attrs.define(slots=False)
class ForStmt(BlockStmt):
    """Defined on grammar line 580

    Two possible definitions:

    'For' &lt'ExtendedID&gt; '=' &lt;Expr&gt; 'To' &lt;Expr&gt; [ 'Step' &lt;Expr&gt; ] &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;

    'For 'Each' &lt;ExtendedID&gt; 'In' &lt;Expr&gt; &lt;NEWLINE&gt; <br />
    &lt;BlockStmtList&gt; 'Next' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class InlineStmt(BlockStmt):
    """Defined on grammar line 377"""


@attrs.define(slots=False)
class AssignStmt(InlineStmt):
    """Defined on grammar line 404

    Two possible definitions:

    &lt;LeftExpr&gt; '=' &lt;Expr&gt;

    'Set' &lt;LeftExpr&gt; '=' { &lt;Expr&gt; | 'New' &lt;LeftExpr&gt; }
    """


@attrs.define(slots=False)
class CallStmt(InlineStmt):
    """Defined on grammar line 428

    'Call' &lt;LeftExpr&gt;
    """


@attrs.define(slots=False)
class SubCallStmt(InlineStmt):
    """Defined on grammar line 414"""


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


@attrs.define(slots=False)
class MemberDecl:
    """Defined on grammar line 278"""


@attrs.define(slots=False)
class FieldDecl(GlobalStmt, MemberDecl):
    """Defined on grammar line 285

    { 'Private' | 'Public' } &lt;FieldName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class VarName:
    """Defined on grammar line 300

    &lt;ExtendedID&gt; [ '(' &lt;ArrayRankList&gt; ')']

    Where &lt;ArrayRankList&gt; is defined as (line 306):

    [ &lt;IntLiteral&gt; [ ',' &lt;ArrayRankList&gt; ] ]
    """

    extended_id: ExtendedID
    array_rank_list: typing.List[Token] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class VarDecl(MemberDecl, BlockStmt):
    """Defined on grammar line 298

    'Dim' &lt;VarName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;
    """

    var_name: typing.List[VarName] = attrs.field(default=attrs.Factory(list))


@attrs.define(slots=False)
class ConstDecl(GlobalStmt, MemberDecl):
    """Defined on grammar line 310

    [ 'Public' | 'Private' ] 'Const' &lt;ConstList&gt; &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class SubDecl(GlobalStmt, MemberDecl):
    """Defined on grammar line 320

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Sub' &lt;ExtendedID&gt; &lt;MethodArgList&gt; &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Sub' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class FunctionDecl(GlobalStmt, MemberDecl):
    """Defined on grammar line 323

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Function' &lt;ExtendedID&gt; &lt;MethodArgList&gt; &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Function' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class PropertyDecl(MemberDecl):
    """Defined on grammar line 347

    { 'Public' 'Default' | [ 'Public' | 'Private' ] } <br />
    'Property' &lt;PropertyAccessType&gt; &lt;ExtendedID&gt; &lt;MethodArgList&gt; &lt;NEWLINE&gt; <br />
    &lt;MethodStmtList&gt; 'End' 'Property' &lt;NEWLINE&gt;
    """


@attrs.define(slots=False)
class ClassDecl(GlobalStmt):
    """Defined on grammar line 273

    'Class' &lt;ExtendedID&gt; &lt;NEWLINE&gt; <br />
    &lt;MemberDeclList&gt; 'End' 'Class' &lt;NEWLINE&gt;

    Attributes
    ----------
    extended_id : ExtendedID
    member_decl_list : List[MemberDecl], default=[]
    """

    extended_id: ExtendedID
    member_decl_list: typing.List[MemberDecl] = attrs.field(default=attrs.Factory(list))


@attrs.define
class Program:
    """The starting symbol for the VBScript grammar.
    Defined on grammar line 267

    Attributes
    ----------
    global_stmt_list : List[GlobalStmt], default=[]
    """

    global_stmt_list: typing.List[GlobalStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define()
class Parser:
    """"""

    codeblock: str
    suppress_exc: bool = attrs.field(default=True)
    output_file: typing.IO = attrs.field(default=sys.stdout)
    _tkzr: typing.Optional[Tokenizer] = attrs.field(
        default=None, repr=False, init=False
    )
    _pos_tok: typing.Optional[Token] = attrs.field(default=None, repr=False, init=False)

    def __enter__(self) -> typing.Self:
        """"""
        self._tkzr = iter(Tokenizer(self.codeblock))
        # preload first token
        self._pos_tok = next(
            self._tkzr, None
        )  # use next(..., None) instead of handling StopIteration
        return self

    def __exit__(self, exc_type, exc_val, tb) -> bool:
        """"""
        if tb is not None:
            print("Parser exited with an exception!", file=self.output_file)
            print("Exception type:", exc_type, file=self.output_file)
            print("Exception value:", str(exc_val), file=self.output_file)
            print("Traceback:", file=self.output_file)
            traceback.print_tb(tb, file=self.output_file)
        self._pos_tok = None
        self._tkzr = None
        # suppress exception
        return self.suppress_exc

    def _advance_pos(self) -> bool:
        """

        Returns
        -------
        bool
            True if tokenizer is not exhausted
        """
        if self._pos_tok is None:
            # iterator already exhausted, or __enter__() not called yet
            return False
        self._pos_tok = next(self._tkzr, None)
        return self._pos_tok is not None

    def _get_token_code(self, casefold: bool = True) -> str:
        """

        Parameters
        ----------
        casefold : bool, default=True
            Whether token code should be returned as a casefolded string

        Returns
        -------
        str

        Raises
        ------
        RuntimeError
        """
        if self._pos_tok is None:
            raise RuntimeError("Tried to load code for None token")
        tok_code = self.codeblock[self._pos_tok.token_src]
        return tok_code.casefold() if casefold else tok_code

    def _try_token_type(self, tok_type: TokenType) -> bool:
        """Compare the given token type against
        the token type of the current token

        Returns
        -------
        bool
            False if the current token is None or
            the token types do not match
        """
        if self._pos_tok is None:
            return False
        return self._pos_tok.token_type == tok_type

    def _try_safe_keyword_id(self) -> typing.Optional[Token]:
        """

        Returns
        -------
        Token or None
            Token if the current token is a safe keyword identifier,
            otherwise None
        """
        if self._try_token_type(TokenType.IDENTIFIER) and self._get_token_code() in [
            "default",
            "erase",
            "error",
            "explicit",
            "property",
            "step",
        ]:
            return self._pos_tok
        return None

    def _parse_extended_id(self) -> ExtendedID:
        """"""
        if (safe_kw := self._try_safe_keyword_id()) is not None:
            self._advance_pos()  # consume safe keyword
            return ExtendedID(safe_kw)
        if self._try_token_type(TokenType.IDENTIFIER):
            id_token = self._pos_tok
            self._advance_pos()  # consume identifier
            return ExtendedID(id_token)
        raise ParserError(
            "Expected an identifier token for the extended identifier symbol"
        )

    def _try_keyword_id(self) -> typing.Optional[Token]:
        """

        Returns
        -------
        Token or None
            Token if the current token is a keyword identifier,
            otherwise None
        """
        if (safe_kw := self._try_safe_keyword_id()) is not None:
            return safe_kw
        if self._try_token_type(TokenType.IDENTIFIER) and self._get_token_code() in [
            "and",
            "byref",
            "byval",
            "call",
            "case",
            "class",
            "const",
            "dim",
            "do",
            "each",
            "else",
            "elseif",
            "empty",
            "end",
            "eqv",
            "exit",
            "false",
            "for",
            "function",
            "get",
            "goto",
            "if",
            "imp",
            "in",
            "is",
            "let",
            "loop",
            "mod",
            "new",
            "next",
            "not",
            "nothing",
            "null",
            "on",
            "option",
            "or",
            "preserve",
            "private",
            "public",
            "redim",
            "resume",
            "select",
            "set",
            "sub",
            "then",
            "to",
            "true",
            "until",
            "wend",
            "while",
            "with",
            "xor",
        ]:
            return self._pos_tok
        return None

    def _parse_qualified_id_tail(self) -> Token:
        """"""
        if (kw_id := self._try_keyword_id()) is not None:
            self._advance_pos()  # consume keyword identifier
            return kw_id
        if self._try_token_type(TokenType.IDENTIFIER) or self._try_token_type(
            TokenType.IDENTIFIER_IDDOT
        ):
            id_tok = self._pos_tok
            self._advance_pos()  # consume identifier
            return id_tok
        raise ParserError(
            "Expected an identifier or a dotted identifier "
            "in the tail of the qualified identifier symbol"
        )

    def _parse_qualified_id(self) -> QualifiedID:
        """"""
        if self._try_token_type(TokenType.IDENTIFIER_IDDOT) or self._try_token_type(
            TokenType.IDENTIFIER_DOTIDDOT
        ):
            id_tokens: typing.List[Token] = [self._pos_tok]
            self._advance_pos()  # consume identifier
            expand_tail = True
            while expand_tail:
                id_tokens.append(self._parse_qualified_id_tail())
                if id_tokens[-1].token_type != TokenType.IDENTIFIER_IDDOT:
                    expand_tail = False
            return QualifiedID(id_tokens)

        if self._try_token_type(TokenType.IDENTIFIER) or self._try_token_type(
            TokenType.IDENTIFIER_DOTID
        ):
            id_token = self._pos_tok
            self._advance_pos()  # consume identifier
            return QualifiedID([id_token])

        raise ParserError(
            "Expected either an identifier token or a dotted identifier token "
            "for the qualified identifier symbol"
        )

    def _parse_exp_expr(self) -> Expr:
        """"""
        # exp expression expands to the right, use a stack
        expr_stack: typing.List[Expr] = [self._parse_value()]

        # more than one term?
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "^":
            self._advance_pos()  # consume '^'
            expr_stack.append(self._parse_value())

        # combine terms into one expression
        while len(expr_stack) > 1:
            expr_right: Expr = expr_stack.pop()
            expr_left: Expr = expr_stack.pop()
            expr_stack.append(ExpExpr(expr_left, expr_right))
        return expr_stack.pop()

    def _parse_unary_expr(self) -> Expr:
        """"""
        # unary expression expands to the right, use a stack
        sign_stack: typing.List[Token] = []

        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() in "-+":
            sign_stack.append(self._pos_tok)
            self._advance_pos()  # consume sign

        # combine signs into one expression
        ret_expr: Expr = self._parse_exp_expr()
        while len(sign_stack) > 0:
            ret_expr = UnaryExpr(sign_stack.pop(), ret_expr)
        return ret_expr

    def _parse_mult_expr(self) -> Expr:
        """"""
        # mult expression expands to the left, use a queue
        op_queue: typing.List[Token] = []
        expr_queue: typing.List[Expr] = [self._parse_unary_expr()]

        # more than one term?
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() in "*/":
            op_queue.append(self._pos_tok)
            self._advance_pos()  # consume operator
            expr_queue.append(self._parse_unary_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, MultExpr(op_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    def _parse_int_div_expr(self) -> Expr:
        """"""
        # int div expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_mult_expr()]

        # more than one term?
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "\\":
            self._advance_pos()  # consume operator
            expr_queue.append(self._parse_mult_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, IntDivExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_mod_expr(self) -> Expr:
        """"""
        # mod expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_int_div_expr()]

        # more than one term?
        while (
            self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "mod"
        ):
            self._advance_pos()  # consume 'Mod'
            expr_queue.append(self._parse_int_div_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, ModExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_add_expr(self) -> Expr:
        """"""
        # add expression expands to the left, use a queue
        op_queue: typing.List[Token] = []
        expr_queue: typing.List[Expr] = [self._parse_mod_expr()]

        # more than one term?
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() in "+-":
            op_queue.append(self._pos_tok)
            self._advance_pos()  # consume operator
            expr_queue.append(self._parse_mod_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, AddExpr(op_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    def _parse_concat_expr(self) -> Expr:
        """"""
        # concat expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_add_expr()]

        # more than one term?
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "&":
            self._advance_pos()  # consume '&'
            expr_queue.append(self._parse_add_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, ConcatExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_compare_expr(self) -> Expr:
        """"""
        # compare expression expands to the left, use a queue
        cmp_queue: typing.List[CompareExprType] = []
        expr_queue: typing.List[Expr] = [self._parse_concat_expr()]

        # more than one term?
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "is"
        ) or (
            self._try_token_type(TokenType.SYMBOL) and self._get_token_code() in "<>="
        ):
            if (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "is"
            ):
                self._advance_pos()  # consume 'is'
                if (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "not"
                ):
                    self._advance_pos()  # consume 'not'
                    cmp_queue.append(CompareExprType.COMPARE_ISNOT)
                else:
                    cmp_queue.append(CompareExprType.COMPARE_IS)
            elif self._try_token_type(TokenType.SYMBOL):
                if self._get_token_code() == ">":
                    self._advance_pos()  # consume '>'
                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == "="
                    ):
                        self._advance_pos()  # consume '='
                        cmp_queue.append(CompareExprType.COMPARE_GTEQ)
                    else:
                        cmp_queue.append(CompareExprType.COMPARE_GT)
                elif self._get_token_code() == "<":
                    self._advance_pos()  # consume '<'
                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == "="
                    ):
                        self._advance_pos()  # consume '='
                        cmp_queue.append(CompareExprType.COMPARE_LTEQ)
                    elif (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == ">"
                    ):
                        self._advance_pos()  # consume '>'
                        cmp_queue.append(CompareExprType.COMPARE_LTGT)
                    else:
                        cmp_queue.append(CompareExprType.COMPARE_LT)
                elif self._get_token_code() == "=":
                    self._advance_pos()  # consume '='
                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == ">"
                    ):
                        self._advance_pos()  # consume '>'
                        cmp_queue.append(CompareExprType.COMPARE_EQGT)
                    elif (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == "<"
                    ):
                        self._advance_pos()  # consume '<'
                        cmp_queue.append(CompareExprType.COMPARE_EQLT)
                    else:
                        cmp_queue.append(CompareExprType.COMPARE_EQ)
            expr_queue.append(self._parse_concat_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, CompareExpr(cmp_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    def _parse_not_expr(self) -> Expr:
        """"""
        # optimization: "Not Not" is a no-op
        # only use NotExpr when not_counter is odd
        not_counter = 0
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "not"
        ):
            not_counter += 1
            self._advance_pos()  # consume 'Not'

        not_expr = self._parse_compare_expr()
        return NotExpr(not_expr) if not_counter % 2 == 1 else not_expr

    def _parse_and_expr(self) -> Expr:
        """"""
        # and expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_not_expr()]

        # more than one term
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "and"
        ):
            self._advance_pos()  # consume 'And'
            expr_queue.append(self._parse_not_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, AndExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_or_expr(self) -> Expr:
        """"""
        # or expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = []

        # more than one term?
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "or"
        ):
            self._advance_pos()  # consume 'Or'
            expr_queue.append(self._parse_and_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, OrExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_xor_expr(self) -> Expr:
        """"""
        # xor expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_or_expr()]

        # more than one term?
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "xor"
        ):
            self._advance_pos()  # consume 'Xor'
            expr_queue.append(self._parse_or_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, XorExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_eqv_expr(self) -> Expr:
        """"""
        # eqv expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_xor_expr()]

        # more than one term?
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "eqv"
        ):
            self._advance_pos()  # consume 'Eqv'
            expr_queue.append(self._parse_xor_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, EqvExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_imp_expr(self) -> Expr:
        """"""
        # imp expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_eqv_expr()]

        # more than one term?
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "imp"
        ):
            self._advance_pos()  # consume 'Imp'
            expr_queue.append(self._parse_eqv_expr())

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, ImpExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_expr(self) -> Expr:
        """"""
        return self._parse_imp_expr()

    def _parse_const_expr(self) -> ConstExpr:
        """"""
        ret_token = self._pos_tok
        if (
            self._try_token_type(TokenType.LITERAL_FLOAT)
            or self._try_token_type(TokenType.LITERAL_STRING)
            or self._try_token_type(TokenType.LITERAL_DATE)
        ):
            self._advance_pos()  # consume const expression
            return ConstExpr(ret_token)
        if (
            self._try_token_type(TokenType.LITERAL_INT)
            or self._try_token_type(TokenType.LITERAL_HEX)
            or self._try_token_type(TokenType.LITERAL_OCT)
        ):
            self._advance_pos()  # consume int literal expression
            return IntLiteral(ret_token)
        # try to match as identifier
        if self._try_token_type(TokenType.IDENTIFIER):
            match self._get_token_code():
                case "true" | "false":
                    self._advance_pos()  # consume bool literal
                    return BoolLiteral(ret_token)
                case "nothing" | "null" | "empty":
                    self._advance_pos()  # consume nothing symbol
                    return Nothing(ret_token)
                case _:
                    raise ParserError("Invalid identifier in const expression")
        raise ParserError("Invalid token in const expression")

    def _parse_left_expr(self) -> LeftExpr:
        """"""
        # attempt to parse qualified identifier
        try:
            qual_id = self._parse_qualified_id()
        except ParserError as ex:
            raise ParserError(
                "Expected qualified identifier in left expression"
            ) from ex

        # check for index or params list
        index_or_params: typing.List[IndexOrParams] = []
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
            self._advance_pos()  # consume '('
            expr_list: typing.List[typing.Optional[Expr]] = []
            while not (
                self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == ")"
            ):
                if (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ","
                ):
                    self._advance_pos()  # consume ','
                    expr_list.append(None)
                else:
                    # interpret as expression
                    expr_list.append(self._parse_expr())

            if (
                not self._try_token_type(TokenType.SYMBOL)
                or self._get_token_code() != ")"
            ):
                raise ParserError(
                    "Expected closing ')' for index or params list in left expression"
                )
            self._advance_pos()  # consume ')'

            dot = False
            if self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == ".":
                dot = True
                self._advance_pos()  # consume '.'
            index_or_params.append(IndexOrParams(expr_list, dot=dot))
            del dot

        if len(index_or_params) == 0:
            return LeftExpr(qual_id)

        if not index_or_params[-1].dot:
            return LeftExpr(qual_id, index_or_params)

        # TODO: check for left expression tail

    def _parse_value(self) -> Expr:
        """"""
        # value could be expression wrapped in parentheses
        if self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
            self._advance_pos()  # consume '('
            ret_expr = self._parse_expr()
            if (
                not self._try_token_type(TokenType.SYMBOL)
                or self._get_token_code() != ")"
            ):
                raise ParserError("Expected ')' after value expression")
            self._advance_pos()  # consume ')'
            return ret_expr

        # try const expression
        if (
            self._try_token_type(TokenType.LITERAL_INT)
            or self._try_token_type(TokenType.LITERAL_HEX)
            or self._try_token_type(TokenType.LITERAL_OCT)
            or self._try_token_type(TokenType.LITERAL_FLOAT)
            or self._try_token_type(TokenType.LITERAL_STRING)
            or self._try_token_type(TokenType.LITERAL_DATE)
            or (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code()
                in ["true", "false", "nothing", "null", "empty"]
            )
        ):
            return self._parse_const_expr()

        # try left expression
        if self._try_token_type(TokenType.IDENTIFIER):
            return self._parse_left_expr()

        raise ParserError("Invalid token in value expression")

    def _parse_option_explicit(self) -> GlobalStmt:
        """"""
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "option"
        ):
            self._advance_pos()  # consume "option"

            # should have 'Explicit' token
            if (
                not self._try_token_type(TokenType.IDENTIFIER)
                or self._get_token_code() != "explicit"
            ):
                raise ParserError("Missing 'Explicit' after 'Option'")
            self._advance_pos()  # consume "explicit"

            # should be terminated by newline
            if not self._try_token_type(TokenType.NEWLINE):
                raise ParserError("Missing newline after 'Option Explicit'")
            self._advance_pos()  # consume newline
            return OptionExplicit()
        raise ParserError("_parse_option_explicit() did not find 'Option' token")

    def _parse_member_decl(self) -> MemberDecl:
        """"""
        return MemberDecl()

    def _parse_class_decl(self) -> GlobalStmt:
        """"""
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "class"
        ):
            self._advance_pos()  # consume 'Class'
            # should have an extended identifier
            class_id = self._parse_extended_id()
            if not self._try_token_type(TokenType.NEWLINE):
                raise ParserError("Missing newline after class identifier")
            self._advance_pos()  # consume newline

            # member declaration list could be empty
            member_decl_list: typing.List[MemberDecl] = []
            while (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() != "end"
            ):
                member_decl_list.append(self._parse_member_decl())

            if (
                not self._try_token_type(TokenType.IDENTIFIER)
                or self._get_token_code() != "end"
            ):
                raise ParserError("Expected 'End' after class member declaration list")
            self._advance_pos()  # consume 'End'
            if (
                not self._try_token_type(TokenType.IDENTIFIER)
                or self._get_token_code() != "class"
            ):
                raise ParserError("Expected 'Class' after 'End' in class declaration")
            self._advance_pos()  # consume 'Class'
            if not self._try_token_type(TokenType.NEWLINE):
                raise Parser("Missing newline after 'End Class'")
            self._advance_pos()  # consume newline
            return ClassDecl(class_id, member_decl_list)
        raise ParserError("_parse_class_decl() did not find 'Class' token")

    def _parse_const_decl(self) -> GlobalStmt:
        """"""
        return ConstDecl()

    def _parse_sub_decl(self) -> GlobalStmt:
        """"""
        return SubDecl()

    def _parse_function_decl(self) -> GlobalStmt:
        """"""
        return FunctionDecl()

    def _parse_access_modifier(self) -> GlobalStmt:
        """Parse global statement that starts with an access modifier

        Could be one of:
        - FieldDecl
        - ConstDecl
        - SubDecl
        - FunctionDecl

        Returns
        -------
        GlobalStmt
        """
        return GlobalStmt()

    def _parse_global_decl(self) -> GlobalStmt:
        """Parse a global declaration that lacks an access modifier

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        if self._try_token_type(TokenType.IDENTIFIER):
            match self._get_token_code():
                case "class":
                    return self._parse_class_decl()
                case "const":
                    return self._parse_const_decl()
                case "sub":
                    return self._parse_sub_decl()
                case "function":
                    return self._parse_function_decl()
                case _:
                    # shouldn't get here, but just in case
                    raise ParserError(
                        "Invalid identifier at start of global declaration"
                    )
        raise ParserError("Global declaration should start with an identifier")

    def _parse_var_decl(self) -> GlobalStmt:
        """"""
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "dim"
        ):
            raise ParserError("Expected 'Dim' in variable declaration")
        self._advance_pos()  # consume 'Dim'

        var_name: typing.List[VarName] = []
        parse_var_name = True
        while parse_var_name:
            var_id = self._parse_extended_id()
            if self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
                # parse array rank list
                self._advance_pos()  # consume '('
                # first int literal is also optional
                find_int_literal = (
                    self._try_token_type(TokenType.LITERAL_INT)
                    or self._try_token_type(TokenType.LITERAL_HEX)
                    or self._try_token_type(TokenType.LITERAL_OCT)
                )
                int_literals: typing.List[Token] = []
                while find_int_literal:
                    if not (
                        self._try_token_type(TokenType.LITERAL_INT)
                        or self._try_token_type(TokenType.LITERAL_HEX)
                        or self._try_token_type(TokenType.LITERAL_OCT)
                    ):
                        raise ParserError(
                            "Invalid token type found in array rank list of variable name declaration"
                        )
                    int_literals.append(self._pos_tok)
                    self._advance_pos()  # consume int literal

                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == ","
                    ):
                        self._advance_pos()  # consume ','

                    # last int literal is optional, check for ending ')'
                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == ")"
                    ):
                        find_int_literal = False
                # should have an ending ')'
                if (
                    not self._try_token_type(TokenType.SYMBOL)
                    or self._get_token_code() != ")"
                ):
                    raise ParserError(
                        "Expected ending ')' for array rank list of variable name declaration"
                    )
                self._advance_pos()  # consume ')'
                var_name.append(VarName(var_id, int_literals))
                del find_int_literal, int_literals
            else:
                var_name.append(VarName(var_id))

            # another variable name?
            if (
                not self._try_token_type(TokenType.SYMBOL)
                or self._get_token_code() != ","
            ):
                parse_var_name = False
            else:
                self._advance_pos()  # consume ','

        if not self._try_token_type(TokenType.NEWLINE):
            raise ParserError("Variable declaration should be terminated by a newline")
        self._advance_pos()  # consume newline
        return VarDecl(var_name)

    def _parse_redim_stmt(self) -> GlobalStmt:
        """"""
        return RedimStmt()

    def _parse_if_stmt(self) -> GlobalStmt:
        """"""
        return IfStmt()

    def _parse_with_stmt(self) -> GlobalStmt:
        """"""
        return WithStmt()

    def _parse_select_stmt(self) -> GlobalStmt:
        """"""
        return SelectStmt()

    def _parse_loop_stmt(self) -> GlobalStmt:
        """"""
        return LoopStmt()

    def _parse_for_stmt(self) -> GlobalStmt:
        """"""
        return ForStmt()

    def _parse_assign_stmt(self) -> GlobalStmt:
        """"""
        return AssignStmt()

    def _parse_call_stmt(self) -> GlobalStmt:
        """"""
        return CallStmt()

    def _parse_subcall_stmt(self) -> GlobalStmt:
        """"""
        return SubCallStmt()

    def _parse_error_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "on"
        ):
            raise ParserError("Expected 'On' in error statement")
        self._advance_pos()  # consume 'On'

        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "error"
        ):
            raise ParserError("Expected 'Error' after 'On' keyword")
        self._advance_pos()  # consume 'Error'

        if self._try_token_type(TokenType.IDENTIFIER):
            if self._get_token_code() == "resume":
                self._advance_pos()  # consume 'Return'
                if (
                    not self._try_token_type(TokenType.IDENTIFIER)
                    or self._get_token_code() != "next"
                ):
                    raise ParserError("Expected 'Next' after 'On Error Resume'")
                self._advance_pos()  # consume 'Next'
                return ErrorStmt(resume_next=True)
            if self._get_token_code() == "goto":
                self._advance_pos()  # consume 'GoTo'
                if not self._try_token_type(TokenType.LITERAL_INT):
                    raise ParserError(
                        "Expected an integer literal after 'On Error GoTo'"
                    )
                goto_spec = self._pos_tok
                self._advance_pos()  # consume int literal
                return ErrorStmt(goto_spec=goto_spec)
        raise ParserError(
            "Expected either 'Resume Next' or 'GoTo <int>' after 'On Error'"
        )

    def _parse_exit_stmt(self) -> GlobalStmt:
        """"""
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "exit"
        ):
            raise ParserError("Expected 'Exit' in exit statement")
        self._advance_pos()  # consume 'Exit'

        if self._try_token_type(TokenType.IDENTIFIER):
            if self._get_token_code() in ["do", "for", "function", "property", "sub"]:
                exit_tok = self._pos_tok
                self._advance_pos()  # consume exit type token
                return ExitStmt(exit_tok)
            raise ParserError(
                "Invalid identifier found after 'Exit'; "
                "expected one of 'Do', 'For', 'Function', 'Property', or 'Sub'"
            )
        raise ParserError(
            "Expected one of 'Do', 'For', 'Function', "
            "'Property', or 'Sub' after 'Exit'"
        )

    def _parse_erase_stmt(self) -> GlobalStmt:
        """"""
        return EraseStmt()

    def _parse_inline_stmt(self) -> GlobalStmt:
        """"""
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            or self._try_token_type(TokenType.IDENTIFIER_IDDOT)
            or self._try_token_type(TokenType.IDENTIFIER_DOTID)
            or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
        ):
            # AssignStmt and SubCallStmt could start with a dotted identifier
            match self._get_token_code():
                case "call":
                    return self._parse_call_stmt()
                case "on":
                    return self._parse_error_stmt()
                case "exit":
                    return self._parse_exit_stmt()
                case "erase":
                    return self._parse_erase_stmt()

                # try assign statement

                # try subcall statement
            return InlineStmt()
        raise ParserError(
            "Inline statement should start with an identifier or dotted identifier"
        )

    def _parse_block_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            or self._try_token_type(TokenType.IDENTIFIER_IDDOT)
            or self._try_token_type(TokenType.IDENTIFIER_DOTID)
            or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
        ):
            # AssignStmt and SubCallStmt could start with a dotted identifier
            match self._get_token_code():
                case "dim":
                    return self._parse_var_decl()
                case "redim":
                    return self._parse_redim_stmt()
                case "if":
                    return self._parse_if_stmt()
                case "with":
                    return self._parse_with_stmt()
                case "select":
                    return self._parse_select_stmt()
                case "do" | "while":
                    return self._parse_loop_stmt()
                case "for":
                    return self._parse_for_stmt()

            # try to parse as inline statement
            ret_inline = self._parse_inline_stmt()
            if not self._try_token_type(TokenType.NEWLINE):
                raise ParserError(
                    "Inline block statement should be terminated by a newline"
                )
            self._advance_pos()  # consume newline
            return ret_inline
        raise ParserError(
            "Block statement should start with an identifier or dotted identifier"
        )

    def _parse_global_stmt(self) -> GlobalStmt:
        """"""
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            or self._try_token_type(TokenType.IDENTIFIER_IDDOT)
            or self._try_token_type(TokenType.IDENTIFIER_DOTID)
            or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
        ):
            # AssignStmt and SubCallStmt could start with a dotted identifier
            match self._get_token_code():
                case "option":
                    return self._parse_option_explicit()
                case "class" | "const" | "sub" | "function":
                    # does not have an access modifier
                    return self._parse_global_decl()
                case "public" | "private":
                    return self._parse_access_modifier()
                case _:
                    # try to parse as a block statement
                    return self._parse_block_stmt()
        raise ParserError(
            "Global statement should start with an identifier or dotted identifier"
        )

    def parse(self) -> Program:
        """

        Returns
        -------
        Program
        """
        if self._tkzr is None:
            raise RuntimeError("Must use the Parser class within a runtime context!")

        # program may optionally start with a newline token
        if self._try_token_type(TokenType.NEWLINE):
            self._advance_pos()  # consume newline

        global_stmts: typing.List[GlobalStmt] = []
        # don't catch any errors here!
        # if this method is run inside of a context, they will be handled by __exit__()
        while self._pos_tok is not None:
            global_stmts.append(self._parse_global_stmt())
        return Program(global_stmts)
