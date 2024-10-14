"""program module"""

import typing
import attrs
from .parser import Parser
from ..tokenizer.token_types import TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import *


__all__ = ["Program"]


@attrs.define(repr=False, slots=False)
class Program(FormatterMixin):
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
        global_stmts: typing.List[GlobalStmt] = []

        # if code has a processing directive,
        # it must be on the first line
        if tkzr.try_token_type(TokenType.DELIM_START_PROCESSING):
            global_stmts.append(Parser.parse_processing_direc(tkzr))

        # don't catch any errors here!
        # they should be caught by the Tokenizer runtime context
        script_mode = False
        while tkzr.current_token is not None:
            if tkzr.try_token_type(TokenType.DELIM_START_SCRIPT):
                assert (
                    script_mode is False
                ), "Encountered starting script delimiter, but previous script delimiter was not closed"
                script_mode = True
                tkzr.advance_pos()  # consume delimiter
                if tkzr.try_token_type(TokenType.NEWLINE):
                    tkzr.advance_pos()
            elif tkzr.try_token_type(TokenType.DELIM_END):
                assert (
                    script_mode is True
                ), "Ending script delimiter does not match any starting script delimiter"
                script_mode = False
                tkzr.advance_pos()  # consume delimiter
            elif tkzr.try_multiple_token_type(
                [TokenType.DELIM_START_OUTPUT, TokenType.FILE_TEXT]
            ):
                # parse output text as a global statement
                global_stmts.append(Parser.parse_output_text(tkzr))
            else:
                global_stmts.append(Parser.parse_global_stmt(tkzr))
        assert (
            script_mode is False
        ), "Script delimiter was not closed before the end of the codeblock"
        return Program(global_stmts)
