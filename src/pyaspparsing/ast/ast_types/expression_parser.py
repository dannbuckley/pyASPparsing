"""parse_expressions module"""

import typing
from ... import ParserError
from ..tokenizer.token_types import Token, TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import Expr, CompareExprType
from .expressions import (
    ImpExpr,
    EqvExpr,
    XorExpr,
    OrExpr,
    AndExpr,
    NotExpr,
    CompareExpr,
    ConcatExpr,
    AddExpr,
    ModExpr,
    IntDivExpr,
    MultExpr,
    UnaryExpr,
    ExpExpr,
    ConstExpr,
    BoolLiteral,
    IntLiteral,
    Nothing,
    QualifiedID,
    IndexOrParams,
    LeftExprTail,
    LeftExpr,
)
from .optimize import FoldableExpr, AddNegated, MultReciprocal


# expressions need to be handled with a class to deal with circular Value and Expr references
class ExpressionParser:
    """Collection of static expression parser functions

    Expression parsing should start with a call to parse_expr()
    """

    @staticmethod
    def parse_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """The entry point for expression parsing

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        return ExpressionParser.parse_imp_expr(tkzr, sub_safe)

    @staticmethod
    def parse_value(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse value expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        if not sub_safe:
            # value could be expression wrapped in parentheses
            if tkzr.try_consume(TokenType.SYMBOL, "("):
                ret_expr: Expr = ExpressionParser.parse_expr(tkzr, sub_safe)
                tkzr.assert_consume(TokenType.SYMBOL, ")")
                return ret_expr

        # try const expression
        if tkzr.try_multiple_token_type(
            [
                TokenType.LITERAL_INT,
                TokenType.LITERAL_HEX,
                TokenType.LITERAL_OCT,
                TokenType.LITERAL_FLOAT,
                TokenType.LITERAL_STRING,
                TokenType.LITERAL_DATE,
            ]
        ) or (
            tkzr.try_token_type(TokenType.IDENTIFIER)
            and tkzr.get_token_code() in ["true", "false", "nothing", "null", "empty"]
        ):
            return ExpressionParser.parse_const_expr(tkzr)

        # try left expression
        # if tkzr.try_token_type(TokenType.IDENTIFIER):
        if tkzr.try_multiple_token_type(
            [TokenType.IDENTIFIER, TokenType.IDENTIFIER_IDDOT]
        ):
            return ExpressionParser.parse_left_expr(tkzr)

        raise ParserError("Invalid token in value expression")

    @staticmethod
    def parse_const_expr(tkzr: Tokenizer) -> ConstExpr:
        """NOT CALLED DIRECTLY

        Parse constant expression

        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        Expr
        """
        ret_token = tkzr.current_token
        assert ret_token is not None, "Expected constant expression, found None"
        if tkzr.try_multiple_token_type(
            [TokenType.LITERAL_FLOAT, TokenType.LITERAL_STRING, TokenType.LITERAL_DATE]
        ):
            tkzr.advance_pos()  # consume const expression
            return ConstExpr(ret_token)
        if tkzr.try_multiple_token_type(
            [TokenType.LITERAL_INT, TokenType.LITERAL_HEX, TokenType.LITERAL_OCT]
        ):
            tkzr.advance_pos()  # consume int literal expression
            return IntLiteral(ret_token)
        # try to match as identifier
        if tkzr.try_token_type(TokenType.IDENTIFIER):
            match tkzr.get_token_code():
                case "true" | "false":
                    tkzr.advance_pos()  # consume bool literal
                    return BoolLiteral(ret_token)
                case "nothing" | "null" | "empty":
                    tkzr.advance_pos()  # consume nothing symbol
                    return Nothing(ret_token)
                case _:
                    raise ParserError("Invalid identifier in const expression")
        raise ParserError("Invalid token in const expression")

    @staticmethod
    def parse_qualified_id_tail(tkzr: Tokenizer) -> Token:
        """NOT CALLED DIRECTLY

        Parse a tail token for a qualified identifier

        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        Token
        """
        assert (
            tkzr.current_token is not None
        ), "Expected the tail of a qualified identifier, found None"
        if (kw_id := tkzr.try_keyword_id()) is not None:
            tkzr.advance_pos()  # consume keyword identifier
            return kw_id
        if tkzr.try_multiple_token_type(
            [TokenType.IDENTIFIER, TokenType.IDENTIFIER_IDDOT]
        ):
            id_tok = tkzr.current_token
            tkzr.advance_pos()  # consume identifier
            return id_tok
        raise ParserError(
            "Expected an identifier or a dotted identifier "
            "in the tail of the qualified identifier symbol"
        )

    @staticmethod
    def parse_qualified_id(tkzr: Tokenizer) -> QualifiedID:
        """NOT CALLED DIRECTLY

        Parse a qualified identifier

        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        QualifiedID
        """
        assert (
            tkzr.current_token is not None
        ), "Expected a qualified identifier, found None"
        if tkzr.try_multiple_token_type(
            [TokenType.IDENTIFIER_IDDOT, TokenType.IDENTIFIER_DOTIDDOT]
        ):
            id_tokens: typing.List[Token] = [tkzr.current_token]
            tkzr.advance_pos()  # consume identifier
            expand_tail = True
            while expand_tail:
                id_tokens.append(ExpressionParser.parse_qualified_id_tail(tkzr))
                if id_tokens[-1].token_type != TokenType.IDENTIFIER_IDDOT:
                    expand_tail = False
            return QualifiedID(id_tokens)
        if tkzr.try_multiple_token_type(
            [TokenType.IDENTIFIER, TokenType.IDENTIFIER_DOTID]
        ):
            id_token = tkzr.current_token
            tkzr.advance_pos()  # consume identifier
            return QualifiedID([id_token])
        raise ParserError(
            "Expected either an identifier token or a dotted identifier token "
            "for the qualified identifier symbol"
        )

    @staticmethod
    def parse_left_expr_tail(tkzr: Tokenizer) -> LeftExprTail:
        """NOT CALLED DIRECTLY

        Parse the tail of a left expression

        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        LeftExprTail
        """
        qual_id_tail: QualifiedID = ExpressionParser.parse_qualified_id(tkzr)
        # check for index or params list
        index_or_params_tail: typing.List[IndexOrParams] = []
        while tkzr.try_consume(TokenType.SYMBOL, "("):
            expr_list: typing.List[typing.Optional[Expr]] = []
            found_expr: bool = False  # helper variable for parsing commas
            while not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ")"
            ):
                if (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and tkzr.get_token_code() == ","
                ):
                    tkzr.advance_pos()  # consume ','
                    # was the previous entry not empty
                    if found_expr:
                        found_expr = False
                    else:
                        expr_list.append(None)
                else:
                    # interpret as expression
                    expr_list.append(ExpressionParser.parse_expr(tkzr))
                    found_expr = True
            del found_expr
            # close current index or params list
            tkzr.assert_consume(TokenType.SYMBOL, ")")
            # check for dot
            dot = tkzr.try_multiple_token_type(
                [TokenType.IDENTIFIER_DOTID, TokenType.IDENTIFIER_DOTIDDOT]
            )
            index_or_params_tail.append(IndexOrParams(expr_list, dot=dot))
            del dot, expr_list
        return LeftExprTail(qual_id_tail, index_or_params_tail)

    @staticmethod
    def parse_left_expr(tkzr: Tokenizer) -> LeftExpr:
        """NOT CALLED DIRECTLY

        Parse a left expression

        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        LeftExpr
        """
        # attempt to parse qualified identifier
        qual_id = ExpressionParser.parse_qualified_id(tkzr)
        # check for index or params list
        index_or_params: typing.List[IndexOrParams] = []
        while tkzr.try_consume(TokenType.SYMBOL, "("):
            expr_list: typing.List[typing.Optional[Expr]] = []
            found_expr: bool = False  # helper variable for parsing commas
            while not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ")"
            ):
                if tkzr.try_consume(TokenType.SYMBOL, ","):
                    # was the previous entry not empty?
                    if found_expr:
                        found_expr = False
                    else:
                        expr_list.append(None)
                else:
                    # interpret as expression
                    expr_list.append(ExpressionParser.parse_expr(tkzr))
                    found_expr = True
            del found_expr
            # close current index or params list
            tkzr.assert_consume(TokenType.SYMBOL, ")")
            # check for dot
            dot = tkzr.try_multiple_token_type(
                [TokenType.IDENTIFIER_DOTID, TokenType.IDENTIFIER_DOTIDDOT]
            )
            index_or_params.append(IndexOrParams(expr_list, dot=dot))
            del dot, expr_list

        if len(index_or_params) == 0:
            # left expression is just a qualified identifier
            return LeftExpr(qual_id)

        if not index_or_params[-1].dot:
            # left expression does not have a tail
            return LeftExpr(qual_id, index_or_params)

        left_expr_tail: typing.List[LeftExprTail] = []
        parse_tail: bool = True
        while parse_tail:
            left_expr_tail.append(ExpressionParser.parse_left_expr_tail(tkzr))
            # continue if this left expression tail contained a dotted "index or params" list
            parse_tail = (
                len(left_expr_tail[-1].index_or_params) > 0
            ) and left_expr_tail[-1].index_or_params[-1].dot
        return LeftExpr(qual_id, index_or_params, left_expr_tail)

    @staticmethod
    def parse_imp_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse an implication expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # 'Imp' expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_eqv_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_consume(TokenType.IDENTIFIER, "imp"):
            expr_queue.append(ExpressionParser.parse_eqv_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next ImpExpr
            expr_queue.insert(0, FoldableExpr.try_fold(expr_left, expr_right, ImpExpr))
        return expr_queue.pop()

    @staticmethod
    def parse_eqv_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse an equivalence expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # 'Eqv' expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_xor_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_consume(TokenType.IDENTIFIER, "eqv"):
            expr_queue.append(ExpressionParser.parse_xor_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next EqvExpr
            expr_queue.insert(0, FoldableExpr.try_fold(expr_left, expr_right, EqvExpr))
        return expr_queue.pop()

    @staticmethod
    def parse_xor_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse an exclusive disjunction (Xor) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # 'Xor' expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [ExpressionParser.parse_or_expr(tkzr, sub_safe)]

        # more than one term?
        while tkzr.try_consume(TokenType.IDENTIFIER, "xor"):
            expr_queue.append(ExpressionParser.parse_or_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next XorExpr
            expr_queue.insert(0, FoldableExpr.try_fold(expr_left, expr_right, XorExpr))
        return expr_queue.pop()

    @staticmethod
    def parse_or_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse an inclusive disjunction (Or) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # 'Or' expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_and_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_consume(TokenType.IDENTIFIER, "or"):
            expr_queue.append(ExpressionParser.parse_and_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next OrExpr
            expr_queue.insert(0, FoldableExpr.try_fold(expr_left, expr_right, OrExpr))
        return expr_queue.pop()

    @staticmethod
    def parse_and_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse a conjunction (And) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # 'And' expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_not_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_consume(TokenType.IDENTIFIER, "and"):
            expr_queue.append(ExpressionParser.parse_not_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next AndExpr
            expr_queue.insert(0, FoldableExpr.try_fold(expr_left, expr_right, AndExpr))
        return expr_queue.pop()

    @staticmethod
    def parse_not_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse a complement (Not) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # optimization: "Not Not" is a no-op
        # only use NotExpr when not_counter is odd
        not_counter = 0
        while tkzr.try_consume(TokenType.IDENTIFIER, "not"):
            not_counter += 1

        not_expr = ExpressionParser.parse_compare_expr(tkzr, sub_safe)
        if not_counter % 2 == 0:
            return not_expr
        can_fold = isinstance(not_expr, (FoldableExpr, ConstExpr))
        if isinstance(not_expr, FoldableExpr):
            not_expr = not_expr.wrapped_expr
        not_expr = NotExpr(not_expr)
        return FoldableExpr(not_expr) if can_fold else not_expr

    @staticmethod
    def parse_compare_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse a comparison expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # comparison expression expands to the left, use a queue
        cmp_queue: typing.List[CompareExprType] = []
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_concat_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while (
            tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "is"
        ) or (tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "<>="):
            if tkzr.try_consume(TokenType.IDENTIFIER, "is"):
                if tkzr.try_consume(TokenType.IDENTIFIER, "not"):
                    # 'Is Not' comparison
                    cmp_queue.append(CompareExprType.COMPARE_ISNOT)
                else:
                    # 'Is' comparison
                    cmp_queue.append(CompareExprType.COMPARE_IS)
            elif tkzr.try_consume(TokenType.SYMBOL, ">"):
                if tkzr.try_consume(TokenType.SYMBOL, "="):
                    # '>=' comparison
                    cmp_queue.append(CompareExprType.COMPARE_GTEQ)
                else:
                    # '>' comparison
                    cmp_queue.append(CompareExprType.COMPARE_GT)
            elif tkzr.try_consume(TokenType.SYMBOL, "<"):
                if tkzr.try_consume(TokenType.SYMBOL, "="):
                    # '<=' comparison
                    cmp_queue.append(CompareExprType.COMPARE_LTEQ)
                elif tkzr.try_consume(TokenType.SYMBOL, ">"):
                    # '<>' comparison
                    cmp_queue.append(CompareExprType.COMPARE_LTGT)
                else:
                    # '<' comparison
                    cmp_queue.append(CompareExprType.COMPARE_LT)
            elif tkzr.try_consume(TokenType.SYMBOL, "="):
                if tkzr.try_consume(TokenType.SYMBOL, ">"):
                    # '=>' comparison
                    cmp_queue.append(CompareExprType.COMPARE_EQGT)
                elif tkzr.try_consume(TokenType.SYMBOL, "<"):
                    # '=<' comparison
                    cmp_queue.append(CompareExprType.COMPARE_EQLT)
                else:
                    # '=' comparison
                    cmp_queue.append(CompareExprType.COMPARE_EQ)
            expr_queue.append(ExpressionParser.parse_concat_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next CompareExpr
            expr_queue.insert(
                0,
                FoldableExpr.try_fold(
                    expr_left, expr_right, CompareExpr, cmp_queue.pop(0)
                ),
            )
        return expr_queue.pop()

    @staticmethod
    def parse_concat_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse a string concatenation (&) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # get first expression
        concat_expr: Expr = ExpressionParser.parse_add_expr(tkzr, sub_safe)

        # more than one term?
        while tkzr.try_consume(TokenType.SYMBOL, "&"):
            if isinstance(concat_expr, ConcatExpr) and any(
                FoldableExpr.can_fold(concat_expr.right)
            ):
                concat_expr = ConcatExpr(
                    concat_expr.left,
                    # fold adjacent strings
                    FoldableExpr.try_fold(
                        concat_expr.right,
                        ExpressionParser.parse_add_expr(tkzr, sub_safe),
                        ConcatExpr,
                    ),
                )
            else:
                concat_expr = FoldableExpr.try_fold(
                    concat_expr,
                    ExpressionParser.parse_add_expr(tkzr, sub_safe),
                    ConcatExpr,
                )
        return concat_expr

    @staticmethod
    def parse_add_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse an addition/subtraction expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool

        Returns
        -------
        Expr
        """
        # terms in expression can be evaluated immediately
        imm_expr: typing.Optional[Expr] = None
        # expression contains terms that cannot be evaluated immediately
        # evaluation must be deferred
        dfr_expr: typing.Optional[Expr] = None

        def _consume_mod_expr(sub_op: bool = False):
            """
            Parameters
            ----------
            sub_op : bool, default=False
                True if previous operator was '-' (subtraction)
            """
            nonlocal tkzr, sub_safe, imm_expr, dfr_expr
            mod_expr = ExpressionParser.parse_mod_expr(tkzr, sub_safe)
            if sub_op:
                # represent subtraction as addition of negative values
                # this makes it easier to move terms around
                mod_expr = AddNegated.wrap(mod_expr)
            if any(FoldableExpr.can_fold(mod_expr)):
                # new expression can be evaluated immediately
                imm_expr = (
                    mod_expr
                    if imm_expr is None
                    else FoldableExpr.try_fold(imm_expr, mod_expr, AddExpr)
                )
            else:
                # evaluation of new expression must be deferred
                dfr_expr = mod_expr if dfr_expr is None else AddExpr(dfr_expr, mod_expr)

        # get first expression
        _consume_mod_expr()

        # more than one term?
        while tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "+-":
            sub_op = tkzr.get_token_code() == "-"
            tkzr.advance_pos()  # consume operator
            _consume_mod_expr(sub_op)

        if imm_expr is not None and dfr_expr is None:
            # pass-through: immediate expression
            return imm_expr
        if dfr_expr is not None and imm_expr is None:
            # pass-through: deferred expression
            return dfr_expr
        # move immediate expression to left subtree
        # and deferred expression to right subtree
        return AddExpr(imm_expr, dfr_expr)

    @staticmethod
    def parse_mod_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse a modulo (Mod) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # 'Mod' expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_int_div_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_consume(TokenType.IDENTIFIER, "mod"):
            expr_queue.append(ExpressionParser.parse_int_div_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next ModExpr
            expr_queue.insert(0, FoldableExpr.try_fold(expr_left, expr_right, ModExpr))
        return expr_queue.pop()

    @staticmethod
    def parse_int_div_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse an integer division (&#92;) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # integer division expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_mult_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_consume(TokenType.SYMBOL, "\\"):
            expr_queue.append(ExpressionParser.parse_mult_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next IntDivExpr
            expr_queue.insert(0, FoldableExpr.try_fold(expr_left, expr_right, IntDivExpr))
        return expr_queue.pop()

    @staticmethod
    def parse_mult_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse a multiplication/division expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # terms in expression can be evaluated immediately
        imm_expr: typing.Optional[Expr] = None
        # expression contains terms that cannot be evaluated immediately
        # evaluation must be deferred
        dfr_expr: typing.Optional[Expr] = None

        def _consume_unary_expr(div_op: bool = False):
            """
            Parameters
            ----------
            div_op : bool, default=False
                True if previous operator '/' (division)
            """
            nonlocal tkzr, sub_safe, imm_expr, dfr_expr
            unary_expr = ExpressionParser.parse_unary_expr(tkzr, sub_safe)
            if div_op:
                # represent division as multiplication of reciprocal values
                # this makes it easier to move terms around
                unary_expr = MultReciprocal.wrap(unary_expr)
            if any(FoldableExpr.can_fold(unary_expr)):
                # new expression can be evaluated immediately
                imm_expr = (
                    unary_expr
                    if imm_expr is None
                    else FoldableExpr.try_fold(imm_expr, unary_expr, MultExpr)
                )
            else:
                # evaluation of new expression must be deferred
                dfr_expr = (
                    unary_expr if dfr_expr is None else MultExpr(dfr_expr, unary_expr)
                )

        # get first expression
        _consume_unary_expr()

        # more than one term?
        while tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "*/":
            div_op = tkzr.get_token_code() == "/"
            tkzr.advance_pos()  # consume operator
            _consume_unary_expr(div_op)

        if imm_expr is not None and dfr_expr is None:
            # pass-through: immediate expression
            return imm_expr
        if dfr_expr is not None and imm_expr is None:
            # pass-through: deferred expression
            return dfr_expr
        # move immediate expression to left subtree
        # and deferred expression to right subtree
        return MultExpr(imm_expr, dfr_expr)

    @staticmethod
    def parse_unary_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse a unary signed expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # unary expression expands to the right, use a stack
        sign_stack: typing.List[Token] = []

        while tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "-+":
            sign_stack.append(tkzr.current_token)
            tkzr.advance_pos()  # consume sign

        # combine signs into one expression
        ret_expr: Expr = ExpressionParser.parse_exp_expr(tkzr, sub_safe)
        can_fold = (
            isinstance(ret_expr, FoldableExpr) or isinstance(ret_expr, ConstExpr)
        ) and len(sign_stack) > 0
        if isinstance(ret_expr, FoldableExpr) and len(sign_stack) > 0:
            # unwrap before processing sign stack
            ret_expr = ret_expr.wrapped_expr
        while len(sign_stack) > 0:
            ret_expr = UnaryExpr(sign_stack.pop(), ret_expr)
        return FoldableExpr(ret_expr) if can_fold else ret_expr

    @staticmethod
    def parse_exp_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """NOT CALLED DIRECTLY

        Parse an exponentiation (^) expression

        Parameters
        ----------
        tkzr : Tokenizer
        sub_safe : bool, default=False

        Returns
        -------
        Expr
        """
        # exponentiation expression expands to the right, use a stack
        expr_stack: typing.List[Expr] = [ExpressionParser.parse_value(tkzr, sub_safe)]

        # more than one term?
        while tkzr.try_consume(TokenType.SYMBOL, "^"):
            expr_stack.append(ExpressionParser.parse_value(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_stack) > 1:
            # stack: pop from back
            expr_right: Expr = expr_stack.pop()
            expr_left: Expr = expr_stack.pop()
            # new expression becomes right term of next ExpExpr
            expr_stack.append(FoldableExpr.try_fold(expr_left, expr_right, ExpExpr))
        return expr_stack.pop()
