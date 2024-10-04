"""Parser for classic ASP code"""

import sys
import traceback
import typing

import attrs

from . import ParserError, TokenizerError
from .tokenizer import TokenType, Token, Tokenizer
from .ast_types import *


@attrs.define()
class Parser:
    """Identify symbols within a codeblock and construct an abstract syntax tree

    This class should be used within a context manager

    Attributes
    ----------
    codeblock : str
    suppress_exc : bool
        If True, `__exit__()` will suppress exceptions
    output_file : IO
    """

    codeblock: str
    suppress_exc: bool = attrs.field(default=True)
    output_file: typing.IO = attrs.field(default=sys.stdout)
    _tkzr: typing.Optional[Tokenizer] = attrs.field(
        default=None, repr=False, init=False
    )
    _pos_tok: typing.Optional[Token] = attrs.field(default=None, repr=False, init=False)

    def __enter__(self) -> typing.Self:
        """

        Returns
        -------
        Self
        """
        self._tkzr = iter(Tokenizer(self.codeblock))
        # preload first token
        self._pos_tok = next(
            self._tkzr, None
        )  # use next(..., None) instead of handling StopIteration
        return self

    def __exit__(self, exc_type, exc_val: BaseException, tb) -> bool:
        """

        Parameters
        ----------
        exc_type
        exc_val
        tb

        Returns
        -------
        `self.suppress_exc` : bool
            True if exceptions will be suppressed
        """
        if tb is not None:
            print("Parser exited with an exception!", file=self.output_file)
            print("Current token:", self._pos_tok, file=self.output_file)
            print(
                "Current token code:",
                repr(self._get_token_code(False)) if not self._pos_tok is None else "",
                file=self.output_file,
            )
            print("Exception type:", exc_type, file=self.output_file)
            print("Exception value:", str(exc_val), file=self.output_file)
            caused_by = exc_val.__cause__
            while caused_by is not None:
                print("Caused by:", file=self.output_file)
                print(
                    "\tException type:",
                    repr(type(exc_val.__cause__)),
                    file=self.output_file,
                )
                print(
                    "\tException value:", str(exc_val.__cause__), file=self.output_file
                )
                caused_by = caused_by.__cause__
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

    def _assert_consume(
        self,
        tok_type: TokenType,
        tok_code: typing.Optional[str] = None,
        *,
        casefold: bool = True,
    ) -> None:
        """Attempt to consume a specific token.
        Raises on failure

        Parameters
        ----------
        tok_type : TokenType
        tok_code : str
            Source code to use when comparing against current token
        casefold : bool, default=True
            Whether tok_code is casefolded. Passed to _get_token_code()

        Raises
        ------
        AssertionError
        """
        # _try_token_type() is also an existence check, will return False if token is None
        if tok_type is None:
            raise ValueError("tok_type must be a valid TokenType")
        if tok_code is None:
            assert self._try_token_type(
                tok_type
            ), f"Expected token of type {repr(tok_type)} and value {repr(tok_code)}"
        else:
            assert (
                self._try_token_type(tok_type)
                and self._get_token_code(casefold) == tok_code
            ), f"Expected token of type {repr(tok_type)} and value {repr(tok_code)}"
        self._advance_pos()  # consume

    def _try_consume(
        self,
        tok_type: TokenType,
        tok_code: str,
        *,
        casefold: bool = True,
        use_in: bool = False,
    ) -> bool:
        """Attempt to consume a specific optional token.
        Does not raise on failure

        Parameters
        ----------
        tok_type : TokenType
        tok_code : str
            Source code to use when comparing against current token
        casefold : bool, default=True
            Whether tok_code is casefolded. Passed to _get_token_code()
        use_in : bool, default=False
            If True, will use "_get_token_code() in tok_code";
            otherwise "_get_token_code() == tok_code"

        Returns
        -------
        bool
            True if token was consumed
        """
        try:
            curr_code: str = self._get_token_code(casefold)
        except RuntimeError:
            return False
        if not (
            self._try_token_type(tok_type)
            and (
                (not use_in and (curr_code == tok_code))
                or (use_in and (curr_code in tok_code))
            )
        ):
            return False
        self._advance_pos()  # consume
        return True

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
        """

        Returns
        -------
        ExtendedID

        Raises
        ------
        ParserError
        """
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
        """

        Returns
        -------
        Token

        Raises
        ------
        ParserError
        """
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
        """

        Returns
        -------
        QualifiedID

        Raises
        ------
        ParserError
        """
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

    def _parse_exp_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # exp expression expands to the right, use a stack
        expr_stack: typing.List[Expr] = [self._parse_value(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.SYMBOL, "^"):
            expr_stack.append(self._parse_value(sub_safe))

        # combine terms into one expression
        while len(expr_stack) > 1:
            expr_right: Expr = expr_stack.pop()
            expr_left: Expr = expr_stack.pop()
            expr_stack.append(ExpExpr(expr_left, expr_right))
        return expr_stack.pop()

    def _parse_unary_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # unary expression expands to the right, use a stack
        sign_stack: typing.List[Token] = []

        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() in "-+":
            sign_stack.append(self._pos_tok)
            self._advance_pos()  # consume sign

        # combine signs into one expression
        ret_expr: Expr = self._parse_exp_expr(sub_safe)
        while len(sign_stack) > 0:
            ret_expr = UnaryExpr(sign_stack.pop(), ret_expr)
        return ret_expr

    def _parse_mult_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # mult expression expands to the left, use a queue
        op_queue: typing.List[Token] = []
        expr_queue: typing.List[Expr] = [self._parse_unary_expr(sub_safe)]

        # more than one term?
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() in "*/":
            op_queue.append(self._pos_tok)
            self._advance_pos()  # consume operator
            expr_queue.append(self._parse_unary_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, MultExpr(op_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    def _parse_int_div_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # int div expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_mult_expr(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.SYMBOL, "\\"):
            expr_queue.append(self._parse_mult_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, IntDivExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_mod_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # mod expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_int_div_expr(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.IDENTIFIER, "mod"):
            expr_queue.append(self._parse_int_div_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, ModExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_add_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # add expression expands to the left, use a queue
        op_queue: typing.List[Token] = []
        expr_queue: typing.List[Expr] = [self._parse_mod_expr(sub_safe)]

        # more than one term?
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() in "+-":
            op_queue.append(self._pos_tok)
            self._advance_pos()  # consume operator
            expr_queue.append(self._parse_mod_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, AddExpr(op_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    def _parse_concat_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # concat expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_add_expr(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.SYMBOL, "&"):
            expr_queue.append(self._parse_add_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, ConcatExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_compare_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # compare expression expands to the left, use a queue
        cmp_queue: typing.List[CompareExprType] = []
        expr_queue: typing.List[Expr] = [self._parse_concat_expr(sub_safe)]

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
            expr_queue.append(self._parse_concat_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, CompareExpr(cmp_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    def _parse_not_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # optimization: "Not Not" is a no-op
        # only use NotExpr when not_counter is odd
        not_counter = 0
        while self._try_consume(TokenType.IDENTIFIER, "not"):
            not_counter += 1

        not_expr = self._parse_compare_expr(sub_safe)
        return NotExpr(not_expr) if not_counter % 2 == 1 else not_expr

    def _parse_and_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # and expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_not_expr(sub_safe)]

        # more than one term
        while self._try_consume(TokenType.IDENTIFIER, "and"):
            expr_queue.append(self._parse_not_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, AndExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_or_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # or expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_and_expr(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.IDENTIFIER, "or"):
            expr_queue.append(self._parse_and_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, OrExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_xor_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # xor expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_or_expr(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.IDENTIFIER, "xor"):
            expr_queue.append(self._parse_or_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, XorExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_eqv_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # eqv expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_xor_expr(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.IDENTIFIER, "eqv"):
            expr_queue.append(self._parse_xor_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, EqvExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_imp_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        # imp expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_eqv_expr(sub_safe)]

        # more than one term?
        while self._try_consume(TokenType.IDENTIFIER, "imp"):
            expr_queue.append(self._parse_eqv_expr(sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            expr_queue.insert(0, ImpExpr(expr_left, expr_right))
        return expr_queue.pop()

    def _parse_expr(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr
        """
        return self._parse_imp_expr(sub_safe)

    def _parse_const_expr(self) -> ConstExpr:
        """

        Returns
        -------
        ConstExpr

        Raises
        ------
        ParserError
        """
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
        """

        Returns
        -------
        LeftExpr

        Raises
        ------
        ParserError
        """
        # attempt to parse qualified identifier
        try:
            qual_id = self._parse_qualified_id()
        except ParserError as ex:
            raise ParserError(
                "Expected qualified identifier in left expression"
            ) from ex

        # check for index or params list
        index_or_params: typing.List[IndexOrParams] = []
        while self._try_consume(TokenType.SYMBOL, "("):
            expr_list: typing.List[typing.Optional[Expr]] = []
            found_expr: bool = False  # helper variable for parsing commas
            while not (
                self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == ")"
            ):
                if (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ","
                ):
                    self._advance_pos()  # consume ','
                    # was the previous entry not empty?
                    if found_expr:
                        found_expr = False
                    else:
                        expr_list.append(None)
                else:
                    # interpret as expression
                    expr_list.append(self._parse_expr())
                    found_expr = True
            del found_expr

            try:
                self._assert_consume(TokenType.SYMBOL, ")")
            except AssertionError as ex:
                raise ParserError("An error occurred in _parse_left_expr()") from ex

            dot = self._try_token_type(
                TokenType.IDENTIFIER_DOTID
            ) or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
            index_or_params.append(IndexOrParams(expr_list, dot=dot))
            del dot, expr_list

        if len(index_or_params) == 0:
            return LeftExpr(qual_id)

        if not index_or_params[-1].dot:
            return LeftExpr(qual_id, index_or_params)

        # check for left expression tail
        left_expr_tail: typing.List[LeftExprTail] = []
        parse_tail: bool = True
        while parse_tail:
            qual_id_tail: QualifiedID = self._parse_qualified_id()

            # check for index or params list
            index_or_params_tail: typing.List[IndexOrParams] = []
            while self._try_consume(TokenType.SYMBOL, "("):
                expr_list: typing.List[Expr] = []
                found_expr: bool = False  # helper variable for parsing commas
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == ","
                    ):
                        self._advance_pos()  # consume ','
                        # was the previous entry not empty?
                        if found_expr:
                            found_expr = False
                        else:
                            expr_list.append(None)
                    else:
                        # interpret as expression
                        expr_list.append(self._parse_expr())
                        found_expr = True
                del found_expr

                try:
                    self._assert_consume(TokenType.SYMBOL, ")")
                except AssertionError as ex:
                    raise ParserError("An error occurred in _parse_left_expr()") from ex

                dot = self._try_token_type(
                    TokenType.IDENTIFIER_DOTID
                ) or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
                index_or_params_tail.append(IndexOrParams(expr_list, dot=dot))
                del dot, expr_list

            left_expr_tail.append(LeftExprTail(qual_id_tail, index_or_params_tail))

            # continue if this left expression tail contained a dotted "index or params" list
            parse_tail = (len(index_or_params_tail) > 0) and index_or_params_tail[
                -1
            ].dot
            del index_or_params_tail
        return LeftExpr(qual_id, index_or_params, left_expr_tail)

    def _parse_value(self, sub_safe: bool = False) -> Expr:
        """
        Parameters
        ----------
        sub_safe : bool, default=False
            If True, disallow expressions that are wrapped in parentheses

        Returns
        -------
        Expr

        Raises
        ------
        ParserError
        """
        if not sub_safe:
            # value could be expression wrapped in parentheses
            if self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
                self._advance_pos()  # consume '('
                ret_expr = self._parse_expr()
                try:
                    self._assert_consume(TokenType.SYMBOL, ")")
                except AssertionError as ex:
                    raise ParserError("An error occurred in _parse_value()") from ex
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
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "option")
            self._assert_consume(TokenType.IDENTIFIER, "explicit")
            self._assert_consume(TokenType.NEWLINE)
            return OptionExplicit()
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_option_explicit()") from ex

    def _parse_member_decl(self) -> MemberDecl:
        """
        Could be one of:
        - FieldDecl
        - VarDecl
        - ConstDecl
        - SubDecl
        - FunctionDecl
        - PropertyDecl
        """
        try:
            if (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "dim"
            ):
                return self._parse_var_decl()

            # identify access modifier
            access_mod: typing.Optional[AccessModifierType] = None
            if self._try_consume(TokenType.IDENTIFIER, "public"):
                if self._try_consume(TokenType.IDENTIFIER, "default"):
                    access_mod = AccessModifierType.PUBLIC_DEFAULT
                else:
                    access_mod = AccessModifierType.PUBLIC
            elif self._try_consume(TokenType.IDENTIFIER, "private"):
                access_mod = AccessModifierType.PRIVATE

            # must have identifier after access modifier
            assert self._try_token_type(
                TokenType.IDENTIFIER
            ), "Member declaration must start with an identifier token"

            # check for other declaration types
            match self._get_token_code():
                case "const":
                    assert (
                        access_mod != AccessModifierType.PUBLIC_DEFAULT
                    ), "'Public Default' access modifier cannot be used with const declaration"
                    return self._parse_const_decl(access_mod)
                case "sub":
                    return self._parse_sub_decl(access_mod)
                case "function":
                    return self._parse_function_decl(access_mod)
                case "property":
                    return self._parse_property_decl(access_mod)

            # assume this is a field declaration
            assert (
                access_mod is not None
            ), "Expected access modifier in field declaration"
            return self._parse_field_decl(access_mod)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_member_decl()") from ex

    def _parse_class_decl(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "class")
            class_id = self._parse_extended_id()
            self._assert_consume(TokenType.NEWLINE)

            # member declaration list could be empty
            member_decl_list: typing.List[MemberDecl] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                member_decl_list.append(self._parse_member_decl())

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "class")
            self._assert_consume(TokenType.NEWLINE)
            return ClassDecl(class_id, member_decl_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_class_decl()") from ex

    def _parse_field_decl(self, access_mod: AccessModifierType) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            # if access_mod == AccessModifierType.PUBLIC_DEFAULT:
            # raise ParserError(
            #     "'Public Default' access modifier cannot be used with field declaration"
            # )
            assert (
                access_mod != AccessModifierType.PUBLIC_DEFAULT
            ), "'Public Default' access modifier cannot be used with field declaration"

            # did not match token, parse as a field declaration
            if not self._try_token_type(TokenType.IDENTIFIER):
                raise ParserError("Expected field name identifier in field declaration")
            field_id: FieldID = FieldID(self._pos_tok)
            self._advance_pos()  # consume identifier

            int_literals: typing.List[Token] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                find_int_literal = (
                    self._try_token_type(TokenType.LITERAL_INT)
                    or self._try_token_type(TokenType.LITERAL_HEX)
                    or self._try_token_type(TokenType.LITERAL_OCT)
                )
                while find_int_literal:
                    if not (
                        self._try_token_type(TokenType.LITERAL_INT)
                        or self._try_token_type(TokenType.LITERAL_HEX)
                        or self._try_token_type(TokenType.LITERAL_OCT)
                    ):
                        raise ParserError(
                            "Invalid token type found in array rank list "
                            "of field name declaration"
                        )
                    int_literals.append(self._pos_tok)
                    self._advance_pos()  # consume int literal

                    self._try_consume(TokenType.SYMBOL, ",")

                    # last int literal is optional, check for ending ')'
                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == ")"
                    ):
                        find_int_literal = False
                # should have an ending ')'
                self._assert_consume(TokenType.SYMBOL, ")")
                del find_int_literal
            field_name: FieldName = FieldName(field_id, int_literals)
            del int_literals

            # prepare for other vars
            self._try_consume(TokenType.SYMBOL, ",")

            other_vars: typing.List[VarName] = []
            parse_var_name = self._try_token_type(TokenType.IDENTIFIER)
            while parse_var_name:
                var_id = self._parse_extended_id()
                if self._try_consume(TokenType.SYMBOL, "("):
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
                                "Invalid token type found in array rank list "
                                "of variable name declaration (part of field declaration)"
                            )
                        int_literals.append(self._pos_tok)
                        self._advance_pos()  # consume int literal

                        self._try_consume(TokenType.SYMBOL, ",")

                        # last int literal is optional, check for ending ')'
                        if (
                            self._try_token_type(TokenType.SYMBOL)
                            and self._get_token_code() == ")"
                        ):
                            find_int_literal = False
                    # should have and ending ')'
                    self._assert_consume(TokenType.SYMBOL, ")")
                    other_vars.append(VarName(var_id, int_literals))
                    del find_int_literal, int_literals
                else:
                    other_vars.append(VarName(var_id))

                # another variable name?
                if (
                    not self._try_token_type(TokenType.SYMBOL)
                    or self._get_token_code() != ","
                ):
                    parse_var_name = False
                else:
                    self._advance_pos()  # consume ','

            self._assert_consume(TokenType.NEWLINE)
            return FieldDecl(field_name, other_vars, access_mod=access_mod)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_field_decl()") from ex

    def _parse_const_decl(
        self, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "const")
            const_list: typing.List[ConstListItem] = []
            while not self._try_token_type(TokenType.NEWLINE):
                const_id = self._parse_extended_id()
                self._assert_consume(TokenType.SYMBOL, "=")
                const_expr: typing.Optional[Expr] = None
                num_paren: int = 0
                # signs expand to the right, use a stack
                sign_stack: typing.List[Token] = []
                while not (
                    self._try_token_type(TokenType.NEWLINE)
                    or (
                        self._try_token_type(TokenType.SYMBOL)
                        and (self._get_token_code() == ",")
                    )
                ):
                    if self._try_consume(TokenType.SYMBOL, "("):
                        num_paren += 1
                    elif (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() in "-+"
                    ):
                        sign_stack.append(self._pos_tok)
                        self._advance_pos()  # consume
                    elif (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() in ")"
                    ):
                        assert (
                            const_expr is not None
                        ), "Expected const expression before ')' in const list item"
                        break
                    else:
                        assert (
                            const_expr is None
                        ), "Can only have one const expression per const list item"
                        const_expr = self._parse_const_expr()
                assert (
                    const_expr is not None
                ), "Expected const expression in const list item"

                # verify correct number of closing parentheses
                while num_paren > 0:
                    self._assert_consume(TokenType.SYMBOL, ")")
                    num_paren -= 1

                # combine signs into one expression
                while len(sign_stack) > 0:
                    const_expr = UnaryExpr(sign_stack.pop(), const_expr)
                const_list.append(ConstListItem(const_id, const_expr))
                del const_id, const_expr, num_paren, sign_stack

                # advance to next item
                self._try_consume(TokenType.SYMBOL, ",")
            self._assert_consume(TokenType.NEWLINE)
            return ConstDecl(const_list, access_mod=access_mod)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_const_decl()") from ex

    def _parse_sub_decl(
        self, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "sub")
            sub_id: ExtendedID = self._parse_extended_id()
            method_arg_list: typing.List[Arg] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    if self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in ["byval", "byref"]:
                        arg_modifier = self._pos_tok
                        self._advance_pos()  # consume modifier
                    else:
                        arg_modifier = None
                    arg_id = self._parse_extended_id()
                    has_paren = self._try_consume(TokenType.SYMBOL, "(")
                    if has_paren:
                        self._assert_consume(TokenType.SYMBOL, ")")
                    method_arg_list.append(
                        Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                    )

                    self._try_consume(TokenType.SYMBOL, ",")
                self._assert_consume(TokenType.SYMBOL, ")")

            method_stmt_list: typing.List[MethodStmt] = []
            if self._try_token_type(TokenType.NEWLINE):
                self._advance_pos()  # consume newline
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "end"
                ):
                    method_stmt_list.append(self._parse_method_stmt())
            else:
                method_stmt_list.append(
                    self._parse_inline_stmt(TokenType.IDENTIFIER, "end")
                )

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "sub")
            self._assert_consume(TokenType.NEWLINE)
            return SubDecl(
                sub_id, method_arg_list, method_stmt_list, access_mod=access_mod
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_sub_decl()") from ex

    def _parse_function_decl(
        self, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "function")
            function_id: ExtendedID = self._parse_extended_id()
            method_arg_list: typing.List[Arg] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    if self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in ["byval", "byref"]:
                        arg_modifier = self._pos_tok
                        self._advance_pos()  # consume modifier
                    else:
                        arg_modifier = None
                    arg_id = self._parse_extended_id()
                    has_paren = self._try_consume(TokenType.SYMBOL, "(")
                    if has_paren:
                        self._assert_consume(TokenType.SYMBOL, ")")
                    method_arg_list.append(
                        Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                    )

                    self._try_consume(TokenType.SYMBOL, ",")
                self._assert_consume(TokenType.SYMBOL, ")")

            method_stmt_list: typing.List[MethodStmt] = []
            if self._try_token_type(TokenType.NEWLINE):
                self._advance_pos()  # consume newline
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "end"
                ):
                    method_stmt_list.append(self._parse_method_stmt())
            else:
                method_stmt_list.append(
                    self._parse_inline_stmt(TokenType.IDENTIFIER, "end")
                )

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "function")
            self._assert_consume(TokenType.NEWLINE)
            return FunctionDecl(
                function_id, method_arg_list, method_stmt_list, access_mod=access_mod
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_function_decl()") from ex

    def _parse_property_decl(
        self, access_mod: typing.Optional[AccessModifierType] = None
    ) -> MemberDecl:
        """

        Returns
        -------
        MemberDecl

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "property")

            assert self._try_token_type(TokenType.IDENTIFIER) and (
                self._get_token_code() in ["get", "let", "set"]
            ), "Expected property access type after 'Property'"
            prop_access_type: Token = self._pos_tok
            self._advance_pos()  # consume access type

            property_id: ExtendedID = self._parse_extended_id()

            method_arg_list: typing.List[Arg] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    if self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in ["byval", "byref"]:
                        arg_modifier = self._pos_tok
                        self._advance_pos()  # consume modifier
                    else:
                        arg_modifier = None
                    arg_id = self._parse_extended_id()
                    has_paren = self._try_consume(TokenType.SYMBOL, "(")
                    if has_paren:
                        self._assert_consume(TokenType.SYMBOL, ")")
                    method_arg_list.append(
                        Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                    )
                    self._try_consume(TokenType.SYMBOL, ",")
                self._assert_consume(TokenType.SYMBOL, ")")

            # property declaration requires newline after arg list
            self._assert_consume(TokenType.NEWLINE)

            method_stmt_list: typing.List[MethodStmt] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                method_stmt_list.append(self._parse_method_stmt())

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "property")
            self._assert_consume(TokenType.NEWLINE)
            return PropertyDecl(
                prop_access_type,
                property_id,
                method_arg_list,
                method_stmt_list,
                access_mod=access_mod,
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_property_decl()") from ex

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

        Raises
        ------
        ParserError
        """
        if self._try_token_type(TokenType.IDENTIFIER):
            try:
                # identify access modifier
                if self._try_consume(TokenType.IDENTIFIER, "public"):
                    if self._try_consume(TokenType.IDENTIFIER, "default"):
                        access_mod = AccessModifierType.PUBLIC_DEFAULT
                    else:
                        access_mod = AccessModifierType.PUBLIC
                elif self._try_consume(TokenType.IDENTIFIER, "private"):
                    access_mod = AccessModifierType.PRIVATE

                # must have identifier after access modifier
                assert self._try_token_type(
                    TokenType.IDENTIFIER
                ), "Expected an identifier token after access modifier"

                # check for other declaration types
                match self._get_token_code():
                    case "const":
                        # cannot use 'Default' with const declaration
                        assert (
                            access_mod != AccessModifierType.PUBLIC_DEFAULT
                        ), "'Public Default' access modifier cannot be used with const declaration"
                        return self._parse_const_decl(access_mod)
                    case "sub":
                        return self._parse_sub_decl(access_mod)
                    case "function":
                        return self._parse_function_decl(access_mod)

                # assume this is a field declaration
                return self._parse_field_decl(access_mod)
            except AssertionError as ex:
                raise ParserError(
                    "An error occurred in _parse_access_modifier()"
                ) from ex
        raise ParserError("Expected a 'Public' or 'Private' access modifier token")

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
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "dim")
            var_name: typing.List[VarName] = []
            parse_var_name = True
            while parse_var_name:
                var_id = self._parse_extended_id()
                if self._try_consume(TokenType.SYMBOL, "("):
                    # parse array rank list
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
                                "Invalid token type found in array rank list "
                                "of variable name declaration"
                            )
                        int_literals.append(self._pos_tok)
                        self._advance_pos()  # consume int literal

                        self._try_consume(TokenType.SYMBOL, ",")

                        # last int literal is optional, check for ending ')'
                        if (
                            self._try_token_type(TokenType.SYMBOL)
                            and self._get_token_code() == ")"
                        ):
                            find_int_literal = False
                    # should have an ending ')'
                    self._assert_consume(TokenType.SYMBOL, ")")
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

            self._assert_consume(TokenType.NEWLINE)
            return VarDecl(var_name)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_var_decl()") from ex

    def _parse_redim_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "redim")
            preserve = self._try_consume(TokenType.IDENTIFIER, "preserve")
            redim_decl_list: typing.List[RedimDecl] = []
            while not self._try_token_type(TokenType.NEWLINE):
                redim_id = self._parse_extended_id()
                self._assert_consume(TokenType.SYMBOL, "(")
                redim_expr: typing.List[Expr] = []
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    redim_expr.append(self._parse_expr())
                    self._try_consume(TokenType.SYMBOL, ",")
                self._assert_consume(TokenType.SYMBOL, ")")
                redim_decl_list.append(RedimDecl(redim_id, redim_expr))
                self._try_consume(TokenType.SYMBOL, ",")
            self._assert_consume(TokenType.NEWLINE)
            return RedimStmt(redim_decl_list, preserve=preserve)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_redim_stmt()") from ex

    def _parse_if_stmt(self) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "if")
            if_expr = self._parse_expr()
            self._assert_consume(TokenType.IDENTIFIER, "then")

            block_stmt_list: typing.List[BlockStmt] = []
            else_stmt_list: typing.List[ElseStmt] = []
            if self._try_token_type(TokenType.NEWLINE):
                self._advance_pos()  # consume newline
                # block statement list
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() in ["elseif", "else", "end"]
                ):
                    block_stmt_list.append(self._parse_block_stmt())
                # check for 'ElseIf' statements
                if (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "elseif"
                ):
                    while not (
                        self._try_token_type(TokenType.IDENTIFIER)
                        and self._get_token_code() in ["else", "end"]
                    ):
                        elif_stmt_list: typing.List[BlockStmt] = []
                        self._assert_consume(TokenType.IDENTIFIER, "elseif")
                        elif_expr: Expr = self._parse_expr()
                        self._assert_consume(TokenType.IDENTIFIER, "then")
                        if self._try_token_type(TokenType.NEWLINE):
                            self._advance_pos()  # consume newline
                            # block statement list
                            while not (
                                self._try_token_type(TokenType.IDENTIFIER)
                                and self._get_token_code() in ["elseif", "else", "end"]
                            ):
                                elif_stmt_list.append(self._parse_block_stmt())
                        else:
                            # inline statement
                            elif_stmt_list.append(
                                self._parse_inline_stmt(TokenType.NEWLINE)
                            )
                            self._assert_consume(TokenType.NEWLINE)
                        else_stmt_list.append(
                            ElseStmt(elif_stmt_list, elif_expr=elif_expr)
                        )
                        del elif_expr, elif_stmt_list
                # check for 'Else' statement
                if self._try_consume(TokenType.IDENTIFIER, "else"):
                    else_block_list: typing.List[BlockStmt] = []
                    if self._try_token_type(TokenType.NEWLINE):
                        self._advance_pos()  # consume newline
                        # block statement list
                        while not (
                            self._try_token_type(TokenType.IDENTIFIER)
                            and self._get_token_code() == "end"
                        ):
                            else_block_list.append(self._parse_block_stmt())
                    else:
                        # inline statement
                        else_block_list.append(
                            self._parse_inline_stmt(TokenType.NEWLINE)
                        )
                        self._assert_consume(TokenType.NEWLINE)
                    else_stmt_list.append(ElseStmt(else_block_list, is_else=True))
                    del else_block_list
                # finish if statement
                self._assert_consume(TokenType.IDENTIFIER, "end")
                self._assert_consume(TokenType.IDENTIFIER, "if")
                self._assert_consume(TokenType.NEWLINE)
            else:
                # inline statement
                block_stmt_list.append(
                    self._parse_inline_stmt(
                        terminal_pairs=[
                            (
                                TokenType.IDENTIFIER,
                                "else",
                            ),  # optional 'Else' <InlineStmt>
                            (TokenType.IDENTIFIER, "end"),  # optional 'End' 'If'
                            (TokenType.NEWLINE),  # if statement terminator
                        ]
                    )
                )
                # check for 'Else' statement
                if self._try_consume(TokenType.IDENTIFIER, "else"):
                    else_stmt_list.append(
                        ElseStmt(
                            [
                                self._parse_inline_stmt(
                                    terminal_pairs=[
                                        (
                                            TokenType.IDENTIFIER,
                                            "end",
                                        ),  # optional 'End' 'If'
                                        (TokenType.NEWLINE),  # if statement terminator
                                    ]
                                )
                            ],
                            is_else=True,
                        )
                    )
                # check for 'End' 'If'
                if self._try_consume(TokenType.IDENTIFIER, "end"):
                    self._assert_consume(TokenType.IDENTIFIER, "if")
                # finish if statement
                self._assert_consume(TokenType.NEWLINE)

            return IfStmt(if_expr, block_stmt_list, else_stmt_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_if_stmt()") from ex

    def _parse_with_stmt(self) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "with")
            with_expr = self._parse_expr()
            self._assert_consume(TokenType.NEWLINE)
            block_stmt_list: typing.List[BlockStmt] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                block_stmt_list.append(self._parse_block_stmt())
            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "with")
            self._assert_consume(TokenType.NEWLINE)
            return WithStmt(with_expr, block_stmt_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_with_stmt()") from ex

    def _parse_select_stmt(self) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "select")
            self._assert_consume(TokenType.IDENTIFIER, "case")
            select_case_expr = self._parse_expr()
            self._assert_consume(TokenType.NEWLINE)
            case_stmt_list: typing.List[CaseStmt] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                self._assert_consume(TokenType.IDENTIFIER, "case")
                is_else: bool = self._try_consume(TokenType.IDENTIFIER, "else")
                case_expr_list: typing.List[Expr] = []
                if not is_else:
                    # parse expression list
                    parse_case_expr: bool = True
                    while parse_case_expr:
                        case_expr_list.append(self._parse_expr())
                        parse_case_expr = self._try_consume(TokenType.SYMBOL, ",")
                    del parse_case_expr
                # check for optional newline
                if self._try_token_type(TokenType.NEWLINE):
                    self._advance_pos()  # consume newline
                # check for block statements
                block_stmt_list: typing.List[BlockStmt] = []
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() in ["case", "end"]
                ):
                    block_stmt_list.append(self._parse_block_stmt())
                case_stmt_list.append(
                    CaseStmt(block_stmt_list, case_expr_list, is_else=is_else)
                )
                del is_else, case_expr_list, block_stmt_list
                if case_stmt_list[-1].is_else:
                    # 'Case' 'Else' must be the last case statement
                    break
            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "select")
            self._assert_consume(TokenType.NEWLINE)
            return SelectStmt(select_case_expr, case_stmt_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_select_stmt()") from ex

    def _parse_loop_stmt(self) -> GlobalStmt:
        """"""
        try:
            assert self._try_token_type(
                TokenType.IDENTIFIER
            ) and self._get_token_code() in [
                "do",
                "while",
            ], "Loop statement must start with 'Do' or 'While'"
            block_stmt_list: typing.List[BlockStmt] = []
            if self._get_token_code() == "while":
                # loop type is 'While'
                loop_type: Token = self._pos_tok
                self._advance_pos()  # consume loop type
                loop_expr: Expr = self._parse_expr()
                self._assert_consume(TokenType.NEWLINE)
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "wend"
                ):
                    block_stmt_list.append(self._parse_block_stmt())
                self._assert_consume(TokenType.IDENTIFIER, "wend")
                self._assert_consume(TokenType.NEWLINE)
                return LoopStmt(
                    block_stmt_list, loop_type=loop_type, loop_expr=loop_expr
                )

            # must be 'Do' loop
            self._assert_consume(TokenType.IDENTIFIER, "do")
            loop_type: typing.Optional[Token] = None
            loop_expr: typing.Optional[Expr] = None

            def _check_for_loop_type() -> bool:
                nonlocal self, loop_type, loop_expr
                if not self._try_token_type(TokenType.NEWLINE):
                    assert self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in [
                        "while",
                        "until",
                    ], "Loop type must be either 'While' or 'Until'"
                    loop_type = self._pos_tok
                    self._advance_pos()  # consume loop type
                    loop_expr = self._parse_expr()
                    return True
                return False

            # check if loop type is at the beginning
            found_loop_type = _check_for_loop_type()
            self._assert_consume(TokenType.NEWLINE)

            # block statement list
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "loop"
            ):
                block_stmt_list.append(self._parse_block_stmt())
            self._assert_consume(TokenType.IDENTIFIER, "loop")

            # check if loop type is at the end
            if not found_loop_type:
                _check_for_loop_type()
            self._assert_consume(TokenType.NEWLINE)

            return LoopStmt(block_stmt_list, loop_type=loop_type, loop_expr=loop_expr)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_loop_stmt()") from ex

    def _parse_for_stmt(self) -> GlobalStmt:
        """"""
        return ForStmt()

    def _parse_assign_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        # 'Set' is optional, don't throw if missing
        self._try_consume(TokenType.IDENTIFIER, "set")
        target_expr = self._parse_left_expr()

        # check for '='
        try:
            self._assert_consume(TokenType.SYMBOL, "=")
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_assign_stmt()") from ex

        # check for 'New'
        is_new = self._try_consume(TokenType.IDENTIFIER, "new")

        # parse assignment expression
        assign_expr = self._parse_left_expr() if is_new else self._parse_expr()
        return AssignStmt(target_expr, assign_expr, is_new=is_new)

    def _parse_call_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "call")
            return CallStmt(self._parse_left_expr())
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_call_stmt()") from ex

    def _parse_subcall_stmt(
        self,
        left_expr: LeftExpr,
        terminal_type: typing.Optional[TokenType] = None,
        terminal_code: typing.Optional[str] = None,
        terminal_casefold: bool = True,
        *,
        terminal_pairs: typing.List[typing.Tuple[TokenType, typing.Optional[str]]] = [],
    ) -> GlobalStmt:
        """

        Parameters
        ----------
        left_expr : LeftExpr
        terminal_type : TokenType
        terminal_code : str | None, default=None,
        terminal_casefold : bool, default=True
        terminal_pairs : List[Tuple[TokenType, str | None]] = []
            If len(terminal_pairs) > 0, will compare against the contents of terminal_pairs
            instead of using terminal_type and terminal_code

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
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
                nonlocal self, terminal_type, terminal_code, terminal_casefold, terminal_pairs
                if len(terminal_pairs) > 0:
                    return any(
                        map(
                            lambda tpair: self._try_token_type(tpair[0])
                            and (
                                (tpair[1] is None)
                                or (self._get_token_code(terminal_casefold) == tpair[1])
                            ),
                            terminal_pairs,
                        )
                    )
                return self._try_token_type(terminal_type) and (
                    (terminal_code is None)
                    or (self._get_token_code(terminal_casefold) == terminal_code)
                )

            sub_safe_expr = None
            if len(left_expr.index_or_params) == 0 or len(left_expr.tail) >= 1:
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
                        self._try_token_type(TokenType.SYMBOL)
                        and (self._get_token_code() == ",")
                    )
                ):
                    sub_safe_expr = self._parse_expr(True)
            else:
                # left_expr = <QualifiedID> <IndexOrParamsList>
                # make sure it matches:
                #   <QualifiedID> '(' [ <Expr> ] ')'
                assert (
                    len(left_expr.index_or_params) == 1
                    and 0 <= len(left_expr.index_or_params[0].expr_list) <= 1
                    and left_expr.index_or_params[0].dot == False
                    and len(left_expr.tail) == 0  # redundant check, but just in case
                ), "Expected left expression to have the form: <QualifiedID> '(' [ <Expr> ] ')'"

            # try to parse comma expression list
            comma_expr_list: typing.List[typing.Optional[Expr]] = []
            found_expr: bool = True  # fix: prevents erroneous None on first iteration
            while not _check_terminal():
                if self._try_consume(TokenType.SYMBOL, ","):
                    # was the previous entry not empty?
                    if found_expr:
                        found_expr = False
                    else:
                        comma_expr_list.append(None)
                else:
                    # interpret as expression
                    comma_expr_list.append(
                        self._parse_expr()
                    )  # don't need sub_safe here
                    found_expr = True
            # DON'T CONSUME TERMINAL, LEAVE FOR CALLER
            del found_expr

            return SubCallStmt(left_expr, sub_safe_expr, comma_expr_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_inline_stmt()") from ex

    def _parse_error_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "on")
            self._assert_consume(TokenType.IDENTIFIER, "error")

            # check for 'Resume'
            if self._try_consume(TokenType.IDENTIFIER, "resume"):
                self._assert_consume(TokenType.IDENTIFIER, "next")
                return ErrorStmt(resume_next=True)

            # check for 'GoTo'
            if self._try_consume(TokenType.IDENTIFIER, "goto"):
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
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_error_stmt()") from ex

    def _parse_exit_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "exit")
            # get exit type
            assert self._try_token_type(
                TokenType.IDENTIFIER
            ) and self._get_token_code() in [
                "do",
                "for",
                "function",
                "property",
                "sub",
            ], "Expected one of the following after 'Exit': 'Do', 'For', 'Function', 'Property', or 'Sub'"
            exit_tok = self._pos_tok
            self._advance_pos()  # consume exit type token
            return ExitStmt(exit_tok)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_exit_stmt()") from ex

    def _parse_erase_stmt(self) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "erase")
            return EraseStmt(self._parse_extended_id())
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_erase_stmt()") from ex

    def _parse_inline_stmt(
        self,
        terminal_type: typing.Optional[TokenType] = None,
        terminal_code: typing.Optional[str] = None,
        terminal_casefold: bool = True,
        *,
        terminal_pairs: typing.List[typing.Tuple[TokenType, typing.Optional[str]]] = [],
    ) -> GlobalStmt:
        """If inline statement is a subcall statement, uses the given terminal token type
        to determine the where the statement ends

        Does not consume the terminal token

        Parameters
        ----------
        terminal_type : TokenType
        terminal_code : str | None, default=None
        terminal_casefold : bool, default=True

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
                case "set":
                    # 'Set' is optional for AssignStmt
                    # need to also handle assignment without leading 'Set'
                    return self._parse_assign_stmt()
                case "call":
                    return self._parse_call_stmt()
                case "on":
                    return self._parse_error_stmt()
                case "exit":
                    return self._parse_exit_stmt()
                case "erase":
                    return self._parse_erase_stmt()

            # no leading keyword, try parsing a left expression
            left_expr: LeftExpr = self._parse_left_expr()

            # assign statement?
            if self._try_consume(TokenType.SYMBOL, "="):
                assign_expr = self._parse_expr()
                return AssignStmt(left_expr, assign_expr)

            # must be a subcall statement
            return self._parse_subcall_stmt(
                left_expr,
                terminal_type,
                terminal_code,
                terminal_casefold,
                terminal_pairs=terminal_pairs,
            )
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
            ret_inline = self._parse_inline_stmt(TokenType.NEWLINE)
            try:
                self._assert_consume(TokenType.NEWLINE)
            except AssertionError as ex:
                raise ParserError("An error occurred in _parse_block_stmt()") from ex
            return ret_inline
        raise ParserError(
            "Block statement should start with an identifier or dotted identifier"
        )

    def _parse_method_stmt(self) -> MethodStmt:
        """

        Returns
        -------
        MethodStmt
        """
        if self._try_token_type(TokenType.IDENTIFIER) and self._get_token_code() in [
            "const",
            "public",
            "private",
        ]:
            if self._try_consume(TokenType.IDENTIFIER, "public"):
                access_mod = AccessModifierType.PUBLIC
            elif self._try_consume(TokenType.IDENTIFIER, "private"):
                access_mod = AccessModifierType.PRIVATE
            else:
                access_mod = None
            return self._parse_const_decl(access_mod)
        else:
            return self._parse_block_stmt()

    def _parse_global_stmt(self) -> GlobalStmt:
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

        Raises
        ------
        RuntimeError
        """
        if self._tkzr is None:
            raise RuntimeError("Must use the Parser class within a runtime context!")

        # program may optionally start with a newline token
        if self._try_token_type(TokenType.NEWLINE):
            self._advance_pos()  # consume newline

        global_stmts: typing.List[GlobalStmt] = []
        # don't catch any errors here!
        # if this method is run inside of a context, errors will be handled by __exit__()
        while self._pos_tok is not None:
            global_stmts.append(self._parse_global_stmt())
        return Program(global_stmts)
