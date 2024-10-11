import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parse_expressions import ExpressionParser


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("1.0E3", ConstExpr(Token.float_literal(3, 8))),
        ('"Hello, world!"', ConstExpr(Token.string_literal(3, 18))),
        ("#1970/01/01#", ConstExpr(Token.date_literal(3, 15))),
        ("0", IntLiteral(Token.int_literal(3, 4))),
        ("&H7F", IntLiteral(Token.hex_literal(3, 7))),
        ("&777", IntLiteral(Token.oct_literal(3, 7))),
        ("True", BoolLiteral(Token.identifier(3, 7))),
        ("False", BoolLiteral(Token.identifier(3, 8))),
        ("Nothing", Nothing(Token.identifier(3, 10))),
        ("Null", Nothing(Token.identifier(3, 7))),
        ("Empty", Nothing(Token.identifier(3, 8))),
    ],
)
def test_parse_const_expr(expr_code: str, expr_val: Expr):
    with Tokenizer(f"<%={expr_code}%>", False) as tkzr:
        tkzr.advance_pos()
        const_expr: Expr = ExpressionParser.parse_const_expr(tkzr)
        assert const_expr == expr_val


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("a", LeftExpr(QualifiedID([Token.identifier(3, 4)]))),
        (
            "a(1,, 3)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 4)]),
                [
                    IndexOrParams(
                        [
                            IntLiteral(Token.int_literal(5, 6)),
                            None,
                            IntLiteral(Token.int_literal(9, 10)),
                        ]
                    )
                ],
            ),
        ),
        (
            "a().b(1,, 3)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 4)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(6, 8, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(9, 10)),
                                    None,
                                    IntLiteral(Token.int_literal(13, 14)),
                                ]
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            "Hello.World()",
            LeftExpr(
                QualifiedID(
                    [Token.identifier(3, 9, dot_end=True), Token.identifier(9, 14)]
                ),
                [IndexOrParams()],
            ),
        ),
        (
            "HelloWorld()",
            LeftExpr(QualifiedID([Token.identifier(3, 13)]), [IndexOrParams()]),
        ),
        (
            "HelloWorld(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams([IntLiteral(Token.int_literal(14, 15))])],
            ),
        ),
        (
            "HelloWorld((1))",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams([IntLiteral(Token.int_literal(15, 16))])],
            ),
        ),
        (
            "HelloWorld(a)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams([LeftExpr(QualifiedID([Token.identifier(14, 15)]))])],
            ),
        ),
        (
            "HelloWorld()()",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(), IndexOrParams()],
            ),
        ),
        (
            "HelloWorld()(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [
                    IndexOrParams(),
                    IndexOrParams([IntLiteral(Token.int_literal(16, 17))]),
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()()",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [IndexOrParams(), IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [IndexOrParams([IntLiteral(Token.int_literal(28, 29))])],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning(1, 2)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(28, 29)),
                                    IntLiteral(Token.int_literal(31, 32)),
                                ]
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()(1)",
            LeftExpr(
                QualifiedID([Token.identifier(3, 13)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(15, 27, dot_start=True)]),
                        [
                            IndexOrParams(),
                            IndexOrParams([IntLiteral(Token.int_literal(30, 31))]),
                        ],
                    )
                ],
            ),
        ),
    ],
)
def test_parse_left_expr(expr_code: str, expr_val: Expr):
    with Tokenizer(f"<%={expr_code}%>", False) as tkzr:
        tkzr.advance_pos()
        left_expr: Expr = ExpressionParser.parse_left_expr(tkzr)
        assert left_expr == expr_val


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "1 ^ 2",
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 ^ 2 ^ 3",
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)), IntLiteral(Token.int_literal(11, 12))
            ),
        ),
        (
            "(1 ^ 2) ^ 3",
            ExpExpr(
                IntLiteral(Token.int_literal(4, 5)), IntLiteral(Token.int_literal(8, 9))
            ),
            IntLiteral(Token.int_literal(13, 14)),
        ),
        (
            "1 ^ 2 ^ 3 ^ 4",
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)),
                ExpExpr(
                    IntLiteral(Token.int_literal(11, 12)),
                    IntLiteral(Token.int_literal(15, 16)),
                ),
            ),
        ),
    ],
)
def test_parse_exp_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        exp_expr: ExpExpr = ExpressionParser.parse_exp_expr(tkzr)
        assert exp_expr.left == exp_left
        assert exp_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_sign,exp_term",
    [
        ("-1", Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
        ("+1", Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
        (
            "+-1",
            Token.symbol(3, 4),
            UnaryExpr(Token.symbol(4, 5), IntLiteral(Token.int_literal(5, 6))),
        ),
        (
            "-(1 ^ 2)",
            Token.symbol(3, 4),
            ExpExpr(
                IntLiteral(Token.int_literal(5, 6)), IntLiteral(Token.int_literal(9, 10))
            ),
        ),
    ],
)
def test_parse_unary_expr(exp_code: str, exp_sign: Token, exp_term: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        unary_expr: UnaryExpr = ExpressionParser.parse_unary_expr(tkzr)
        assert unary_expr.sign == exp_sign
        assert unary_expr.term == exp_term


@pytest.mark.parametrize(
    "exp_code,exp_op,exp_left,exp_right",
    [
        (
            "1 * 2",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 / 2",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 * 2 / 3",
            Token.symbol(9, 10),
            MultExpr(
                Token.symbol(5, 6),
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "1 * (2 / 3)",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            MultExpr(
                Token.symbol(10, 11),
                IntLiteral(Token.int_literal(8, 9)),
                IntLiteral(Token.int_literal(12, 13)),
            ),
        ),
        (
            "1 * 2 / 3 * 4",
            Token.symbol(13, 14),
            MultExpr(
                Token.symbol(9, 10),
                MultExpr(
                    Token.symbol(5, 6),
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                IntLiteral(Token.int_literal(11, 12)),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "-1 * 2",
            Token.symbol(6, 7),
            UnaryExpr(Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 * -2",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            UnaryExpr(Token.symbol(7, 8), IntLiteral(Token.int_literal(8, 9))),
        ),
        (
            "-1 * -2",
            Token.symbol(6, 7),
            UnaryExpr(Token.symbol(3, 4), IntLiteral(Token.int_literal(4, 5))),
            UnaryExpr(Token.symbol(8, 9), IntLiteral(Token.int_literal(9, 10))),
        ),
        (
            "1 ^ 2 * 3",
            Token.symbol(9, 10),
            ExpExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "1 * 2 ^ 3",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            ExpExpr(
                IntLiteral(Token.int_literal(7, 8)), IntLiteral(Token.int_literal(11, 12))
            ),
        ),
        (
            "1 ^ 2 * 3 ^ 4",
            Token.symbol(9, 10),
            ExpExpr(
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            ExpExpr(
                IntLiteral(Token.int_literal(11, 12)),
                IntLiteral(Token.int_literal(15, 16)),
            ),
        ),
    ],
)
def test_parse_mult_expr(exp_code: str, exp_op: Token, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mult_expr: MultExpr = ExpressionParser.parse_mult_expr(tkzr)
        assert mult_expr.op == exp_op
        assert mult_expr.left == exp_left
        assert mult_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "4 \\ 2",
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "4 \\ 2 \\ 1",
            IntDivExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "4 \\ (2 \\ 1)",
            IntLiteral(Token.int_literal(3, 4)),
            IntDivExpr(
                IntLiteral(Token.int_literal(8, 9)),
                IntLiteral(Token.int_literal(12, 13)),
            ),
        ),
        (
            "8 \\ 4 \\ 2 \\ 1",
            IntDivExpr(
                IntDivExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                IntLiteral(Token.int_literal(11, 12)),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "2 * 4 \\ 8",
            MultExpr(
                Token.symbol(5, 6),
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "4 \\ 2 * 8",
            IntLiteral(Token.int_literal(3, 4)),
            MultExpr(
                Token.symbol(9, 10),
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(11, 12)),
            ),
        ),
        (
            "2 * 4 \\ 4 * 2",
            MultExpr(
                Token.symbol(5, 6),
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            MultExpr(
                Token.symbol(13, 14),
                IntLiteral(Token.int_literal(11, 12)),
                IntLiteral(Token.int_literal(15, 16)),
            ),
        ),
    ],
)
def test_parse_int_div_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        int_div_expr: IntDivExpr = ExpressionParser.parse_int_div_expr(tkzr)
        assert int_div_expr.left == exp_left
        assert int_div_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "6 Mod 2",
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(9, 10)),
        ),
        (
            "6 Mod 4 Mod 2",
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(9, 10))
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "6 Mod (4 Mod 2)",
            IntLiteral(Token.int_literal(3, 4)),
            ModExpr(
                IntLiteral(Token.int_literal(10, 11)),
                IntLiteral(Token.int_literal(16, 17)),
            ),
        ),
        (
            "8 Mod 6 Mod 4 Mod 2",
            ModExpr(
                ModExpr(
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(9, 10)),
                ),
                IntLiteral(Token.int_literal(15, 16)),
            ),
            IntLiteral(Token.int_literal(21, 22)),
        ),
        (
            "6 \\ 2 Mod 4",
            IntDivExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntLiteral(Token.int_literal(13, 14)),
        ),
        (
            "6 Mod 4 \\ 2",
            IntLiteral(Token.int_literal(3, 4)),
            IntDivExpr(
                IntLiteral(Token.int_literal(9, 10)),
                IntLiteral(Token.int_literal(13, 14)),
            ),
        ),
        (
            "6 \\ 2 Mod 8 \\ 4",
            IntDivExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(7, 8))
            ),
            IntDivExpr(
                IntLiteral(Token.int_literal(13, 14)),
                IntLiteral(Token.int_literal(17, 18)),
            ),
        ),
    ],
)
def test_parse_mod_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        mod_expr: ModExpr = ExpressionParser.parse_mod_expr(tkzr)
        assert mod_expr.left == exp_left
        assert mod_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_op,exp_left,exp_right",
    [
        (
            "1 + 2",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 - 2",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 + 2 - 3",
            Token.symbol(9, 10),
            AddExpr(
                Token.symbol(5, 6),
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            IntLiteral(Token.int_literal(11, 12)),
        ),
        (
            "1 + (2 - 3)",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            AddExpr(
                Token.symbol(10, 11),
                IntLiteral(Token.int_literal(8, 9)),
                IntLiteral(Token.int_literal(12, 13)),
            ),
        ),
        (
            "1 + 2 - 3 + 4",
            Token.symbol(13, 14),
            AddExpr(
                Token.symbol(9, 10),
                AddExpr(
                    Token.symbol(5, 6),
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                IntLiteral(Token.int_literal(11, 12)),
            ),
            IntLiteral(Token.int_literal(15, 16)),
        ),
        (
            "2 Mod 1 + 3",
            Token.symbol(11, 12),
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(9, 10))
            ),
            IntLiteral(Token.int_literal(13, 14)),
        ),
        (
            "2 + 3 Mod 1",
            Token.symbol(5, 6),
            IntLiteral(Token.int_literal(3, 4)),
            ModExpr(
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(13, 14)),
            ),
        ),
        (
            "2 Mod 1 + 3 Mod 1",
            Token.symbol(11, 12),
            ModExpr(
                IntLiteral(Token.int_literal(3, 4)), IntLiteral(Token.int_literal(9, 10))
            ),
            ModExpr(
                IntLiteral(Token.int_literal(13, 14)),
                IntLiteral(Token.int_literal(19, 20)),
            ),
        ),
    ],
)
def test_parse_add_expr(exp_code: str, exp_op: Token, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        add_expr: AddExpr = ExpressionParser.parse_add_expr(tkzr)
        assert add_expr.op == exp_op
        assert add_expr.left == exp_left
        assert add_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            '"Hello, " & "world!"',
            ConstExpr(Token.string_literal(3, 12)),
            ConstExpr(Token.string_literal(15, 23)),
        )
    ],
)
def test_parse_concat_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        concat_expr: ConcatExpr = ExpressionParser.parse_concat_expr(tkzr)
        assert concat_expr.left == exp_left
        assert concat_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_cmp_type,exp_left,exp_right",
    [
        (
            "1 Is 1",
            CompareExprType.COMPARE_IS,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 Is Not 1",
            CompareExprType.COMPARE_ISNOT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(12, 13)),
        ),
        (
            "1 >= 1",
            CompareExprType.COMPARE_GTEQ,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 => 1",
            CompareExprType.COMPARE_EQGT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 <= 1",
            CompareExprType.COMPARE_LTEQ,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 =< 1",
            CompareExprType.COMPARE_EQLT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 > 1",
            CompareExprType.COMPARE_GT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 < 1",
            CompareExprType.COMPARE_LT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
        (
            "1 <> 1",
            CompareExprType.COMPARE_LTGT,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(8, 9)),
        ),
        (
            "1 = 1",
            CompareExprType.COMPARE_EQ,
            IntLiteral(Token.int_literal(3, 4)),
            IntLiteral(Token.int_literal(7, 8)),
        ),
    ],
)
def test_parse_compare_expr(
    exp_code: str, exp_cmp_type: CompareExprType, exp_left: Expr, exp_right: Expr
):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        compare_expr: CompareExpr = ExpressionParser.parse_compare_expr(tkzr)
        assert compare_expr.cmp_type == exp_cmp_type
        assert compare_expr.left == exp_left
        assert compare_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_term",
    [
        ("Not True", BoolLiteral(Token.identifier(7, 11))),
        (
            "Not 1 > 1",
            CompareExpr(
                CompareExprType.COMPARE_GT,
                IntLiteral(Token.int_literal(7, 8)),
                IntLiteral(Token.int_literal(11, 12)),
            ),
        ),
    ],
)
def test_parse_not_expr(exp_code: str, exp_term: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        not_expr: NotExpr = ExpressionParser.parse_not_expr(tkzr)
        assert not_expr.term == exp_term


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True And False",
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 17)),
        ),
        (
            "True And False And True",
            AndExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True And (False And True)",
            BoolLiteral(Token.identifier(3, 7)),
            AndExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True And False And True And False",
            AndExpr(
                AndExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "Not False And True",
            NotExpr(BoolLiteral(Token.identifier(7, 12))),
            BoolLiteral(Token.identifier(17, 21)),
        ),
        (
            "True And Not False",
            BoolLiteral(Token.identifier(3, 7)),
            NotExpr(BoolLiteral(Token.identifier(16, 21))),
        ),
        (
            "Not False And Not False",
            NotExpr(BoolLiteral(Token.identifier(7, 12))),
            NotExpr(BoolLiteral(Token.identifier(21, 26))),
        ),
        (
            "Not Not True And True",
            BoolLiteral(Token.identifier(11, 15)),  # 'Not Not' ignored
            BoolLiteral(Token.identifier(20, 24)),
        ),
        (
            "1 = 1 And True",
            CompareExpr(
                CompareExprType.COMPARE_EQ,
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            BoolLiteral(Token.identifier(13, 17)),
        ),
        (
            "True And 1 = 1",
            BoolLiteral(Token.identifier(3, 7)),
            CompareExpr(
                CompareExprType.COMPARE_EQ,
                IntLiteral(Token.int_literal(12, 13)),
                IntLiteral(Token.int_literal(16, 17)),
            ),
        ),
        (
            "1 = 1 And 2 = 2",
            CompareExpr(
                CompareExprType.COMPARE_EQ,
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            CompareExpr(
                CompareExprType.COMPARE_EQ,
                IntLiteral(Token.int_literal(13, 14)),
                IntLiteral(Token.int_literal(17, 18)),
            ),
        ),
        (
            "Not 1 <> 1 And 2 = 2",
            NotExpr(
                CompareExpr(
                    CompareExprType.COMPARE_LTGT,
                    IntLiteral(Token.int_literal(7, 8)),
                    IntLiteral(Token.int_literal(12, 13)),
                )
            ),
            CompareExpr(
                CompareExprType.COMPARE_EQ,
                IntLiteral(Token.int_literal(18, 19)),
                IntLiteral(Token.int_literal(22, 23)),
            ),
        ),
        (
            "1 = 1 And Not 2 <> 2",
            CompareExpr(
                CompareExprType.COMPARE_EQ,
                IntLiteral(Token.int_literal(3, 4)),
                IntLiteral(Token.int_literal(7, 8)),
            ),
            NotExpr(
                CompareExpr(
                    CompareExprType.COMPARE_LTGT,
                    IntLiteral(Token.int_literal(17, 18)),
                    IntLiteral(Token.int_literal(22, 23)),
                )
            ),
        ),
        (
            "Not 1 <> 1 And Not 2 <> 2",
            NotExpr(
                CompareExpr(
                    CompareExprType.COMPARE_LTGT,
                    IntLiteral(Token.int_literal(7, 8)),
                    IntLiteral(Token.int_literal(12, 13)),
                )
            ),
            NotExpr(
                CompareExpr(
                    CompareExprType.COMPARE_LTGT,
                    IntLiteral(Token.int_literal(22, 23)),
                    IntLiteral(Token.int_literal(27, 28)),
                )
            ),
        ),
    ],
)
def test_parse_and_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        and_expr: AndExpr = ExpressionParser.parse_and_expr(tkzr)
        assert and_expr.left == exp_left
        assert and_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True Or False",
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(11, 16)),
        ),
        (
            "True Or False Or True",
            OrExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(11, 16)),
            ),
            BoolLiteral(Token.identifier(20, 24)),
        ),
        (
            "True Or (False Or True)",
            BoolLiteral(Token.identifier(3, 7)),
            OrExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(21, 25)),
            ),
        ),
        (
            "True Or False Or True Or False",
            OrExpr(
                OrExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(11, 16)),
                ),
                BoolLiteral(Token.identifier(20, 24)),
            ),
            BoolLiteral(Token.identifier(28, 33)),
        ),
        (
            "True And False Or True",
            AndExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(21, 25)),
        ),
        (
            "True Or False And True",
            BoolLiteral(Token.identifier(3, 7)),
            AndExpr(
                BoolLiteral(Token.identifier(11, 16)),
                BoolLiteral(Token.identifier(21, 25)),
            ),
        ),
        (
            "True And False Or True And False",
            AndExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            AndExpr(
                BoolLiteral(Token.identifier(21, 25)),
                BoolLiteral(Token.identifier(30, 35)),
            ),
        ),
    ],
)
def test_parse_or_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        or_expr: OrExpr = ExpressionParser.parse_or_expr(tkzr)
        assert or_expr.left == exp_left
        assert or_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True Xor False",
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 17)),
        ),
        (
            "True Xor False Xor True",
            XorExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Xor (False Xor True)",
            BoolLiteral(Token.identifier(3, 7)),
            XorExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True Xor False Xor True Xor False",
            XorExpr(
                XorExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "True Or False Xor True",
            OrExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(11, 16)),
            ),
            BoolLiteral(Token.identifier(21, 25)),
        ),
        (
            "True Xor False Or True",
            BoolLiteral(Token.identifier(3, 7)),
            OrExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(21, 25)),
            ),
        ),
        (
            "True Or False Xor True Or False",
            OrExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(11, 16)),
            ),
            OrExpr(
                BoolLiteral(Token.identifier(21, 25)),
                BoolLiteral(Token.identifier(29, 34)),
            ),
        ),
    ],
)
def test_parse_xor_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        xor_expr: XorExpr = ExpressionParser.parse_xor_expr(tkzr)
        assert xor_expr.left == exp_left
        assert xor_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True Eqv True",
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 16)),
        ),
        (
            "True Eqv False Eqv True",
            EqvExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Eqv (False Eqv True)",
            BoolLiteral(Token.identifier(3, 7)),
            EqvExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True Eqv False Eqv True Eqv False",
            EqvExpr(
                EqvExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "True Xor False Eqv True",
            XorExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Eqv False Xor True",
            BoolLiteral(Token.identifier(3, 7)),
            XorExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(22, 26)),
            ),
        ),
        (
            "True Xor False Eqv True Xor False",
            XorExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            XorExpr(
                BoolLiteral(Token.identifier(22, 26)),
                BoolLiteral(Token.identifier(31, 36)),
            ),
        ),
    ],
)
def test_parse_eqv_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        eqv_expr: EqvExpr = ExpressionParser.parse_eqv_expr(tkzr)
        assert eqv_expr.left == exp_left
        assert eqv_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True Imp True",
            BoolLiteral(Token.identifier(3, 7)),
            BoolLiteral(Token.identifier(12, 16)),
        ),
        (
            "True Imp False Imp True",
            ImpExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Imp (False Imp True)",
            BoolLiteral(Token.identifier(3, 7)),
            ImpExpr(
                BoolLiteral(Token.identifier(13, 18)),
                BoolLiteral(Token.identifier(23, 27)),
            ),
        ),
        (
            "True Imp False Imp True Imp False",
            ImpExpr(
                ImpExpr(
                    BoolLiteral(Token.identifier(3, 7)),
                    BoolLiteral(Token.identifier(12, 17)),
                ),
                BoolLiteral(Token.identifier(22, 26)),
            ),
            BoolLiteral(Token.identifier(31, 36)),
        ),
        (
            "True Eqv False Imp True",
            EqvExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            BoolLiteral(Token.identifier(22, 26)),
        ),
        (
            "True Imp False Eqv True",
            BoolLiteral(Token.identifier(3, 7)),
            EqvExpr(
                BoolLiteral(Token.identifier(12, 17)),
                BoolLiteral(Token.identifier(22, 26)),
            ),
        ),
        (
            "True Eqv False Imp True Eqv False",
            EqvExpr(
                BoolLiteral(Token.identifier(3, 7)),
                BoolLiteral(Token.identifier(12, 17)),
            ),
            EqvExpr(
                BoolLiteral(Token.identifier(22, 26)),
                BoolLiteral(Token.identifier(31, 36)),
            ),
        ),
    ],
)
def test_parse_imp_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(f"<%={exp_code}%>", False) as tkzr:
        tkzr.advance_pos()
        imp_expr: ImpExpr = ExpressionParser.parse_imp_expr(tkzr)
        assert imp_expr.left == exp_left
        assert imp_expr.right == exp_right
