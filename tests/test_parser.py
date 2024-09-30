from contextlib import ExitStack
import typing
import pytest
from pyaspparsing import ParserError
from pyaspparsing.parser import *


@pytest.mark.parametrize(
    "stmt_code,stmt_type",
    [
        ("Option Explicit\n", OptionExplicit()),
        ("Class MyClass\nEnd Class\n", ClassDecl(ExtendedID(Token.identifier(6, 13)))),
        (
            "Dim my_var\n",
            VarDecl([VarName(ExtendedID(Token.identifier(4, 10)))]),
        ),
        (
            "Dim vara, var_b\n",
            VarDecl(
                [
                    VarName(ExtendedID(Token.identifier(4, 8))),
                    VarName(ExtendedID(Token.identifier(10, 15))),
                ]
            ),
        ),
        (
            "Dim my_array(3)\n",
            VarDecl(
                [
                    VarName(
                        ExtendedID(Token.identifier(4, 12)),
                        [Token.int_literal(13, 14)],
                    )
                ]
            ),
        ),
        (
            "Dim my_array()\n",
            VarDecl([VarName(ExtendedID(Token.identifier(4, 12)))]),
        ),
        (
            "Dim my_array(3,)\n",
            VarDecl(
                [
                    VarName(
                        ExtendedID(Token.identifier(4, 12)),
                        [Token.int_literal(13, 14)],
                    )
                ]
            ),
        ),
        (
            "Dim my_table(4, 6)\n",
            VarDecl(
                [
                    VarName(
                        ExtendedID(Token.identifier(4, 12)),
                        [
                            Token.int_literal(13, 14),
                            Token.int_literal(16, 17),
                        ],
                    )
                ]
            ),
        ),
        ("On Error Resume Next\n", ErrorStmt(resume_next=True)),
        (
            "On Error GoTo 0\n",
            ErrorStmt(goto_spec=Token.int_literal(14, 15)),
        ),
        ("Exit Do\n", ExitStmt(Token.identifier(5, 7))),
        ("Exit For\n", ExitStmt(Token.identifier(5, 8))),
        ("Exit Function\n", ExitStmt(Token.identifier(5, 13))),
        ("Exit Property\n", ExitStmt(Token.identifier(5, 13))),
        ("Exit Sub\n", ExitStmt(Token.identifier(5, 8))),
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
        ("Dim"),  # missing variable name and <NEWLINE>
        ("Dim myvar"),  # missing <NEWLINE>
        ("Dim myarray()"),  # missing <NEWLINE>
        ("Dim myarray("),  # missing ending ')' and <NEWLINE>
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
