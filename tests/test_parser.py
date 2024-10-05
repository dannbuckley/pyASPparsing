from contextlib import ExitStack
import typing
import pytest
from pyaspparsing import ParserError
from pyaspparsing.parser import *
from pyaspparsing.ast.ast_types import *


@pytest.mark.parametrize(
    "stmt_code,stmt_type",
    [
        ("Option Explicit\n", OptionExplicit()),
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
            "Private my_var\n",  # private field declaration
            FieldDecl(
                FieldName(FieldID(Token.identifier(8, 14))),
                access_mod=AccessModifierType.PRIVATE,
            ),
        ),
        (
            "Public my_var\n",  # public field declaration
            FieldDecl(
                FieldName(FieldID(Token.identifier(7, 13))),
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public my_var(1)\n",  # public field declaration with array rank list
            FieldDecl(
                FieldName(
                    FieldID(Token.identifier(7, 13)), [Token.int_literal(14, 15)]
                ),
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public my_var(1, 2)\n",  # public field declaration with array rank list
            FieldDecl(
                FieldName(
                    FieldID(Token.identifier(7, 13)),
                    [Token.int_literal(14, 15), Token.int_literal(17, 18)],
                ),
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public my_var, my_other_var\n",  # public field declaration with other var
            FieldDecl(
                FieldName(FieldID(Token.identifier(7, 13))),
                [VarName(ExtendedID(Token.identifier(15, 27)))],
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public my_var, my_other_var, yet_another\n",  # public field declaration with multiple other var
            FieldDecl(
                FieldName(FieldID(Token.identifier(7, 13))),
                [
                    VarName(ExtendedID(Token.identifier(15, 27))),
                    VarName(ExtendedID(Token.identifier(29, 40))),
                ],
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public my_var, my_other_var(1)\n",  # public field declaration with other var
            FieldDecl(
                FieldName(FieldID(Token.identifier(7, 13))),
                [
                    VarName(
                        ExtendedID(Token.identifier(15, 27)),
                        [Token.int_literal(28, 29)],
                    )
                ],
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Public my_var, my_other_var(1, 2)\n",  # public field declaration with other var
            FieldDecl(
                FieldName(FieldID(Token.identifier(7, 13))),
                [
                    VarName(
                        ExtendedID(Token.identifier(15, 27)),
                        [Token.int_literal(28, 29), Token.int_literal(31, 32)],
                    )
                ],
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Const a = 1\n",  # const declaration
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        IntLiteral(Token.int_literal(10, 11)),
                    )
                ]
            ),
        ),
        (
            "Const a = (1)\n",  # const declaration with paren ConstExprDef
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        IntLiteral(Token.int_literal(11, 12)),
                    )
                ]
            ),
        ),
        (
            "Const a = ((1))\n",  # const declaration with nested paren ConstExprDef
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        IntLiteral(Token.int_literal(12, 13)),
                    )
                ]
            ),
        ),
        (
            "Const a = -1\n",  # const declaration with sign ConstExprDef
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        UnaryExpr(
                            Token.symbol(10, 11), IntLiteral(Token.int_literal(11, 12))
                        ),
                    )
                ]
            ),
        ),
        (
            "Const a = +-1\n",  # const declaration with multiple sign ConstExprDef
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        UnaryExpr(
                            Token.symbol(10, 11),
                            UnaryExpr(
                                Token.symbol(11, 12),
                                IntLiteral(Token.int_literal(12, 13)),
                            ),
                        ),
                    )
                ]
            ),
        ),
        (
            "Const a = -(1)\n",  # const declaration with sign paren ConstExprDef
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        UnaryExpr(
                            Token.symbol(10, 11), IntLiteral(Token.int_literal(12, 13))
                        ),
                    )
                ]
            ),
        ),
        (
            "Const a = +(-(1))\n",  # const declaration with multiple sign nested paren ConstExprDef
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        UnaryExpr(
                            Token.symbol(10, 11),
                            UnaryExpr(
                                Token.symbol(12, 13),
                                IntLiteral(Token.int_literal(14, 15)),
                            ),
                        ),
                    )
                ]
            ),
        ),
        (
            "Const a = 1, b = 2\n",  # const declaration with multiple items
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(6, 7)),
                        IntLiteral(Token.int_literal(10, 11)),
                    ),
                    ConstListItem(
                        ExtendedID(Token.identifier(13, 14)),
                        IntLiteral(Token.int_literal(17, 18)),
                    ),
                ]
            ),
        ),
        (
            "Public Const a = 1\n",  # public const declaration
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(13, 14)),
                        IntLiteral(Token.int_literal(17, 18)),
                    )
                ],
                access_mod=AccessModifierType.PUBLIC,
            ),
        ),
        (
            "Private Const a = 1\n",  # private const declaration
            ConstDecl(
                [
                    ConstListItem(
                        ExtendedID(Token.identifier(14, 15)),
                        IntLiteral(Token.int_literal(18, 19)),
                    )
                ],
                access_mod=AccessModifierType.PRIVATE,
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
            "ReDim my_array(10)\n",
            RedimStmt(
                [
                    RedimDecl(
                        ExtendedID(Token.identifier(6, 14)),
                        [
                            IntLiteral(Token.int_literal(15, 17)),
                        ],
                    )
                ]
            ),
        ),
        (
            "ReDim my_array(10, 10)\n",
            RedimStmt(
                [
                    RedimDecl(
                        ExtendedID(Token.identifier(6, 14)),
                        [
                            IntLiteral(Token.int_literal(15, 17)),
                            IntLiteral(Token.int_literal(19, 21)),
                        ],
                    )
                ]
            ),
        ),
        (
            "ReDim Preserve my_array(10, 10)\n",
            RedimStmt(
                [
                    RedimDecl(
                        ExtendedID(Token.identifier(15, 23)),
                        [
                            IntLiteral(Token.int_literal(24, 26)),
                            IntLiteral(Token.int_literal(28, 30)),
                        ],
                    )
                ],
                preserve=True,
            ),
        ),
        (
            # if statement (BlockStmtList), empty block list
            "If 1 = 1 Then\nEnd If\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                )
            ),
        ),
        (
            # if statement (BlockStmtList), one block statement
            "If 1 = 1 Then\nDim my_var\nEnd If\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                [VarDecl([VarName(ExtendedID(Token.identifier(18, 24)))])],
            ),
        ),
        (
            # if statement (BlockStmtList), empty elseif (BlockStmtList)
            "If 1 = 2 Then\nElseIf 1 = 1 Then\nEnd If\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                else_stmt_list=[
                    ElseStmt(
                        [],
                        elif_expr=CompareExpr(
                            CompareExprType.COMPARE_EQ,
                            IntLiteral(Token.int_literal(21, 22)),
                            IntLiteral(Token.int_literal(25, 26)),
                        ),
                    )
                ],
            ),
        ),
        (
            # if statement (BlockStmtList), elseif with block statement
            "If 1 = 2 Then\nElseIf 1 = 1 Then\nDim my_var\nEnd If\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                else_stmt_list=[
                    ElseStmt(
                        [VarDecl([VarName(ExtendedID(Token.identifier(36, 42)))])],
                        elif_expr=CompareExpr(
                            CompareExprType.COMPARE_EQ,
                            IntLiteral(Token.int_literal(21, 22)),
                            IntLiteral(Token.int_literal(25, 26)),
                        ),
                    )
                ],
            ),
        ),
        (
            # if statement (BlockStmtList), elseif with inline statement
            'If 1 = 2 Then\nElseIf 1 = 1 Then Response.Write("Hello, world!")\nEnd If\n',
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                else_stmt_list=[
                    ElseStmt(
                        [
                            SubCallStmt(
                                LeftExpr(
                                    QualifiedID(
                                        [
                                            Token.identifier(32, 41, dot_end=True),
                                            Token.identifier(41, 46),
                                        ]
                                    ),
                                    [
                                        IndexOrParams(
                                            [ConstExpr(Token.string_literal(47, 62))]
                                        )
                                    ],
                                )
                            )
                        ],
                        elif_expr=CompareExpr(
                            CompareExprType.COMPARE_EQ,
                            IntLiteral(Token.int_literal(21, 22)),
                            IntLiteral(Token.int_literal(25, 26)),
                        ),
                    )
                ],
            ),
        ),
        (
            # if statement (BlockStmtList), empty else (BlockStmtList)
            "If 1 = 2 Then\nElse\nEnd If\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                else_stmt_list=[ElseStmt(is_else=True)],
            ),
        ),
        (
            # if statement (BlockStmtList), else with block statement
            "If 1 = 2 Then\nElse\nDim my_var\nEnd If\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                else_stmt_list=[
                    ElseStmt(
                        [VarDecl([VarName(ExtendedID(Token.identifier(23, 29)))])],
                        is_else=True,
                    )
                ],
            ),
        ),
        (
            # if statement (BlockStmtList), else with inline statement
            'If 1 = 2 Then\nElse Response.Write("Hello, world!")\nEnd If\n',
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                else_stmt_list=[
                    ElseStmt(
                        [
                            SubCallStmt(
                                LeftExpr(
                                    QualifiedID(
                                        [
                                            Token.identifier(19, 28, dot_end=True),
                                            Token.identifier(28, 33),
                                        ]
                                    ),
                                    [
                                        IndexOrParams(
                                            [ConstExpr(Token.string_literal(34, 49))]
                                        )
                                    ],
                                )
                            )
                        ],
                        is_else=True,
                    )
                ],
            ),
        ),
        (
            # if statement (InlineStmt), empty until newline
            "If 1 = 1 Then a = 1\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                [
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(14, 15)])),
                        IntLiteral(Token.int_literal(18, 19)),
                    )
                ],
            ),
        ),
        (
            # if statement (InlineStmt), else
            "If 1 = 2 Then a = 1 Else a = 2\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                [
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(14, 15)])),
                        IntLiteral(Token.int_literal(18, 19)),
                    )
                ],
                [
                    ElseStmt(
                        [
                            AssignStmt(
                                LeftExpr(QualifiedID([Token.identifier(25, 26)])),
                                IntLiteral(Token.int_literal(29, 30)),
                            )
                        ],
                        is_else=True,
                    )
                ],
            ),
        ),
        (
            # if statement (InlineStmt), end if
            "If 1 = 1 Then a = 1 End If\n",
            IfStmt(
                CompareExpr(
                    CompareExprType.COMPARE_EQ,
                    IntLiteral(Token.int_literal(3, 4)),
                    IntLiteral(Token.int_literal(7, 8)),
                ),
                [
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(14, 15)])),
                        IntLiteral(Token.int_literal(18, 19)),
                    )
                ],
            ),
        ),
        (
            # empty with statement
            "With my_var\nEnd With\n",
            WithStmt(LeftExpr(QualifiedID([Token.identifier(5, 11)]))),
        ),
        (
            # with statement, one assignment statement
            'With my_var\n.Name = "This is a name"\nEnd With\n',
            WithStmt(
                LeftExpr(QualifiedID([Token.identifier(5, 11)])),
                [
                    AssignStmt(
                        LeftExpr(
                            QualifiedID([Token.identifier(12, 17, dot_start=True)])
                        ),
                        ConstExpr(Token.string_literal(20, 36)),
                    )
                ],
            ),
        ),
        (
            # select statement, empty case list
            "Select Case a\nEnd Select\n",
            SelectStmt(LeftExpr(QualifiedID([Token.identifier(12, 13)]))),
        ),
        (
            # select statement, one empty case without newline
            "Select Case a\nCase 1 End Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [CaseStmt(case_expr_list=[IntLiteral(Token.int_literal(19, 20))])],
            ),
        ),
        (
            # select statement, one empty case with newline
            "Select Case a\nCase 1\nEnd Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [CaseStmt(case_expr_list=[IntLiteral(Token.int_literal(19, 20))])],
            ),
        ),
        (
            # select statement, one case without newline
            "Select Case a\nCase 1 Dim my_var\nEnd Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [
                    CaseStmt(
                        [VarDecl([VarName(ExtendedID(Token.identifier(25, 31)))])],
                        [IntLiteral(Token.int_literal(19, 20))],
                    )
                ],
            ),
        ),
        (
            # select statement, one case without newline
            "Select Case a\nCase 1\nDim my_var\nEnd Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [
                    CaseStmt(
                        [VarDecl([VarName(ExtendedID(Token.identifier(25, 31)))])],
                        [IntLiteral(Token.int_literal(19, 20))],
                    )
                ],
            ),
        ),
        (
            # select statement, empty case else without newline
            "Select Case a\nCase Else End Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [CaseStmt(is_else=True)],
            ),
        ),
        (
            # select statement, empty case else with newline
            "Select Case a\nCase Else\nEnd Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [CaseStmt(is_else=True)],
            ),
        ),
        (
            # select statement, one empty case and empty case else
            "Select Case a\nCase 1 Case Else End Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [
                    CaseStmt(case_expr_list=[IntLiteral(Token.int_literal(19, 20))]),
                    CaseStmt(is_else=True),
                ],
            ),
        ),
        (
            # select statement, case else without newline
            "Select Case a\nCase Else Dim my_var\nEnd Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [
                    CaseStmt(
                        [VarDecl([VarName(ExtendedID(Token.identifier(28, 34)))])],
                        is_else=True,
                    )
                ],
            ),
        ),
        (
            # select statement, case else with newline
            "Select Case a\nCase Else\nDim my_var\nEnd Select\n",
            SelectStmt(
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                [
                    CaseStmt(
                        [VarDecl([VarName(ExtendedID(Token.identifier(28, 34)))])],
                        is_else=True,
                    )
                ],
            ),
        ),
        (
            # empty while loop
            "While True\nWEnd\n",
            LoopStmt(
                loop_type=Token.identifier(0, 5),
                loop_expr=BoolLiteral(Token.identifier(6, 10)),
            ),
        ),
        (
            # while loop
            "While True\nSet a = a + 1\nWEnd\n",
            LoopStmt(
                [
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(15, 16)])),
                        AddExpr(
                            Token.symbol(21, 22),
                            LeftExpr(QualifiedID([Token.identifier(19, 20)])),
                            IntLiteral(Token.int_literal(23, 24)),
                        ),
                    )
                ],
                loop_type=Token.identifier(0, 5),
                loop_expr=BoolLiteral(Token.identifier(6, 10)),
            ),
        ),
        (
            # empty do loop
            "Do\nLoop\n",
            LoopStmt(),
        ),
        (
            # do loop
            "Do\nSet a = a + 1\nLoop\n",
            LoopStmt(
                [
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(7, 8)])),
                        AddExpr(
                            Token.symbol(13, 14),
                            LeftExpr(QualifiedID([Token.identifier(11, 12)])),
                            IntLiteral(Token.int_literal(15, 16)),
                        ),
                    )
                ]
            ),
        ),
        (
            # empty do while loop - beginning
            "Do While True\nLoop\n",
            LoopStmt(
                loop_type=Token.identifier(3, 8),
                loop_expr=BoolLiteral(Token.identifier(9, 13)),
            ),
        ),
        (
            # empty do until loop - beginning
            "Do Until True\nLoop\n",
            LoopStmt(
                loop_type=Token.identifier(3, 8),
                loop_expr=BoolLiteral(Token.identifier(9, 13)),
            ),
        ),
        (
            # empty do while loop - end
            "Do\nLoop While True\n",
            LoopStmt(
                loop_type=Token.identifier(8, 13),
                loop_expr=BoolLiteral(Token.identifier(14, 18)),
            ),
        ),
        (
            # empty do until loop - end
            "Do\nLoop Until True\n",
            LoopStmt(
                loop_type=Token.identifier(8, 13),
                loop_expr=BoolLiteral(Token.identifier(14, 18)),
            ),
        ),
        (
            # empty '=' 'To' type for loop without step
            "For target = 0 To 5\nNext\n",
            ForStmt(
                ExtendedID(Token.identifier(4, 10)),
                eq_expr=IntLiteral(Token.int_literal(13, 14)),
                to_expr=IntLiteral(Token.int_literal(18, 19)),
            ),
        ),
        (
            # empty '=' 'To' type for loop with step
            "For target = 0 To 5 Step 2\nNext\n",
            ForStmt(
                ExtendedID(Token.identifier(4, 10)),
                eq_expr=IntLiteral(Token.int_literal(13, 14)),
                to_expr=IntLiteral(Token.int_literal(18, 19)),
                step_expr=IntLiteral(Token.int_literal(25, 26)),
            ),
        ),
        (
            # empty 'Each' 'In' type for loop
            "For Each target In array\nNext\n",
            ForStmt(
                ExtendedID(Token.identifier(9, 15)),
                each_in_expr=LeftExpr(QualifiedID([Token.identifier(19, 24)])),
            ),
        ),
        (
            # '=' 'To' for loop
            "For target = 0 To 5\nSet a = target\nNext\n",
            ForStmt(
                ExtendedID(Token.identifier(4, 10)),
                [
                    AssignStmt(
                        LeftExpr(QualifiedID([Token.identifier(24, 25)])),
                        LeftExpr(QualifiedID([Token.identifier(28, 34)])),
                    )
                ],
                eq_expr=IntLiteral(Token.int_literal(13, 14)),
                to_expr=IntLiteral(Token.int_literal(18, 19)),
            ),
        ),
        (
            "a = 1\n",  # LeftExpr = Expr
            AssignStmt(
                LeftExpr(QualifiedID([Token.identifier(0, 1)])),
                IntLiteral(Token.int_literal(4, 5)),
            ),
        ),
        (
            "Set a = 1\n",  # Set LeftExpr = Expr
            AssignStmt(
                LeftExpr(QualifiedID([Token.identifier(4, 5)])),
                IntLiteral(Token.int_literal(8, 9)),
            ),
        ),
        (
            "Set a = New b\n",  # Set LeftExpr = New LeftExpr
            AssignStmt(
                LeftExpr(QualifiedID([Token.identifier(4, 5)])),
                LeftExpr(QualifiedID([Token.identifier(12, 13)])),
                is_new=True,
            ),
        ),
        (
            "Set a(1,, 3) = 42\n",  # LeftExpr with omitted expr in index or params list
            AssignStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(4, 5)]),
                    [
                        IndexOrParams(
                            [
                                IntLiteral(Token.int_literal(6, 7)),
                                None,
                                IntLiteral(Token.int_literal(10, 11)),
                            ]
                        )
                    ],
                ),
                IntLiteral(Token.int_literal(15, 17)),
            ),
        ),
        (
            "Set a().b(1,, 3) = 42\n",  # LeftExpr with omitted expr in tail index or params list
            AssignStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(4, 5)]),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(7, 9, dot_start=True)]),
                            [
                                IndexOrParams(
                                    [
                                        IntLiteral(Token.int_literal(10, 11)),
                                        None,
                                        IntLiteral(Token.int_literal(14, 15)),
                                    ]
                                )
                            ],
                        )
                    ],
                ),
                IntLiteral(Token.int_literal(19, 21)),
            ),
        ),
        (
            "Call Hello.World()\n",  # call QualifiedID with a QualifiedIDTail
            CallStmt(
                LeftExpr(
                    QualifiedID(
                        [
                            Token.identifier(5, 11, dot_end=True),
                            Token.identifier(11, 16),
                        ]
                    ),
                    [IndexOrParams()],
                )
            ),
        ),
        (
            "Call HelloWorld()\n",  # no params
            CallStmt(
                LeftExpr(QualifiedID([Token.identifier(5, 15)]), [IndexOrParams()])
            ),
        ),
        (
            "Call HelloWorld()()\n",  # multiple IndexOrParam in LeftExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams(), IndexOrParams()],
                )
            ),
        ),
        (
            "Call HelloWorld()(1)\n",  # param in later IndexOrParam for LeftExpr
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [
                        IndexOrParams(),
                        IndexOrParams([IntLiteral(Token.int_literal(18, 19))]),
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld().GoodMorning()\n",  # LeftExprTail
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(17, 29, dot_start=True)]),
                            [IndexOrParams()],
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld().GoodMorning()()\n",  # multiple IndexOrParam in LeftExprTail
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(17, 29, dot_start=True)]),
                            [IndexOrParams(), IndexOrParams()],
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld().GoodMorning(1)\n",  # param in LeftExprTail
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(17, 29, dot_start=True)]),
                            [IndexOrParams([IntLiteral(Token.int_literal(30, 31))])],
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld().GoodMorning(1, 2)\n",  # multiple params in LeftExprTail
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(17, 29, dot_start=True)]),
                            [
                                IndexOrParams(
                                    [
                                        IntLiteral(Token.int_literal(30, 31)),
                                        IntLiteral(Token.int_literal(33, 34)),
                                    ]
                                )
                            ],
                        )
                    ],
                )
            ),
        ),
        (
            "Call HelloWorld().GoodMorning()(1)\n",  # param in later IndexOrParam for LeftExprTail
            CallStmt(
                LeftExpr(
                    QualifiedID([Token.identifier(5, 15)]),
                    [IndexOrParams(dot=True)],
                    [
                        LeftExprTail(
                            QualifiedID([Token.identifier(17, 29, dot_start=True)]),
                            [
                                IndexOrParams(),
                                IndexOrParams([IntLiteral(Token.int_literal(32, 33))]),
                            ],
                        )
                    ],
                )
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
        ("Erase my_var\n", EraseStmt(ExtendedID(Token.identifier(6, 12)))),
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
        ("Set"),  # missing target expression
        ("Set a"),  # missing '='
        ("Set a ="),  # missing assignment expression
        ("Set a = New"),  # missing assignment expression
        ("Set a = b"),  # missing <NEWLINE>
        ("Set a = New b"),  # missing <NEWLINE>
        (
            'Call HelloWorld(("Missing paren"'
        ),  # missing ending ')' for value and for "index or params"
        ('Call HelloWorld("Missing paren"'),  # missing ending ')' for "index or params"
        ("Call Hello().World("),  # missing ending ')' for tail "index or params"
        ("Call"),  # missing left expression
        ("On"),  # missing Error { Resume Next | Goto IntLiteral } <NEWLINE>
        ("On Error"),  # missing { Resume Next | GoTo IntLiteral } <NEWLINE>
        ("On Error Resume"),  # missing 'Next' <NEWLINE>
        ("On Error Resume Next"),  # missing <NEWLINE>
        ("On Error GoTo"),  # missing IntLiteral <NEWLINE>
        ("On Error GoTo 0"),  # missing <NEWLINE>
        ("Exit"),  # missing exit type and <NEWLINE>
        ("Exit Do"),  # missing <NEWLINE>
        ("Exit Reality\n"),  # improper exit type
        ("Erase my_var"),  # missing <NEWLINE>
        ("Erase"),  # missing extended identifier
    ],
)
def test_invalid_global_stmt(stmt_code: str):
    with ExitStack() as stack:
        stack.enter_context(pytest.raises(ParserError))
        # parse code (don't suppress exception)
        prsr = stack.enter_context(Parser(stmt_code, False))
        prsr.parse()
