"""parse_expressions module"""

import typing
from ..tokenizer.token_types import Token, TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import Expr
from .expressions import *


# expressions need to be handled with a class to deal with circular Value and Expr references
class ExpressionParser:
    """"""

    @staticmethod
    def parse_value(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        pass

    @staticmethod
    def parse_const_expr(tkzr: Tokenizer) -> Expr:
        pass

    @staticmethod
    def parse_left_expr(tkzr: Tokenizer) -> Expr:
        pass

    @staticmethod
    def parse_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        return ExpressionParser.parse_imp_expr(tkzr, sub_safe)

    @staticmethod
    def parse_imp_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
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
    def parse_eqv_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
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
    def parse_xor_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
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
    def parse_or_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
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
    def parse_and_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # 'And' expression expands to the left, use a queue

    @staticmethod
    def parse_not_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # optimization: "Not Not" is a no-op
        # only use NotExpr when not_counter is odd

    @staticmethod
    def parse_compare_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # comparison expression expands to the left, use a queue

    @staticmethod
    def parse_concat_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # concatenation expression expands to the left, use a queue

    @staticmethod
    def parse_add_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # addition/subtraction expression expands to the left, use a queue

    @staticmethod
    def parse_mod_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # 'Mod' expression expands to the left, use a queue

    @staticmethod
    def parse_int_div_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # integer division expression expands to the left, use a queue

    @staticmethod
    def parse_mult_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
        """"""
        # multiplication/division expression expands to the left, use a queue
        op_queue: typing.List[Token] = []
        expr_queue: typing.List[Expr] = [
            ExpressionParser.parse_unary_expr(tkzr, sub_safe)
        ]

        # more than one term?
        while tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() in "*/":
            op_queue.append(tkzr)
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
    def parse_unary_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
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
    def parse_exp_expr(tkzr: Tokenizer, sub_safe: bool = True) -> Expr:
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
