import pytest
from pyaspparsing.ast.tokenizer.token_types import Token
from pyaspparsing.ast.tokenizer.state_machine import Tokenizer
from pyaspparsing.ast.ast_types import *
from pyaspparsing.ast.ast_types.program import Program


@pytest.mark.parametrize(
    "stmt_code,stmt_type",
    [
        ("Class MyClass\nEnd Class\n", ClassDecl(ExtendedID(Token.identifier(6, 13)))),
        (
            # class with private field declaration
            "Class MyClass\nPrivate my_var\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    FieldDecl(
                        FieldName(FieldID(Token.identifier(22, 28))),
                        access_mod=AccessModifierType.PRIVATE,
                    )
                ],
            ),
        ),
        (
            # class with public field declaration
            "Class MyClass\nPublic my_var\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    FieldDecl(
                        FieldName(FieldID(Token.identifier(21, 27))),
                        access_mod=AccessModifierType.PUBLIC,
                    )
                ],
            ),
        ),
        (
            # class with variable declaration
            "Class MyClass\nDim my_var\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [VarDecl([VarName(ExtendedID(Token.identifier(18, 24)))])],
            ),
        ),
        (
            # class with const declaration
            "Class MyClass\nConst a = 42\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    ConstDecl(
                        [
                            ConstListItem(
                                ExtendedID(Token.identifier(20, 21)),
                                IntLiteral(Token.int_literal(24, 26)),
                            )
                        ]
                    )
                ],
            ),
        ),
        (
            # class with public const declaration
            "Class MyClass\nPublic Const a = 42\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    ConstDecl(
                        [
                            ConstListItem(
                                ExtendedID(Token.identifier(27, 28)),
                                IntLiteral(Token.int_literal(31, 33)),
                            )
                        ],
                        access_mod=AccessModifierType.PUBLIC,
                    )
                ],
            ),
        ),
        (
            # class with private const declaration
            "Class MyClass\nPrivate Const a = 42\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    ConstDecl(
                        [
                            ConstListItem(
                                ExtendedID(Token.identifier(28, 29)),
                                IntLiteral(Token.int_literal(32, 34)),
                            )
                        ],
                        access_mod=AccessModifierType.PRIVATE,
                    )
                ],
            ),
        ),
        (
            # class with sub declaration
            "Class MyClass\nSub my_subroutine\nEnd Sub\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [SubDecl(ExtendedID(Token.identifier(18, 31)))],
            ),
        ),
        (
            # class with function declaration
            "Class MyClass\nFunction my_function\nEnd Function\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [FunctionDecl(ExtendedID(Token.identifier(23, 34)))],
            ),
        ),
        (
            # class with get property declaration
            "Class MyClass\nProperty Get my_property\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26), ExtendedID(Token.identifier(27, 38))
                    )
                ],
            ),
        ),
        (
            # class with let property declaration
            "Class MyClass\nProperty Let my_property\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26), ExtendedID(Token.identifier(27, 38))
                    )
                ],
            ),
        ),
        (
            # class with set property declaration
            "Class MyClass\nProperty Set my_property\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26), ExtendedID(Token.identifier(27, 38))
                    )
                ],
            ),
        ),
        (
            # class with property declaration, empty arg list
            "Class MyClass\nProperty Get my_property()\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26), ExtendedID(Token.identifier(27, 38))
                    )
                ],
            ),
        ),
        (
            # class with property declaration, single arg
            "Class MyClass\nProperty Get my_property(first)\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26),
                        ExtendedID(Token.identifier(27, 38)),
                        [Arg(ExtendedID(Token.identifier(39, 44)))],
                    )
                ],
            ),
        ),
        (
            # class with property declaration, single arg with paren
            "Class MyClass\nProperty Get my_property(first())\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26),
                        ExtendedID(Token.identifier(27, 38)),
                        [Arg(ExtendedID(Token.identifier(39, 44)), has_paren=True)],
                    )
                ],
            ),
        ),
        (
            # class with property declaration, byval arg
            "Class MyClass\nProperty Get my_property(ByVal first)\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26),
                        ExtendedID(Token.identifier(27, 38)),
                        [
                            Arg(
                                ExtendedID(Token.identifier(45, 50)),
                                arg_modifier=Token.identifier(39, 44),
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            # class with property declaration, byref arg
            "Class MyClass\nProperty Get my_property(ByRef first)\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26),
                        ExtendedID(Token.identifier(27, 38)),
                        [
                            Arg(
                                ExtendedID(Token.identifier(45, 50)),
                                arg_modifier=Token.identifier(39, 44),
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            # class with property declaration, multiple args
            "Class MyClass\nProperty Get my_property(first, second)\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26),
                        ExtendedID(Token.identifier(27, 38)),
                        [
                            Arg(ExtendedID(Token.identifier(39, 44))),
                            Arg(ExtendedID(Token.identifier(46, 52))),
                        ],
                    )
                ],
            ),
        ),
        (
            # class with property declaration, single method statement
            "Class MyClass\nProperty Get my_property\nDim c, d\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(23, 26),
                        ExtendedID(Token.identifier(27, 38)),
                        method_stmt_list=[
                            VarDecl(
                                [
                                    VarName(ExtendedID(Token.identifier(43, 44))),
                                    VarName(ExtendedID(Token.identifier(46, 47))),
                                ]
                            )
                        ],
                    )
                ],
            ),
        ),
        (
            # class with public property declaration
            "Class MyClass\nPublic Property Get my_property\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(30, 33),
                        ExtendedID(Token.identifier(34, 45)),
                        access_mod=AccessModifierType.PUBLIC,
                    )
                ],
            ),
        ),
        (
            # class with public default property declaration
            "Class MyClass\nPublic Default Property Get my_property\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(38, 41),
                        ExtendedID(Token.identifier(42, 53)),
                        access_mod=AccessModifierType.PUBLIC_DEFAULT,
                    )
                ],
            ),
        ),
        (
            # class with private property declaration
            "Class MyClass\nPrivate Property Get my_property\nEnd Property\nEnd Class\n",
            ClassDecl(
                ExtendedID(Token.identifier(6, 13)),
                [
                    PropertyDecl(
                        Token.identifier(31, 34),
                        ExtendedID(Token.identifier(35, 46)),
                        access_mod=AccessModifierType.PRIVATE,
                    )
                ],
            ),
        ),
        (
            "Sub my_subroutine\nEnd Sub\n",  # sub declaration
            SubDecl(ExtendedID(Token.identifier(4, 17))),
        ),
        (
            "Sub my_subroutine()\nEnd Sub\n",  # sub declaration with parentheses
            SubDecl(ExtendedID(Token.identifier(4, 17))),
        ),
        (
            "Sub my_subroutine(first)\nEnd Sub\n",  # sub declaration with arg
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                [Arg(ExtendedID(Token.identifier(18, 23)))],
            ),
        ),
        (
            "Sub my_subroutine(first())\nEnd Sub\n",  # sub declaration with paren arg
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                [Arg(ExtendedID(Token.identifier(18, 23)), has_paren=True)],
            ),
        ),
        (
            "Sub my_subroutine(ByVal first)\nEnd Sub\n",  # sub declaration with byval arg
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                [
                    Arg(
                        ExtendedID(Token.identifier(24, 29)),
                        arg_modifier=Token.identifier(18, 23),
                    )
                ],
            ),
        ),
        (
            "Sub my_subroutine(ByRef first)\nEnd Sub\n",  # sub declaration with byref arg
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                [
                    Arg(
                        ExtendedID(Token.identifier(24, 29)),
                        arg_modifier=Token.identifier(18, 23),
                    )
                ],
            ),
        ),
        (
            "Sub my_subroutine(first, second)\nEnd Sub\n",  # sub declaration with multiple args
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                [
                    Arg(ExtendedID(Token.identifier(18, 23))),
                    Arg(ExtendedID(Token.identifier(25, 31))),
                ],
            ),
        ),
        (
            "Private Sub my_subroutine\nEnd Sub\n",  # private sub
            SubDecl(
                ExtendedID(Token.identifier(12, 25)),
                access_mod=AccessModifierType.PRIVATE,
            ),
        ),
        (
            "Public Sub my_subroutine\nEnd Sub\n",  # public sub
            SubDecl(
                ExtendedID(Token.identifier(11, 24)),
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public Default Sub my_subroutine\nEnd Sub\n",  # public default sub
            SubDecl(
                ExtendedID(Token.identifier(19, 32)),
                access_mod=AccessModifierType.PUBLIC_DEFAULT,
            ),
        ),
        (
            "Sub my_subroutine Set a = 1 End Sub\n",  # sub with inline statement
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                method_stmt_list=[
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(22, 23)])),
                        IntLiteral(Token.int_literal(26, 27)),
                    )
                ],
            ),
        ),
        (
            "Sub my_subroutine\nDim c, d\nEnd Sub\n",  # sub with statement list
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                method_stmt_list=[
                    VarDecl(
                        [
                            VarName(ExtendedID(Token.identifier(22, 23))),
                            VarName(ExtendedID(Token.identifier(25, 26))),
                        ]
                    )
                ],
            ),
        ),
        (
            # const declaration as method statement
            "Sub my_subroutine\nConst a = 42\nEnd Sub\n",
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                method_stmt_list=[
                    ConstDecl(
                        [
                            ConstListItem(
                                ExtendedID(Token.identifier(24, 25)),
                                IntLiteral(Token.int_literal(28, 30)),
                            )
                        ]
                    )
                ],
            ),
        ),
        (
            # public const declaration as method statement
            "Sub my_subroutine\nPublic Const a = 42\nEnd Sub\n",
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                method_stmt_list=[
                    ConstDecl(
                        [
                            ConstListItem(
                                ExtendedID(Token.identifier(31, 32)),
                                IntLiteral(Token.int_literal(35, 37)),
                            )
                        ],
                        access_mod=AccessModifierType.PUBLIC,
                    )
                ],
            ),
        ),
        (
            # private const declaration as method statement
            "Sub my_subroutine\nPrivate Const a = 42\nEnd Sub\n",
            SubDecl(
                ExtendedID(Token.identifier(4, 17)),
                method_stmt_list=[
                    ConstDecl(
                        [
                            ConstListItem(
                                ExtendedID(Token.identifier(32, 33)),
                                IntLiteral(Token.int_literal(36, 38)),
                            )
                        ],
                        access_mod=AccessModifierType.PRIVATE,
                    )
                ],
            ),
        ),
        (
            "Function my_function\nEnd Function\n",  # function declaration
            FunctionDecl(ExtendedID(Token.identifier(9, 20))),
        ),
        (
            "Function my_function()\nEnd Function\n",  # function declaration with parentheses
            FunctionDecl(ExtendedID(Token.identifier(9, 20))),
        ),
        (
            "Function my_function(first)\nEnd Function\n",  # function declaration with arg
            FunctionDecl(
                ExtendedID(Token.identifier(9, 20)),
                [Arg(ExtendedID(Token.identifier(21, 26)))],
            ),
        ),
        (
            "Function my_function(first())\nEnd Function\n",  # function declaration with paren arg
            FunctionDecl(
                ExtendedID(Token.identifier(9, 20)),
                [Arg(ExtendedID(Token.identifier(21, 26)), has_paren=True)],
            ),
        ),
        (
            "Function my_function(ByVal first)\nEnd Function\n",  # function declaration with byval arg
            FunctionDecl(
                ExtendedID(Token.identifier(9, 20)),
                [
                    Arg(
                        ExtendedID(Token.identifier(27, 32)),
                        arg_modifier=Token.identifier(21, 26),
                    )
                ],
            ),
        ),
        (
            "Function my_function(ByRef first)\nEnd Function\n",  # function declaration with byref arg
            FunctionDecl(
                ExtendedID(Token.identifier(9, 20)),
                [
                    Arg(
                        ExtendedID(Token.identifier(27, 32)),
                        arg_modifier=Token.identifier(21, 26),
                    )
                ],
            ),
        ),
        (
            "Function my_function(first, second)\nEnd Function\n",  # function declaration with multiple args
            FunctionDecl(
                ExtendedID(Token.identifier(9, 20)),
                [
                    Arg(ExtendedID(Token.identifier(21, 26))),
                    Arg(ExtendedID(Token.identifier(28, 34))),
                ],
            ),
        ),
        (
            "Private Function my_function\nEnd Function\n",  # private function
            FunctionDecl(
                ExtendedID(Token.identifier(17, 28)),
                access_mod=AccessModifierType.PRIVATE,
            ),
        ),
        (
            "Public Function my_function\nEnd Function\n",  # public function
            FunctionDecl(
                ExtendedID(Token.identifier(16, 27)),
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public Default Function my_function\nEnd Function\n",  # public default function
            FunctionDecl(
                ExtendedID(Token.identifier(24, 35)),
                access_mod=AccessModifierType.PUBLIC_DEFAULT,
            ),
        ),
        (
            "Function my_function Set a = 1 End Function\n",  # function with inline statement
            FunctionDecl(
                ExtendedID(Token.identifier(9, 20)),
                method_stmt_list=[
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(25, 26)])),
                        IntLiteral(Token.int_literal(29, 30)),
                    )
                ],
            ),
        ),
        (
            "Function my_function\nDim a, b\nEnd Function\n",  # function with statement list
            FunctionDecl(
                ExtendedID(Token.identifier(9, 20)),
                method_stmt_list=[
                    VarDecl(
                        [
                            VarName(ExtendedID(Token.identifier(25, 26))),
                            VarName(ExtendedID(Token.identifier(28, 29))),
                        ]
                    )
                ],
            ),
        ),
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
