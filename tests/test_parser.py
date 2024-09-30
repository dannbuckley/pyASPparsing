from contextlib import ExitStack
import typing
import pytest
from pyaspparsing import ParserError
from pyaspparsing.parser import *


@pytest.mark.parametrize(
    "stmt_code,stmt_type",
    [
        ("Option Explicit\n", OptionExplicit()),
        ("On Error Resume Next\n", ErrorStmt(resume_next=True)),
        (
            "On Error GoTo 0\n",
            ErrorStmt(goto_spec=Token(TokenType.LITERAL_INT, slice(14, 15))),
        ),
        ("Exit Do\n", ExitStmt(Token(TokenType.IDENTIFIER, slice(5, 7)))),
        ("Exit For\n", ExitStmt(Token(TokenType.IDENTIFIER, slice(5, 8)))),
        ("Exit Function\n", ExitStmt(Token(TokenType.IDENTIFIER, slice(5, 13)))),
        ("Exit Property\n", ExitStmt(Token(TokenType.IDENTIFIER, slice(5, 13)))),
        ("Exit Sub\n", ExitStmt(Token(TokenType.IDENTIFIER, slice(5, 8)))),
    ],
)
def test_valid_global_stmt(stmt_code: str, stmt_type: GlobalStmt):
    # don't suppress exceptions
    with Parser(stmt_code, False) as prsr:
        prog = prsr.parse()
        assert len(prog.global_stmt_list) == 1
        assert prog.global_stmt_list[0] == stmt_type


@pytest.mark.parametrize(
    "stmt_code",
    [
        ("Option"),  # missing 'Explicit' <NEWLINE>
        ("Option Explicit"),  # missing <NEWLINE>
        ("On"),  # missing Error { Resume Next | Goto IntLiteral } <NEWLINE>
        ("On Error"),  # missing { Resume Next | GoTo IntLiteral } <NEWLINE>
        ("On Error Resume"),  # missing 'Next' <NEWLINE>
        ("On Error Resume Next"),  # missing <NEWLINE>
        ("On Error GoTo"),  # missing IntLiteral <NEWLINE>
        ("On Error GoTo 0"),  # missing <NEWLINE>
        ("Exit"),  # missing exit type and <NEWLINE>
        ("Exit Do"),  # missing <NEWLINE>
        ("Exit Reality\n"),  # improper exit type
    ],
)
def test_invalid_global_stmt(stmt_code: str):
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ParserError))
        # parse code (don't suppress exception)
        prsr = stack.enter_context(Parser(stmt_code, False))
        prsr.parse()