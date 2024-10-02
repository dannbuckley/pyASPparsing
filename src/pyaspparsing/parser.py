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

    def __exit__(self, exc_type, exc_val, tb) -> bool:
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

    def _parse_exp_expr(self) -> Expr:
        """

        Returns
        -------
        Expr
        """
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
        """

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
        ret_expr: Expr = self._parse_exp_expr()
        while len(sign_stack) > 0:
            ret_expr = UnaryExpr(sign_stack.pop(), ret_expr)
        return ret_expr

    def _parse_mult_expr(self) -> Expr:
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
        # mod expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_int_div_expr()]

        # more than one term?
        while (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "mod"
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
        # or expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [self._parse_and_expr()]

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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
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
        """

        Returns
        -------
        Expr
        """
        return self._parse_imp_expr()

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
        while self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
            self._advance_pos()  # consume '('
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

            if (
                not self._try_token_type(TokenType.SYMBOL)
                or self._get_token_code() != ")"
            ):
                raise ParserError(
                    "Expected closing ')' for index or params list in left expression"
                )
            self._advance_pos()  # consume ')'

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
            while (
                self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "("
            ):
                self._advance_pos()  # consume '('
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

                if (
                    not self._try_token_type(TokenType.SYMBOL)
                    or self._get_token_code() != ")"
                ):
                    raise ParserError(
                        "Expected closing ')' for index or params list in left expression tail"
                    )
                self._advance_pos()  # consume ')'

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

    def _parse_value(self) -> Expr:
        """

        Returns
        -------
        Expr

        Raises
        ------
        ParserError
        """
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
                raise ParserError("Missing newline after 'End Class'")
            self._advance_pos()  # consume newline
            return ClassDecl(class_id, member_decl_list)
        raise ParserError("_parse_class_decl() did not find 'Class' token")

    def _parse_const_decl(
        self, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "const"
        ):
            raise ParserError("_parse_const_decl() did not find 'Const' token")
        return ConstDecl(access_mod=access_mod)

    def _parse_sub_decl(
        self, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "sub"
        ):
            raise ParserError("_parse_sub_decl() did not find 'Sub' token")
        self._advance_pos() # consume 'Sub'
        sub_id: ExtendedID = self._parse_extended_id()
        method_arg_list: typing.List[Arg] = []
        if self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
            self._advance_pos()  # consume '('

            while not (
                self._try_token_type(TokenType.SYMBOL) and self._get_token_code() != ")"
            ):
                if self._try_token_type(
                    TokenType.IDENTIFIER
                ) and self._get_token_code() in ["byval", "byref"]:
                    arg_modifier = self._pos_tok
                    self._advance_pos()  # consume modifier
                else:
                    arg_modifier = None
                arg_id = self._parse_extended_id()
                has_paren = (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == "("
                )
                if has_paren:
                    self._advance_pos()  # consume '('
                    if (
                        not self._try_token_type(TokenType.SYMBOL)
                        or self._get_token_code() != ")"
                    ):
                        raise ParserError(
                            "Expected ending ')' in argument definition for sub declaration"
                        )
                    self._advance_pos()  # consume ')'
                method_arg_list.append(Arg(arg_id, arg_modifier, has_paren))

                if (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ","
                ):
                    self._advance_pos()  # consume ','

            if (
                not self._try_token_type(TokenType.SYMBOL)
                or self._get_token_code() != ")"
            ):
                raise ParserError(
                    "Expected ending ')' in method argument list of sub declaration"
                )
            self._advance_pos()  # consume ')'

        method_stmt_list: typing.List[MethodStmt] = []
        if self._try_token_type(TokenType.NEWLINE):
            self._advance_pos()  # consume newline
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                method_stmt_list.append(self._parse_method_stmt())
        else:
            method_stmt_list.append(self._parse_inline_stmt())

        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "end"
        ):
            raise ParserError("Expected 'End' in sub declaration")
        self._advance_pos()  # consume 'End'
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "sub"
        ):
            raise ParserError("Expected 'Sub' after 'End' in sub declaration")
        self._advance_pos()  # consume 'Sub'
        if not self._try_token_type(TokenType.NEWLINE):
            raise ParserError("Expected newline after sub declaration")
        self._advance_pos()  # consume newline
        return SubDecl(sub_id, method_arg_list, method_stmt_list, access_mod=access_mod)

    def _parse_function_decl(
        self, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "function"
        ):
            raise ParserError("_parse_function_decl() did not find 'Function' token")
        self._advance_pos() # consume 'Function'
        function_id: ExtendedID = self._parse_extended_id()
        method_arg_list: typing.List[Arg] = []
        if self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
            self._advance_pos()  # consume '('

            while not (
                self._try_token_type(TokenType.SYMBOL) and self._get_token_code() != ")"
            ):
                if self._try_token_type(
                    TokenType.IDENTIFIER
                ) and self._get_token_code() in ["byval", "byref"]:
                    arg_modifier = self._pos_tok
                    self._advance_pos()  # consume modifier
                else:
                    arg_modifier = None
                arg_id = self._parse_extended_id()
                has_paren = (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == "("
                )
                if has_paren:
                    self._advance_pos()  # consume '('
                    if (
                        not self._try_token_type(TokenType.SYMBOL)
                        or self._get_token_code() != ")"
                    ):
                        raise ParserError(
                            "Expected ending ')' in argument definition for function declaration"
                        )
                    self._advance_pos()  # consume ')'
                method_arg_list.append(Arg(arg_id, arg_modifier, has_paren))

                if (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ","
                ):
                    self._advance_pos()  # consume ','

            if (
                not self._try_token_type(TokenType.SYMBOL)
                or self._get_token_code() != ")"
            ):
                raise ParserError(
                    "Expected ending ')' in method argument list of function declaration"
                )
            self._advance_pos()  # consume ')'

        method_stmt_list: typing.List[MethodStmt] = []
        if self._try_token_type(TokenType.NEWLINE):
            self._advance_pos()  # consume newline
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                method_stmt_list.append(self._parse_method_stmt())
        else:
            method_stmt_list.append(self._parse_inline_stmt())

        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "end"
        ):
            raise ParserError("Expected 'End' token in function declaration")
        self._advance_pos()  # consume 'End'
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "function"
        ):
            raise ParserError("Expected 'Function' after 'End' in function declaration")
        self._advance_pos()  # consume 'Function'
        if not self._try_token_type(TokenType.NEWLINE):
            raise ParserError("Expected newline after function declaration")
        self._advance_pos()  # consume newline
        return FunctionDecl(
            function_id, method_arg_list, method_stmt_list, access_mod=access_mod
        )

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
            # identify access modifier
            if self._get_token_code() == "public":
                self._advance_pos()  # consume 'Public'
                if (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "default"
                ):
                    self._advance_pos()  # consume 'Default'
                    access_mod = AccessModifierType.PUBLIC_DEFAULT
                else:
                    access_mod = AccessModifierType.PUBLIC
            elif self._get_token_code() == "private":
                self._advance_pos()  # consume 'Private'
                access_mod = AccessModifierType.PRIVATE

            if not self._try_token_type(TokenType.IDENTIFIER):
                raise ParserError("Expected an identifier token after access modifier")

            # check for other declaration types
            match self._get_token_code():
                case "const" if access_mod != AccessModifierType.PUBLIC_DEFAULT:
                    # cannot use 'Default' with const declaration
                    return self._parse_const_decl(access_mod)
                case "const" if access_mod == AccessModifierType.PUBLIC_DEFAULT:
                    raise ParserError(
                        "'Public Default' access modifier cannot be used with const declaration"
                    )
                case "sub":
                    return self._parse_sub_decl(access_mod)
                case "function":
                    return self._parse_function_decl(access_mod)

            if access_mod == AccessModifierType.PUBLIC_DEFAULT:
                raise ParserError(
                    "'Public Default' access modifier cannot be used with field declaration"
                )

            # did not match token, parse as a field declaration
            if not self._try_token_type(TokenType.IDENTIFIER):
                raise ParserError("Expected field name identifier in field declaration")
            field_id: FieldID = FieldID(self._pos_tok)
            self._advance_pos()  # consume identifier

            int_literals: typing.List[Token] = []
            if self._try_token_type(TokenType.SYMBOL) and self._get_token_code() == "(":
                self._advance_pos()  # consume '('
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
                        "Expected ending ')' for array rank list of field name declaration"
                    )
                self._advance_pos()  # consume ')'
                del find_int_literal
            field_name: FieldName = FieldName(field_id, int_literals)
            del int_literals

            other_vars: typing.List[VarName] = []
            parse_var_name = self._try_token_type(TokenType.IDENTIFIER)
            while parse_var_name:
                var_id = self._parse_extended_id()
                if (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == "("
                ):
                    self._advance_pos()  # consume '('
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
                    # should have and ending ')'
                    if (
                        not self._try_token_type(TokenType.SYMBOL)
                        or self._get_token_code() != ")"
                    ):
                        raise ParserError(
                            "Expected ending ')' for array rank list "
                            "of variable name declaration (part of field declaration)"
                        )
                    self._advance_pos()  # consume ')'
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

            if not self._try_token_type(TokenType.NEWLINE):
                raise ParserError("Expected newline after field declaration")
            self._advance_pos()  # consume newline
            return FieldDecl(field_name, other_vars, access_mod=access_mod)
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
                            "Invalid token type found in array rank list "
                            "of variable name declaration"
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
            and self._get_token_code() == "set"
        ):
            # 'Set' is optional, don't throw if missing
            self._advance_pos()  # consume 'Set'

        # parse target expression
        target_expr = self._parse_left_expr()

        # check for '='
        if not self._try_token_type(TokenType.SYMBOL) or self._get_token_code() != "=":
            raise ParserError("Expected '=' in assignment statement")
        self._advance_pos()  # consume '='

        # check for 'New'
        is_new = (
            self._try_token_type(TokenType.IDENTIFIER)
            and self._get_token_code() == "new"
        )
        if is_new:
            self._advance_pos()  # consume 'New'

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
        if (
            not self._try_token_type(TokenType.IDENTIFIER)
            or self._get_token_code() != "call"
        ):
            raise ParserError("_parse_call_stmt() did not find 'Call' token")
        self._advance_pos()  # consume 'Call'
        return CallStmt(self._parse_left_expr())

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
            and self._get_token_code() == "erase"
        ):
            self._advance_pos()  # consume 'Erase'
            return EraseStmt(self._parse_extended_id())
        raise ParserError("_parse_erase_stmt() could not find 'Erase' token")

    def _parse_inline_stmt(self) -> GlobalStmt:
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

                # TODO: assign statement without leading 'Set'

                # TODO: subcall statement
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
            if self._get_token_code() == "public":
                self._advance_pos()  # consume 'Public'
                access_mod = AccessModifierType.PUBLIC
            elif self._get_token_code() == "private":
                self._advance_pos()  # consume 'Private'
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
