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
    OutputText,
)
from .linker import Linker, generate_linked_program
from .generators import codegen_global_stmt, CodegenState  # pylint: disable=E0401
from .scope import ScopeType
from .symbols import Response, Request, Server
from .symbols.functions import vbscript_builtin as vb_blt


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
    # initialize state object
    cg_state = CodegenState(Environment(), lnk, StringIO(), StringIO(), StringIO())
    cg_state.add_symbol(Response())
    cg_state.add_symbol(Request())
    cg_state.add_symbol(Server())
    for blt in filter(lambda x: x.find("builtin_", 0, 8) == 0, dir(vb_blt)):
        cg_state.add_symbol(getattr(vb_blt, blt)())
    # all script data should be handled in a separate "user" scope
    cg_state.scope_mgr.enter_scope(ScopeType.SCOPE_SCRIPT_USER)
    # separate function/sub declarations from other code
    other_st: list[GlobalStmt] = []
    with Tokenizer(codeblock, suppress_exc, exc_file) as tkzr:
        # file contains user-defined functions/subs?
        user_methods = False
        for glob_st in generate_linked_program(tkzr, lnk):
            if isinstance(
                glob_st,
                (ProcessingDirective, OptionExplicit, ErrorStmt, FunctionDecl, SubDecl),
            ):
                # handle setup code and function/sub declarations first
                # this alleviates a scope resolution issue since
                # functions can be declared AFTER they're used
                codegen_global_stmt(glob_st, cg_state, top_level=True)
                if not user_methods:
                    user_methods = True
            elif isinstance(glob_st, OutputText):
                if (
                    len(glob_st.directives) == 0
                    and len(glob_st.chunks) == 1
                    and glob_st.chunks[0].isspace()
                ):
                    # ignore output between statements if the output is exclusively whitespace
                    continue
                other_st.append(glob_st)
            else:
                # defer consideration of other code until after all functions/subs declared
                other_st.append(glob_st)
        if user_methods and len(other_st) > 0:
            # add a blank line for readability
            print("\n", end="", file=cg_state.script_file)
        # declarations finished, go back over remaining code
        for remaining_st in other_st:
            codegen_global_stmt(remaining_st, cg_state, top_level=True)
    if cg_state.in_script_block:
        cg_state.end_script_block()
    return cg_state
