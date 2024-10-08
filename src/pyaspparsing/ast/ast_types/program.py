"""program module"""

import typing
import attrs
from ... import ParserError
from .parser_state import GlobalStateStack
from .state_handlers import (
    reg_state_handlers,
    reg_state_returns_stmt,
    GlobalStmtGenOpt,
    StmtGenManager,
)
from ..tokenizer.token_types import TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import GlobalStmt


__all__ = [
    "Program",
]


def parse_global_stmt(tkzr: Tokenizer) -> typing.Generator[GlobalStmt, None, None]:
    """
    Parameters
    ----------
    tkzr : Tokenizer
        Tokenizer that has entered into a runtime context

    Returns
    -------
    GlobalStmt

    Raises
    ------
    AssertionError
    """
    state_stack = GlobalStateStack()
    stmt_gen_mngr = StmtGenManager()
    try:
        for state in state_stack:
            # if state in reg_state_starts_stmt.keys():
            # curr_stmt_gen = reg_state_starts_stmt[state].generate_global_stmt()
            # use next(..., None) so that StopIteration isn't raised in a generator
            # next(curr_stmt_gen, None)  # start generator

            if state in reg_state_returns_stmt:
                yield reg_state_handlers[state](tkzr, state_stack, stmt_gen_mngr)
            else:
                reg_state_handlers[state](tkzr, state_stack, stmt_gen_mngr)

            # if state in reg_state_cleans_stmt:
            # curr_stmt_gen = None
    except Exception as ex:
        raise ParserError("An error occurred during parsing") from ex


@attrs.define
class Program:
    """The starting symbol for the VBScript grammar.
    Defined on grammar line 267

    Attributes
    ----------
    global_stmt_list : List[GlobalStmt], default=[]
    """

    global_stmt_list: typing.List[GlobalStmt] = attrs.field(default=attrs.Factory(list))

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer
            Tokenizer that has entered into a runtime context

        Returns
        -------
        Program
        """
        # program may optionally start with a newline token
        if tkzr.try_token_type(TokenType.NEWLINE):
            tkzr.advance_pos()  # consume newline

        # don't catch any errors here!
        # they should be caught by the Tokenizer runtime context
        return Program(list(parse_global_stmt(tkzr)))
