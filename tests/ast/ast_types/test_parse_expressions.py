import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.parse_expressions import ExpressionParser


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("1.0E3", ConstExpr(Token.float_literal(0, 5))),
        ('"Hello, world!"', ConstExpr(Token.string_literal(0, 15))),
        ("#1970/01/01#", ConstExpr(Token.date_literal(0, 12))),
        ("0", IntLiteral(Token.int_literal(0, 1))),
        ("&H7F", IntLiteral(Token.int_literal(0, 4))),
        ("&777", IntLiteral(Token.int_literal(0, 4))),
        ("True", BoolLiteral(Token.identifier(0, 4))),
        ("False", BoolLiteral(Token.identifier(0, 5))),
        ("Nothing", Nothing(Token.identifier(0, 7))),
        ("Null", Nothing(Token.identifier(0, 4))),
        ("Empty", Nothing(Token.identifier(0, 5))),
    ],
)
def test_parse_const_expr(expr_code: str, expr_val: Expr):
    with Tokenizer(expr_code) as tkzr:
        const_expr: Expr = ExpressionParser.parse_const_expr(tkzr)
        assert const_expr == expr_val


@pytest.mark.parametrize(
    "expr_code,expr_val",
    [
        ("a", LeftExpr(QualifiedID([Token.identifier(0, 1)]))),
        (
            "a(1,, 3)",
            LeftExpr(
                QualifiedID([Token.identifier(0, 1)]),
                [
                    IndexOrParams(
                        [
                            IntLiteral(Token.int_literal(2, 3)),
                            None,
                            IntLiteral(Token.int_literal(6, 7)),
                        ]
                    )
                ],
            ),
        ),
        (
            "a().b(1,, 3)",
            LeftExpr(
                QualifiedID([Token.identifier(0, 1)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(3, 5, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(6, 7)),
                                    None,
                                    IntLiteral(Token.int_literal(10, 11)),
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
                    [Token.identifier(0, 6, dot_end=True), Token.identifier(6, 11)]
                ),
                [IndexOrParams()],
            ),
        ),
        (
            "HelloWorld()",
            LeftExpr(QualifiedID([Token.identifier(0, 10)]), [IndexOrParams()]),
        ),
        (
            "HelloWorld(1)",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams([IntLiteral(Token.int_literal(11, 12))])],
            ),
        ),
        (
            "HelloWorld((1))",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams([IntLiteral(Token.int_literal(12, 13))])],
            ),
        ),
        (
            "HelloWorld(a)",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams([LeftExpr(QualifiedID([Token.identifier(11, 12)]))])],
            ),
        ),
        (
            "HelloWorld()()",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams(), IndexOrParams()],
            ),
        ),
        (
            "HelloWorld()(1)",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [
                    IndexOrParams(),
                    IndexOrParams([IntLiteral(Token.int_literal(13, 14))]),
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(12, 24, dot_start=True)]),
                        [IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning()()",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(12, 24, dot_start=True)]),
                        [IndexOrParams(), IndexOrParams()],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning(1)",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(12, 24, dot_start=True)]),
                        [IndexOrParams([IntLiteral(Token.int_literal(25, 26))])],
                    )
                ],
            ),
        ),
        (
            "HelloWorld().GoodMorning(1, 2)",
            LeftExpr(
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(12, 24, dot_start=True)]),
                        [
                            IndexOrParams(
                                [
                                    IntLiteral(Token.int_literal(25, 26)),
                                    IntLiteral(Token.int_literal(28, 29)),
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
                QualifiedID([Token.identifier(0, 10)]),
                [IndexOrParams(dot=True)],
                [
                    LeftExprTail(
                        QualifiedID([Token.identifier(12, 24, dot_start=True)]),
                        [
                            IndexOrParams(),
                            IndexOrParams([IntLiteral(Token.int_literal(27, 28))]),
                        ],
                    )
                ],
            ),
        ),
    ],
)
def test_parse_left_expr(expr_code: str, expr_val: Expr):
    with Tokenizer(expr_code) as tkzr:
        left_expr: Expr = ExpressionParser.parse_left_expr(tkzr)
        assert left_expr == expr_val


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "1 ^ 2",
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(4, 5)),
        )
    ],
)
def test_parse_exp_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        exp_expr: ExpExpr = ExpressionParser.parse_exp_expr(tkzr)
        assert exp_expr.left == exp_left
        assert exp_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_sign,exp_term",
    [("-1", Token.symbol(0, 1), IntLiteral(Token.int_literal(1, 2)))],
)
def test_parse_unary_expr(exp_code: str, exp_sign: Token, exp_term: Expr):
    with Tokenizer(exp_code) as tkzr:
        unary_expr: UnaryExpr = ExpressionParser.parse_unary_expr(tkzr)
        assert unary_expr.sign == exp_sign
        assert unary_expr.term == exp_term


@pytest.mark.parametrize(
    "exp_code,exp_op,exp_left,exp_right",
    [
        (
            "1 * 2",
            Token.symbol(2, 3),
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(4, 5)),
        )
    ],
)
def test_parse_mult_expr(exp_code: str, exp_op: Token, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        mult_expr: MultExpr = ExpressionParser.parse_mult_expr(tkzr)
        assert mult_expr.op == exp_op
        assert mult_expr.left == exp_left
        assert mult_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "4 \\ 2",
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(4, 5)),
        )
    ],
)
def test_parse_int_div_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        int_div_expr: IntDivExpr = ExpressionParser.parse_int_div_expr(tkzr)
        assert int_div_expr.left == exp_left
        assert int_div_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "6 Mod 2",
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(6, 7)),
        )
    ],
)
def test_parse_mod_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        mod_expr: ModExpr = ExpressionParser.parse_mod_expr(tkzr)
        assert mod_expr.left == exp_left
        assert mod_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_op,exp_left,exp_right",
    [
        (
            "1 + 2",
            Token.symbol(2, 3),
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(4, 5)),
        )
    ],
)
def test_parse_add_expr(exp_code: str, exp_op: Token, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        add_expr: AddExpr = ExpressionParser.parse_add_expr(tkzr)
        assert add_expr.op == exp_op
        assert add_expr.left == exp_left
        assert add_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            '"Hello, " & "world!"',
            ConstExpr(Token.string_literal(0, 9)),
            ConstExpr(Token.string_literal(12, 20)),
        )
    ],
)
def test_parse_concat_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        concat_expr: ConcatExpr = ExpressionParser.parse_concat_expr(tkzr)
        assert concat_expr.left == exp_left
        assert concat_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_cmp_type,exp_left,exp_right",
    [
        (
            "1 <= 1",
            CompareExprType.COMPARE_LTEQ,
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(5, 6)),
        )
    ],
)
def test_parse_compare_expr(
    exp_code: str, exp_cmp_type: CompareExprType, exp_left: Expr, exp_right: Expr
):
    with Tokenizer(exp_code) as tkzr:
        compare_expr: CompareExpr = ExpressionParser.parse_compare_expr(tkzr)
        assert compare_expr.cmp_type == exp_cmp_type
        assert compare_expr.left == exp_left
        assert compare_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_term", [("Not True", BoolLiteral(Token.identifier(4, 8)))]
)
def test_parse_not_expr(exp_code: str, exp_term: Expr):
    with Tokenizer(exp_code) as tkzr:
        not_expr: NotExpr = ExpressionParser.parse_not_expr(tkzr)
        assert not_expr.term == exp_term


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True And False",
            BoolLiteral(Token.identifier(0, 4)),
            BoolLiteral(Token.identifier(9, 14)),
        )
    ],
)
def test_parse_and_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        and_expr: AndExpr = ExpressionParser.parse_and_expr(tkzr)
        assert and_expr.left == exp_left
        assert and_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True Or False",
            BoolLiteral(Token.identifier(0, 4)),
            BoolLiteral(Token.identifier(8, 13)),
        )
    ],
)
def test_parse_or_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        or_expr: OrExpr = ExpressionParser.parse_or_expr(tkzr)
        assert or_expr.left == exp_left
        assert or_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "True Xor False",
            BoolLiteral(Token.identifier(0, 4)),
            BoolLiteral(Token.identifier(9, 14)),
        )
    ],
)
def test_parse_xor_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        xor_expr: XorExpr = ExpressionParser.parse_xor_expr(tkzr)
        assert xor_expr.left == exp_left
        assert xor_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "1 Eqv 1",
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(6, 7)),
        )
    ],
)
def test_parse_eqv_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        eqv_expr: EqvExpr = ExpressionParser.parse_eqv_expr(tkzr)
        assert eqv_expr.left == exp_left
        assert eqv_expr.right == exp_right


@pytest.mark.parametrize(
    "exp_code,exp_left,exp_right",
    [
        (
            "1 Imp 1",
            IntLiteral(Token.int_literal(0, 1)),
            IntLiteral(Token.int_literal(6, 7)),
        )
    ],
)
def test_parse_imp_expr(exp_code: str, exp_left: Expr, exp_right: Expr):
    with Tokenizer(exp_code) as tkzr:
        imp_expr: ImpExpr = ExpressionParser.parse_imp_expr(tkzr)
        assert imp_expr.left == exp_left
        assert imp_expr.right == exp_right
