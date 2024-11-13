"""codegen module"""

from io import StringIO
import sys
from typing import IO
from jinja2 import Environment
from ..ast.tokenizer.state_machine import Tokenizer
from ..ast.ast_types import (
    GlobalStmt,
    ProcessingDirective,
    OptionExplicit,
    ErrorStmt,
    FunctionDecl,
    SubDecl,
)
from .linker import Linker, generate_linked_program
from .generators import CodegenState, codegen_global_stmt


def generate_code(
    codeblock: str, lnk: Linker, suppress_exc: bool = True, exc_file: IO = sys.stdout
) -> CodegenState:
    """Separate codeblock into a template and a script

    Parameters
    ----------
    codeblock : str
    lnk : Linker
    suppress_exc : bool, default=True
    exc_file : IO, default=sys.stdout

    Returns
    -------
    CodegenState
    """
    cg_state = CodegenState(Environment(), StringIO(), StringIO(), StringIO())
    # separate function/sub declarations from other code
    other_st: list[GlobalStmt] = []
    with Tokenizer(codeblock, suppress_exc, exc_file) as tkzr:
        for glob_st in generate_linked_program(tkzr, lnk):
            if isinstance(
                glob_st,
                (ProcessingDirective, OptionExplicit, ErrorStmt, FunctionDecl, SubDecl),
            ):
                # handle setup code and function/sub declarations first
                # this alleviates a scope resolution issue since
                # functions can be declared AFTER they're used
                codegen_global_stmt(glob_st, cg_state, top_level=True)
            else:
                # defer consideration of other code until after all functions/subs declared
                other_st.append(glob_st)
        # declarations finished, go back over remaining code
        for remaining_st in other_st:
            codegen_global_stmt(remaining_st, cg_state, top_level=True)
    return cg_state
