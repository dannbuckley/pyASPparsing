"""codegen module"""

from io import StringIO
import sys
from typing import IO
from jinja2 import Environment
from ..ast.tokenizer.state_machine import Tokenizer
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
    with Tokenizer(codeblock, suppress_exc, exc_file) as tkzr:
        for glob_st in generate_linked_program(tkzr, lnk):
            codegen_global_stmt(glob_st, cg_state, top_level=True)
    return cg_state
