import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.program import Program


def test_parse_output_text():
    with Tokenizer("Written directly <%= variable %> to Response") as tkzr:
        prog = Program.from_tokenizer(tkzr)
        output_text = prog.global_stmt_list[0]
        assert isinstance(output_text, OutputText)
        assert len(output_text.chunks) == 2
        assert output_text.chunks[0] == Token.file_text(0, 17)
        assert output_text.chunks[1] == Token.file_text(32, 44)
        assert len(output_text.directives) == 1
        assert output_text.directives[0] == OutputDirective(
            slice(17, 32), LeftExpr(QualifiedID([Token.identifier(21, 29)]))
        )
        for i, (out_type, out_idx) in enumerate(
            [
                (OutputType.OUTPUT_RAW, 0),
                (OutputType.OUTPUT_DIRECTIVE, 0),
                (OutputType.OUTPUT_RAW, 1),
            ]
        ):
            match output_text.stitch_order[i]:
                case (st_type, st_idx):
                    assert st_type == out_type
                    assert st_idx == out_idx
                case _:
                    pytest.fail(
                        "Element of OutputText.stitch_order should be a tuple of (OutputType, int)"
                    )
