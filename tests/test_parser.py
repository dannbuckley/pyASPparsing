from contextlib import ExitStack
import typing
import pytest
from pyaspparsing import ParserError
from pyaspparsing.parser import *
from pyaspparsing.ast_types import *


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
        (
            "Call HelloWorld()\n",  # no params
            CallStmt(
                LeftExpr(QualifiedID([Token.identifier(5, 15)]), [IndexOrParams()])
            ),
        ),
        (
            "Call HelloWorld(1)\n",  # Value ::= ConstExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams([IntLiteral(Token.int_literal(16, 17))])],
                )
            ),
        ),
        (
            "Call HelloWorld(a)\n",  # Value ::= LeftExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [LeftExpr(QualifiedID([Token.identifier(16, 17)]))]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld((1))\n",  # Value ::= '(' Expr ')'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams([IntLiteral(Token.int_literal(17, 18))])],
                )
            ),
        ),
        (
            'Call HelloWorld(1.0, "String param", #1970/01/01#)\n',  # default ConstExpr types
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                ConstExpr(Token.float_literal(16, 19)),
                                ConstExpr(Token.string_literal(21, 35)),
                                ConstExpr(Token.date_literal(37, 49)),
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1, &1, &H1)\n",  # different forms of IntLiteral
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                IntLiteral(Token.int_literal(16, 17)),
                                IntLiteral(Token.oct_literal(19, 21)),
                                IntLiteral(Token.hex_literal(23, 26)),
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(True, False)\n",  # different forms of BoolLiteral
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                BoolLiteral(Token.identifier(16, 20)),
                                BoolLiteral(Token.identifier(22, 27)),
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 ^ 2)\n",  # ExpExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                ExpExpr(
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(-1)\n",  # '-' UnaryExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                UnaryExpr(
                                    Token.symbol(16, 17),
                                    IntLiteral(Token.int_literal(17, 18)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(+1)\n",  # '+' UnaryExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                UnaryExpr(
                                    Token.symbol(16, 17),
                                    IntLiteral(Token.int_literal(17, 18)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 * 2)\n",  # MultExpr with '*'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                MultExpr(
                                    Token.symbol(18, 19),
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 / 2)\n",  # MultExpr with '/'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                MultExpr(
                                    Token.symbol(18, 19),
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 \\ 2)\n",  # IntDivExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                IntDivExpr(
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(3 Mod 2)\n",  # ModExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                ModExpr(
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(22, 23)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 + 2)\n",  # AddExpr with '+'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                AddExpr(
                                    Token.symbol(18, 19),
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 - 2)\n",  # AddExpr with '-'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                AddExpr(
                                    Token.symbol(18, 19),
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            'Call HelloWorld("Hello, " & "world!")\n',  # ConcatExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                ConcatExpr(
                                    ConstExpr(Token.string_literal(16, 25)),
                                    ConstExpr(Token.string_literal(28, 36)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(a Is Nothing)\n",  # CompareExpr with 'Is'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_IS,
                                    LeftExpr(QualifiedID([Token.identifier(16, 17)])),
                                    Nothing(Token.identifier(21, 28)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(a Is Not Nothing)\n",  # CompareExpr with 'Is'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_ISNOT,
                                    LeftExpr(QualifiedID([Token.identifier(16, 17)])),
                                    Nothing(Token.identifier(25, 32)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 >= 2)\n",  # CompareExpr with '>='
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_GTEQ,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(21, 22)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 => 2)\n",  # CompareExpr with '=>'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_EQGT,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(21, 22)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 <= 2)\n",  # CompareExpr with '<='
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_LTEQ,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(21, 22)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 =< 2)\n",  # CompareExpr with '=<'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_EQLT,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(21, 22)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 > 2)\n",  # CompareExpr with '>'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_GT,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 < 2)\n",  # CompareExpr with '<'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_LT,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 <> 2)\n",  # CompareExpr with '<>'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_LTGT,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(21, 22)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(1 = 2)\n",  # CompareExpr with '='
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                CompareExpr(
                                    CompareExprType.COMPARE_EQ,
                                    IntLiteral(Token.int_literal(16, 17)),
                                    IntLiteral(Token.int_literal(20, 21)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(Not False)\n",  # NotExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams([NotExpr(BoolLiteral(Token.identifier(20, 25)))])],
                )
            ),
        ),
        (
            "Call HelloWorld(Not Not False)\n",  # NotExpr optimization, ignore 'Not Not'
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams([BoolLiteral(Token.identifier(24, 29))])],
                )
            ),
        ),
        (
            "Call HelloWorld(True And False)\n",  # AndExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                AndExpr(
                                    BoolLiteral(Token.identifier(16, 20)),
                                    BoolLiteral(Token.identifier(25, 30)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(True Or False)\n",  # OrExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                OrExpr(
                                    BoolLiteral(Token.identifier(16, 20)),
                                    BoolLiteral(Token.identifier(24, 29)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(True Xor False)\n",  # XorExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                XorExpr(
                                    BoolLiteral(Token.identifier(16, 20)),
                                    BoolLiteral(Token.identifier(25, 30)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(True Eqv False)\n",  # EqvExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                EqvExpr(
                                    BoolLiteral(Token.identifier(16, 20)),
                                    BoolLiteral(Token.identifier(25, 30)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld(True Imp False)\n",  # ImpExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                ImpExpr(
                                    BoolLiteral(Token.identifier(16, 20)),
                                    BoolLiteral(Token.identifier(25, 30)),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            # should return as "(a Eqv b) Imp c"
            "Call HelloWorld(a Eqv b Imp c)\n",  # higher precedence -> lower precedence
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                ImpExpr(
                                    EqvExpr(
                                        LeftExpr(
                                            QualifiedID([Token.identifier(16, 17)])
                                        ),
                                        LeftExpr(
                                            QualifiedID([Token.identifier(22, 23)])
                                        ),
                                    ),
                                    LeftExpr(QualifiedID([Token.identifier(28, 29)])),
                                )
                            ]
                        )
                    ],
                )
            ),
        ),
        (
            # should return as "a Imp (b Eqv c)"
            "Call HelloWorld(a Imp b Eqv c)\n",  # lower precedence -> higher precedence
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(
                            [
                                ImpExpr(
                                    LeftExpr(QualifiedID([Token.identifier(16, 17)])),
                                    EqvExpr(
                                        LeftExpr(
                                            QualifiedID([Token.identifier(22, 23)])
                                        ),
                                        LeftExpr(
                                            QualifiedID([Token.identifier(28, 29)])
                                        ),
                                    ),
                                )
                            ]
                        )
                    ],
                )
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
