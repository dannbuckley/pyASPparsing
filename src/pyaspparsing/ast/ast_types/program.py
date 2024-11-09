"""program module"""

from typing import Generator
import attrs
from .parser import Parser
from ..tokenizer.token_types import TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import FormatterMixin, GlobalStmt


def generate_program(tkzr: Tokenizer) -> Generator[GlobalStmt, None, None]:
    """
    Parameters
    ----------
    tkzr : Tokenizer

    Yields
    -------
    GlobalStmt
    """
    # there may be output text before processing directive
    if tkzr.try_token_type(TokenType.FILE_TEXT):
        yield Parser.parse_output_text(tkzr)

    # if code has a processing directive,
    # it must be on the first code line
    if tkzr.try_token_type(TokenType.DELIM_START_PROCESSING):
        yield Parser.parse_processing_direc(tkzr)

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
        elif tkzr.try_token_type(TokenType.HTML_START_COMMENT):
            # could be either an include directive or output text (regular HTML comment)
            yield Parser.parse_html_comment(tkzr)
        elif tkzr.try_multiple_token_type(
            [TokenType.DELIM_START_OUTPUT, TokenType.FILE_TEXT]
        ):
            # parse output text as a global statement
            yield Parser.parse_output_text(tkzr)
        else:
            yield Parser.parse_global_stmt(tkzr)
    assert (
        script_mode is False
    ), "Script delimiter was not closed before the end of the codeblock"


@attrs.define(repr=False, slots=False)
class Program(FormatterMixin):
    """The starting symbol for the VBScript grammar.
    Defined on grammar line 267

    Attributes
    ----------
    global_stmt_list : List[GlobalStmt], default=[]
    """

    global_stmt_list: list[GlobalStmt] = attrs.field(default=attrs.Factory(list))

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer

        Returns
        -------
        Program
        """
        return Program(list(generate_program(tkzr)))
