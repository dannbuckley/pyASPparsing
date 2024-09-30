"""Parser for classic ASP code"""

import sys
import traceback
import typing

import attrs

from . import ParserError, TokenizerError
from .tokenizer import TokenType, Token, Tokenizer


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
class VarDecl(MemberDecl, BlockStmt):
    """Defined on grammar line 298

    'Dim' &lt;VarName&gt; &lt;OtherVarsOpt&gt; &lt;NEWLINE&gt;
    """


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
    member_decl_list : List[MemberDecl], default=[]
    """

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
        """"""
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

    def _parse_class_decl(self) -> GlobalStmt:
        """"""
        return ClassDecl()

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
        return VarDecl()

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
