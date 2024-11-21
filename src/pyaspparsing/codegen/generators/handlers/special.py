# ProcessingDirective
# IncludeFile
# OutputText

from pathlib import Path
from ....ast.ast_types import (
    EvalExpr,
    LeftExpr,
    # special constructs
    ProcessingDirective,
    IncludeFile,
    OutputText,
    OutputDirective,
    OutputType,
)
from ....ast.ast_types.parser import Parser
from ...symbols.symbol import (
    ValueSymbol,
    ArraySymbol,
)
from ..codegen_state import CodegenState
from ..codegen_return import CodegenReturn
from ..codegen_reg import create_global_cg_func, codegen_global_stmt

__all__ = [
    "cg_processing_directive",
    "cg_include_file",
    "cg_output_text",
]


@create_global_cg_func(ProcessingDirective)
def cg_processing_directive(
    stmt: ProcessingDirective, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for processing directive

    Parameters
    ----------
    stmt : ProcessingDirective
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    cg_ret.append("Processing directive")
    return cg_ret


@create_global_cg_func(IncludeFile)
def cg_include_file(
    stmt: IncludeFile, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Handler for (unresolved) includes

    Parameters
    ----------
    stmt : IncludeFile
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    # try to include file
    inc_path = Path(stmt.include_path[1:-1])
    if (inc_prog := cg_state.lnk.request(inc_path)) is not None:
        for glob_st in inc_prog.global_stmt_list:
            if isinstance(glob_st, OutputText) and (
                len(glob_st.directives) == 0
                and len(glob_st.chunks) == 1
                and glob_st.chunks[0].isspace()
            ):
                # ignore output between statements if the output is exclusively whitespace
                continue
            cg_ret.combine(
                codegen_global_stmt(
                    (
                        Parser.reinterpret_output_block(glob_st)
                        if isinstance(glob_st, OutputText)
                        else glob_st
                    ),
                    cg_state,
                ),
                indent=False,
            )
    else:
        print(f"Unresolved include: {stmt.include_path}", file=cg_state.error_file)
    return cg_ret


@create_global_cg_func(OutputText)
def cg_output_text(
    stmt: OutputText, cg_state: CodegenState, cg_ret: CodegenReturn
) -> CodegenReturn:
    """Code generator for output text

    Parameters
    ----------
    stmt : OutputText
    cg_state : CodegenState
    cg_ret : CodegenReturn

    Returns
    -------
    CodegenReturn
    """
    if not (all(map(lambda x: x.isspace(), stmt.chunks)) and len(stmt.directives) == 0):
        for output in stmt.stitch():
            match output[0]:
                case OutputType.OUTPUT_RAW:
                    print(output[1], end="", file=cg_state.template_file)
                case OutputType.OUTPUT_DIRECTIVE:
                    # assert for type inference
                    assert isinstance(output[1], OutputDirective)
                    out_expr = output[1].output_expr
                    # check if the expression can be evaluated
                    if isinstance(out_expr, EvalExpr):
                        # print directly to template as string
                        print(
                            out_expr.str_cast().expr_value,
                            end="",
                            file=cg_state.template_file,
                        )
                        continue
                    elif isinstance(out_expr, LeftExpr):
                        # check if the left expression represents a value
                        res_out = cg_state.sym_table.resolve_symbol(
                            out_expr, cg_state.scope_mgr.current_environment
                        )
                        if len(res_out) == 1:
                            sym_out = res_out[0].symbol
                            if isinstance(sym_out, ValueSymbol) and isinstance(
                                sym_out.value, EvalExpr
                            ):
                                print(
                                    sym_out.value.str_cast().expr_value,
                                    end="",
                                    file=cg_state.template_file,
                                )
                                continue
                            elif isinstance(sym_out, ArraySymbol):
                                try:
                                    if isinstance(
                                        (sym_arr_val := sym_out.retrieve(out_expr)),
                                        EvalExpr,
                                    ):
                                        print(
                                            sym_arr_val.str_cast().expr_value,
                                            end="",
                                            file=cg_state.template_file,
                                        )
                                        continue
                                except AssertionError:
                                    # could not evaluate array indices
                                    pass
                    # register output expression
                    expr_name = cg_state.add_output_expr(output[1].output_expr)
                    print(
                        "{{- " + expr_name + " -}}", end="", file=cg_state.template_file
                    )
                    cg_ret.append(f"Create output expression {expr_name}")
    return cg_ret
