"""parse_expressions module"""

import typing
from ... import ParserError
from ..tokenizer.token_types import Token, TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import Expr, CompareExprType
from .expressions import *

__all__ = ["ExpressionParser"]


# expressions need to be handled with a class to deal with circular Value and Expr references
class ExpressionParser:
    """"""

    @staticmethod
    def parse_value(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
        if not sub_safe:
            # value could be expression wrapped in parentheses
            if tkzr.try_consume(TokenType.SYMBOL, "("):
                ret_expr = ExpressionParser.parse_expr(tkzr, sub_safe)
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
        if tkzr.try_token_type(TokenType.IDENTIFIER):
            return ExpressionParser.parse_left_expr(tkzr)

        raise ParserError("Invalid token in value expression")

    @staticmethod
    def parse_const_expr(tkzr: Tokenizer) -> Expr:
        """"""
        ret_token = tkzr.current_token
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
        """"""
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
        """"""
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
        """"""
        qual_id_tail: QualifiedID = ExpressionParser.parse_qualified_id(tkzr)
        # check for index or params list
        index_or_params_tail: typing.List[IndexOrParams] = []
        while tkzr.try_consume(TokenType.SYMBOL, "("):
            expr_list: typing.List[Expr] = []
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
    def parse_left_expr(tkzr: Tokenizer) -> Expr:
        """"""
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
    def parse_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        return ExpressionParser.parse_imp_expr(tkzr, sub_safe)

    @staticmethod
    def parse_imp_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, ImpExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_eqv_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, EqvExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_xor_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, XorExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_or_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, OrExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_and_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, AndExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_not_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
        # optimization: "Not Not" is a no-op
        # only use NotExpr when not_counter is odd
        not_counter = 0
        while tkzr.try_consume(TokenType.IDENTIFIER, "not"):
            not_counter += 1

        not_expr = ExpressionParser.parse_compare_expr(tkzr, sub_safe)
        return NotExpr(not_expr) if not_counter % 2 == 1 else not_expr

    @staticmethod
    def parse_compare_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, CompareExpr(cmp_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_concat_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
        # concatenation expression expands to the left, use a queue
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_add_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_consume(TokenType.SYMBOL, "&"):
            expr_queue.append(ExpressionParser.parse_add_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next ConcatExpr
            expr_queue.insert(0, ConcatExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_add_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
        # addition/subtraction expression expands to the left, use a queue
        op_queue: typing.List[Token] = []
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_mod_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "+-":
            op_queue.append(tkzr.current_token)
            tkzr.advance_pos()  # consume operator
            expr_queue.append(ExpressionParser.parse_mod_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next AddExpr
            expr_queue.insert(0, AddExpr(op_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_mod_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, ModExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_int_div_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_queue.insert(0, IntDivExpr(expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_mult_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
        # multiplication/division expression expands to the left, use a queue
        op_queue: typing.List[Token] = []
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_unary_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "*/":
            op_queue.append(tkzr.current_token)
            tkzr.advance_pos()  # consume operator
            expr_queue.append(ExpressionParser.parse_unary_expr(tkzr, sub_safe))

        # combine terms into one expression
        while len(expr_queue) > 1:
            # queue: pop from front
            expr_left: Expr = expr_queue.pop(0)
            expr_right: Expr = expr_queue.pop(0)
            # new expression becomes left term of next MultExpr
            expr_queue.insert(0, MultExpr(op_queue.pop(0), expr_left, expr_right))
        return expr_queue.pop()

    @staticmethod
    def parse_unary_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
        # unary expression expands to the right, use a stack
        sign_stack: typing.List[Token] = []

        while tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "-+":
            sign_stack.append(tkzr.current_token)
            tkzr.advance_pos()  # consume sign

        # combine signs into one expression
        ret_expr: Expr = ExpressionParser.parse_exp_expr(tkzr, sub_safe)
        while len(sign_stack) > 0:
            ret_expr = UnaryExpr(sign_stack.pop(), ret_expr)
        return ret_expr

    @staticmethod
    def parse_exp_expr(tkzr: Tokenizer, sub_safe: bool = False) -> Expr:
        """"""
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
            expr_stack.append(ExpExpr(expr_left, expr_right))
        return expr_stack.pop()
