import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.program import Program


@pytest.mark.parametrize(
    "stmt_code,stmt_type",
    [
        (
            # left_expr = <QualifiedID> <SubSafeExpr>
            'Response.Write "Hello, world!"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    )
                ),
                ConstExpr(Token.string_literal(15, 30)),
            ),
        ),
        (
            # left_expr = <QualifiedID> <SubSafeExpr> <CommaExprList>
            'Response.Write "Hello, world!", "Second string"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    )
                ),
                ConstExpr(Token.string_literal(15, 30)),
                [ConstExpr(Token.string_literal(32, 47))],
            ),
        ),
        (
            # left_expr = <QualifiedID> <CommaExprList>
            'Response.Write , "Second param"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    )
                ),
                comma_expr_list=[ConstExpr(Token.string_literal(17, 31))],
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' ')'
            "Response.Write()\n",  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    ),
                    [IndexOrParams()],
                )
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')'
            'Response.Write("Hello, world!")\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    ),
                    [IndexOrParams([ConstExpr(Token.string_literal(15, 30))])],
                )
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')' <CommaExprList>
            'Response.Write("Hello, world!"), "String at end"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    ),
                    [IndexOrParams([ConstExpr(Token.string_literal(15, 30))])],
                ),
                comma_expr_list=[ConstExpr(Token.string_literal(33, 48))],
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')' <CommaExprList>
            'Response.Write("Hello, world!"), "First",, "Last"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    ),
                    [IndexOrParams([ConstExpr(Token.string_literal(15, 30))])],
                ),
                comma_expr_list=[
                    ConstExpr(Token.string_literal(33, 40)),
                    None,
                    ConstExpr(Token.string_literal(43, 49)),
                ],
            ),
        ),
        (
            # left_expr = <QualifiedID> '(' <Expr> ')' <CommaExprList>
            'Response.Write("Hello, world!"), "String in middle", "String at end"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 9, dot_end=True), Token.identifier(9, 14)]
                    ),
                    [IndexOrParams([ConstExpr(Token.string_literal(15, 30))])],
                ),
                comma_expr_list=[
                    ConstExpr(Token.string_literal(33, 51)),
                    ConstExpr(Token.string_literal(53, 68)),
                ],
            ),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail>
            "Left.Expr().WithTail()\n",  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 5, dot_end=True), Token.identifier(5, 9)]
                    ),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(11, 20, dot_start=True)]),
                            [IndexOrParams()],
                        )
                    ],
                )
            ),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail> <SubSafeExpr>
            'Left.Expr().WithTail() "Hello, world!"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 5, dot_end=True), Token.identifier(5, 9)]
                    ),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(11, 20, dot_start=True)]),
                            [IndexOrParams()],
                        )
                    ],
                ),
                ConstExpr(Token.string_literal(23, 38)),
            ),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail> <SubSafeExpr> <CommaExprList>
            'Left.Expr().WithTail() "Hello, world", "Second param"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 5, dot_end=True), Token.identifier(5, 9)]
                    ),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(11, 20, dot_start=True)]),
                            [IndexOrParams()],
                        )
                    ],
                ),
                ConstExpr(Token.string_literal(23, 37)),
                [ConstExpr(Token.string_literal(39, 53))],
            ),
        ),
        (
            # left_expr = <QualifiedID> { <IndexOrParamsList> '.' | <IndexOrParamsListDot> }
            #       <LeftExprTail> <CommaExprList>
            'Left.Expr().WithTail() , "Second param"\n',  # subcall statement
            SubCallStmt(
                LeftExpr(
                    QualifiedID(
                        [Token.identifier(0, 5, dot_end=True), Token.identifier(5, 9)]
                    ),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(11, 20, dot_start=True)]),
                            [IndexOrParams()],
                        )
                    ],
                ),
                comma_expr_list=[ConstExpr(Token.string_literal(25, 39))],
            ),
        ),
    ],
)
def test_valid_global_stmt(stmt_code: str, stmt_type: GlobalStmt):
    # don't suppress exceptions
    with Tokenizer(stmt_code, False) as tkzr:
        prog = Program.from_tokenizer(tkzr)
        assert len(prog.global_stmt_list) == 1
        assert prog.global_stmt_list[0] == stmt_type
