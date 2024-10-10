"""Parser for classic ASP code"""

import sys
import traceback
import typing

import attrs

from ... import ParserError

from ..tokenizer.state_machine import Tokenizer
from ..tokenizer.token_types import TokenType, Token
from .base import *
from .declarations import *
from .expressions import *
from .statements import *
from .program import Program
from .parse_expressions import ExpressionParser


@attrs.define()
class Parser:
    """"""

    @staticmethod
    def parse_member_decl(tkzr: Tokenizer) -> MemberDecl:
        """
        Could be one of:
        - FieldDecl
        - VarDecl
        - ConstDecl
        - SubDecl
        - FunctionDecl
        - PropertyDecl
        """
        if tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "dim":
            return Parser.parse_var_decl(tkzr)

        # identify access modifier
        access_mod: typing.Optional[AccessModifierType] = None
        if tkzr.try_consume(TokenType.IDENTIFIER, "public"):
            if tkzr.try_consume(TokenType.IDENTIFIER, "default"):
                access_mod = AccessModifierType.PUBLIC_DEFAULT
            else:
                access_mod = AccessModifierType.PUBLIC
        elif tkzr.try_consume(TokenType.IDENTIFIER, "private"):
            access_mod = AccessModifierType.PRIVATE

        # must have identifier after access modifier
        assert tkzr.try_token_type(
            TokenType.IDENTIFIER
        ), "Member declaration must start with an identifier token"

        # check for other declaration types
        match tkzr.get_token_code():
            case "const":
                assert (
                    access_mod != AccessModifierType.PUBLIC_DEFAULT
                ), "'Public Default' access modifier cannot be used with const declaration"
                return Parser.parse_const_decl(tkzr, access_mod)
            case "sub":
                return Parser.parse_sub_decl(tkzr, access_mod)
            case "function":
                return Parser.parse_function_decl(tkzr, access_mod)
            case "property":
                return Parser.parse_property_decl(tkzr, access_mod)

        # assume this is a field declaration
        assert access_mod is not None, "Expected access modifier in field declaration"
        return Parser.parse_field_decl(tkzr, access_mod)

    @staticmethod
    def parse_class_decl(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "class")
        class_id = ExtendedID.from_tokenizer(tkzr)
        tkzr.assert_consume(TokenType.NEWLINE)

        # member declaration list could be empty
        member_decl_list: typing.List[MemberDecl] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "end"
        ):
            member_decl_list.append(Parser.parse_member_decl(tkzr))

        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "class")
        tkzr.assert_consume(TokenType.NEWLINE)
        return ClassDecl(class_id, member_decl_list)

    @staticmethod
    def parse_field_decl(tkzr: Tokenizer, access_mod: AccessModifierType) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        assert (
            access_mod != AccessModifierType.PUBLIC_DEFAULT
        ), "'Public Default' access modifier cannot be used with field declaration"

        # did not match token, parse as a field declaration
        if not tkzr.try_token_type(TokenType.IDENTIFIER):
            raise ParserError("Expected field name identifier in field declaration")
        field_id: FieldID = FieldID(tkzr.current_token)
        tkzr.advance_pos()  # consume identifier

        int_literals: typing.List[Token] = []
        if tkzr.try_consume(TokenType.SYMBOL, "("):
            find_int_literal = tkzr.try_multiple_token_type(
                [
                    TokenType.LITERAL_INT,
                    TokenType.LITERAL_HEX,
                    TokenType.LITERAL_OCT,
                ]
            )
            while find_int_literal:
                if not tkzr.try_multiple_token_type(
                    [
                        TokenType.LITERAL_INT,
                        TokenType.LITERAL_HEX,
                        TokenType.LITERAL_OCT,
                    ]
                ):
                    raise ParserError(
                        "Invalid token type found in array rank list "
                        "of field name declaration"
                    )
                int_literals.append(tkzr.current_token)
                tkzr.advance_pos()  # consume int literal

                tkzr.try_consume(TokenType.SYMBOL, ",")

                # last int literal is optional, check for ending ')'
                if (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and tkzr.get_token_code() == ")"
                ):
                    find_int_literal = False
            # should have an ending ')'
            tkzr.assert_consume(TokenType.SYMBOL, ")")
            del find_int_literal
        field_name: FieldName = FieldName(field_id, int_literals)
        del int_literals

        # prepare for other vars
        tkzr.try_consume(TokenType.SYMBOL, ",")

        other_vars: typing.List[VarName] = []
        parse_var_name = tkzr.try_token_type(TokenType.IDENTIFIER)
        while parse_var_name:
            var_id = ExtendedID.from_tokenizer(tkzr)
            if tkzr.try_consume(TokenType.SYMBOL, "("):
                find_int_literal = tkzr.try_multiple_token_type(
                    [
                        TokenType.LITERAL_INT,
                        TokenType.LITERAL_HEX,
                        TokenType.LITERAL_OCT,
                    ]
                )
                int_literals: typing.List[Token] = []
                while find_int_literal:
                    if not tkzr.try_multiple_token_type(
                        [
                            TokenType.LITERAL_INT,
                            TokenType.LITERAL_HEX,
                            TokenType.LITERAL_OCT,
                        ]
                    ):
                        raise ParserError(
                            "Invalid token type found in array rank list "
                            "of variable name declaration (part of field declaration)"
                        )
                    int_literals.append(tkzr.current_token)
                    tkzr.advance_pos()  # consume int literal

                    tkzr.try_consume(TokenType.SYMBOL, ",")

                    # last int literal is optional, check for ending ')'
                    if (
                        tkzr.try_token_type(TokenType.SYMBOL)
                        and tkzr.get_token_code() == ")"
                    ):
                        find_int_literal = False
                # should have and ending ')'
                tkzr.assert_consume(TokenType.SYMBOL, ")")
                other_vars.append(VarName(var_id, int_literals))
                del find_int_literal, int_literals
            else:
                other_vars.append(VarName(var_id))

            # another variable name?
            if not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ","
            ):
                parse_var_name = False
            else:
                tkzr.advance_pos()  # consume ','

        tkzr.assert_consume(TokenType.NEWLINE)
        return FieldDecl(field_name, other_vars, access_mod=access_mod)

    @staticmethod
    def parse_const_decl(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "const")
        const_list: typing.List[ConstListItem] = []
        while not tkzr.try_token_type(TokenType.NEWLINE):
            const_id = ExtendedID.from_tokenizer(tkzr)
            tkzr.assert_consume(TokenType.SYMBOL, "=")
            const_expr: typing.Optional[Expr] = None
            num_paren: int = 0
            # signs expand to the right, use a stack
            sign_stack: typing.List[Token] = []
            while not (
                tkzr.try_token_type(TokenType.NEWLINE)
                or (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and (tkzr.get_token_code() == ",")
                )
            ):
                if tkzr.try_consume(TokenType.SYMBOL, "("):
                    num_paren += 1
                elif (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and tkzr.get_token_code() in "-+"
                ):
                    sign_stack.append(tkzr.current_token)
                    tkzr.advance_pos()  # consume
                elif (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and tkzr.get_token_code() in ")"
                ):
                    assert (
                        const_expr is not None
                    ), "Expected const expression before ')' in const list item"
                    break
                else:
                    assert (
                        const_expr is None
                    ), "Can only have one const expression per const list item"
                    const_expr = ExpressionParser.parse_const_expr(tkzr)
            assert (
                const_expr is not None
            ), "Expected const expression in const list item"

            # verify correct number of closing parentheses
            while num_paren > 0:
                tkzr.assert_consume(TokenType.SYMBOL, ")")
                num_paren -= 1

            # combine signs into one expression
            while len(sign_stack) > 0:
                const_expr = UnaryExpr(sign_stack.pop(), const_expr)
            const_list.append(ConstListItem(const_id, const_expr))
            del const_id, const_expr, num_paren, sign_stack

            # advance to next item
            tkzr.try_consume(TokenType.SYMBOL, ",")
        tkzr.assert_consume(TokenType.NEWLINE)
        return ConstDecl(const_list, access_mod=access_mod)

    @staticmethod
    def parse_sub_decl(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "sub")
        sub_id = ExtendedID.from_tokenizer(tkzr)
        method_arg_list: typing.List[Arg] = []
        if tkzr.try_consume(TokenType.SYMBOL, "("):
            while not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ")"
            ):
                if tkzr.try_token_type(
                    TokenType.IDENTIFIER
                ) and tkzr.get_token_code() in ["byval", "byref"]:
                    arg_modifier = tkzr.current_token
                    tkzr.advance_pos()  # consume modifier
                else:
                    arg_modifier = None
                arg_id = ExtendedID.from_tokenizer(tkzr)
                has_paren = tkzr.try_consume(TokenType.SYMBOL, "(")
                if has_paren:
                    tkzr.assert_consume(TokenType.SYMBOL, ")")
                method_arg_list.append(
                    Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                )

                tkzr.try_consume(TokenType.SYMBOL, ",")
            tkzr.assert_consume(TokenType.SYMBOL, ")")

        method_stmt_list: typing.List[MethodStmt] = []
        if tkzr.try_token_type(TokenType.NEWLINE):
            tkzr.advance_pos()  # consume newline
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() == "end"
            ):
                method_stmt_list.append(Parser.parse_method_stmt(tkzr))
        else:
            method_stmt_list.append(
                Parser.parse_inline_stmt(tkzr, TokenType.IDENTIFIER, "end")
            )

        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "sub")
        tkzr.assert_consume(TokenType.NEWLINE)
        return SubDecl(sub_id, method_arg_list, method_stmt_list, access_mod=access_mod)

    @staticmethod
    def parse_function_decl(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "function")
        function_id = ExtendedID.from_tokenizer(tkzr)
        method_arg_list: typing.List[Arg] = []
        if tkzr.try_consume(TokenType.SYMBOL, "("):
            while not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ")"
            ):
                if tkzr.try_token_type(
                    TokenType.IDENTIFIER
                ) and tkzr.get_token_code() in ["byval", "byref"]:
                    arg_modifier = tkzr.current_token
                    tkzr.advance_pos()  # consume modifier
                else:
                    arg_modifier = None
                arg_id = ExtendedID.from_tokenizer(tkzr)
                has_paren = tkzr.try_consume(TokenType.SYMBOL, "(")
                if has_paren:
                    tkzr.assert_consume(TokenType.SYMBOL, ")")
                method_arg_list.append(
                    Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                )

                tkzr.try_consume(TokenType.SYMBOL, ",")
            tkzr.assert_consume(TokenType.SYMBOL, ")")

        method_stmt_list: typing.List[MethodStmt] = []
        if tkzr.try_token_type(TokenType.NEWLINE):
            tkzr.advance_pos()  # consume newline
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() == "end"
            ):
                method_stmt_list.append(Parser.parse_method_stmt(tkzr))
        else:
            method_stmt_list.append(
                Parser.parse_inline_stmt(tkzr, TokenType.IDENTIFIER, "end")
            )

        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "function")
        tkzr.assert_consume(TokenType.NEWLINE)
        return FunctionDecl(
            function_id, method_arg_list, method_stmt_list, access_mod=access_mod
        )

    @staticmethod
    def parse_property_decl(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ) -> MemberDecl:
        """

        Returns
        -------
        MemberDecl

        Raises
        ------
        ParserError
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "property")

        assert tkzr.try_token_type(TokenType.IDENTIFIER) and (
            tkzr.get_token_code() in ["get", "let", "set"]
        ), "Expected property access type after 'Property'"
        prop_access_type: Token = tkzr.current_token
        tkzr.advance_pos()  # consume access type

        property_id = ExtendedID.from_tokenizer(tkzr)

        method_arg_list: typing.List[Arg] = []
        if tkzr.try_consume(TokenType.SYMBOL, "("):
            while not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ")"
            ):
                if tkzr.try_token_type(
                    TokenType.IDENTIFIER
                ) and tkzr.get_token_code() in ["byval", "byref"]:
                    arg_modifier = tkzr.current_token
                    tkzr.advance_pos()  # consume modifier
                else:
                    arg_modifier = None
                arg_id = ExtendedID.from_tokenizer(tkzr)
                has_paren = tkzr.try_consume(TokenType.SYMBOL, "(")
                if has_paren:
                    tkzr.assert_consume(TokenType.SYMBOL, ")")
                method_arg_list.append(
                    Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                )
                tkzr.try_consume(TokenType.SYMBOL, ",")
            tkzr.assert_consume(TokenType.SYMBOL, ")")

        # property declaration requires newline after arg list
        tkzr.assert_consume(TokenType.NEWLINE)

        method_stmt_list: typing.List[MethodStmt] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "end"
        ):
            method_stmt_list.append(Parser.parse_method_stmt(tkzr))

        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "property")
        tkzr.assert_consume(TokenType.NEWLINE)
        return PropertyDecl(
            prop_access_type,
            property_id,
            method_arg_list,
            method_stmt_list,
            access_mod=access_mod,
        )

    @staticmethod
    def parse_access_modifier(tkzr: Tokenizer) -> GlobalStmt:
        """Parse global statement that starts with an access modifier

        Could be one of:
        - FieldDecl
        - ConstDecl
        - SubDecl
        - FunctionDecl

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        if tkzr.try_token_type(TokenType.IDENTIFIER):
            # identify access modifier
            if tkzr.try_consume(TokenType.IDENTIFIER, "public"):
                if tkzr.try_consume(TokenType.IDENTIFIER, "default"):
                    access_mod = AccessModifierType.PUBLIC_DEFAULT
                else:
                    access_mod = AccessModifierType.PUBLIC
            elif tkzr.try_consume(TokenType.IDENTIFIER, "private"):
                access_mod = AccessModifierType.PRIVATE

            # must have identifier after access modifier
            assert tkzr.try_token_type(
                TokenType.IDENTIFIER
            ), "Expected an identifier token after access modifier"

            # check for other declaration types
            match tkzr.get_token_code():
                case "const":
                    # cannot use 'Default' with const declaration
                    assert (
                        access_mod != AccessModifierType.PUBLIC_DEFAULT
                    ), "'Public Default' access modifier cannot be used with const declaration"
                    return Parser.parse_const_decl(tkzr, access_mod)
                case "sub":
                    return Parser.parse_sub_decl(tkzr, access_mod)
                case "function":
                    return Parser.parse_function_decl(tkzr, access_mod)

            # assume this is a field declaration
            return Parser.parse_field_decl(tkzr, access_mod)
        raise ParserError("Expected a 'Public' or 'Private' access modifier token")

    @staticmethod
    def parse_global_decl(tkzr: Tokenizer) -> GlobalStmt:
        """Parse a global declaration that lacks an access modifier

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        if tkzr.try_token_type(TokenType.IDENTIFIER):
            match tkzr.get_token_code():
                case "class":
                    return Parser.parse_class_decl(tkzr)
                case "const":
                    return Parser.parse_const_decl(tkzr)
                case "sub":
                    return Parser.parse_sub_decl(tkzr)
                case "function":
                    return Parser.parse_function_decl(tkzr)
                case _:
                    # shouldn't get here, but just in case
                    raise ParserError(
                        "Invalid identifier at start of global declaration"
                    )
        raise ParserError("Global declaration should start with an identifier")

    @staticmethod
    def parse_var_decl(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "dim")
        var_name: typing.List[VarName] = []
        parse_var_name = True
        while parse_var_name:
            var_id = ExtendedID.from_tokenizer(tkzr)
            if tkzr.try_consume(TokenType.SYMBOL, "("):
                # parse array rank list
                # first int literal is also optional
                find_int_literal = tkzr.try_multiple_token_type(
                    [
                        TokenType.LITERAL_INT,
                        TokenType.LITERAL_HEX,
                        TokenType.LITERAL_OCT,
                    ]
                )
                int_literals: typing.List[Token] = []
                while find_int_literal:
                    if not tkzr.try_multiple_token_type(
                        [
                            TokenType.LITERAL_INT,
                            TokenType.LITERAL_HEX,
                            TokenType.LITERAL_OCT,
                        ]
                    ):
                        raise ParserError(
                            "Invalid token type found in array rank list "
                            "of variable name declaration"
                        )
                    int_literals.append(tkzr.current_token)
                    tkzr.advance_pos()  # consume int literal

                    tkzr.try_consume(TokenType.SYMBOL, ",")

                    # last int literal is optional, check for ending ')'
                    if (
                        tkzr.try_token_type(TokenType.SYMBOL)
                        and tkzr.get_token_code() == ")"
                    ):
                        find_int_literal = False
                # should have an ending ')'
                tkzr.assert_consume(TokenType.SYMBOL, ")")
                var_name.append(VarName(var_id, int_literals))
                del find_int_literal, int_literals
            else:
                var_name.append(VarName(var_id))

            # another variable name?
            if not (
                tkzr.try_token_type(TokenType.SYMBOL) and tkzr.get_token_code() == ","
            ):
                parse_var_name = False
            else:
                tkzr.advance_pos()  # consume ','

        tkzr.assert_consume(TokenType.NEWLINE)
        return VarDecl(var_name)

    @staticmethod
    def parse_if_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "if")
        if_expr = ExpressionParser.parse_expr(tkzr)
        tkzr.assert_consume(TokenType.IDENTIFIER, "then")

        block_stmt_list: typing.List[BlockStmt] = []
        else_stmt_list: typing.List[ElseStmt] = []
        if tkzr.try_token_type(TokenType.NEWLINE):
            tkzr.advance_pos()  # consume newline
            # block statement list
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() in ["elseif", "else", "end"]
            ):
                block_stmt_list.append(Parser.parse_block_stmt(tkzr))
            # check for 'ElseIf' statements
            if (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() == "elseif"
            ):
                while not (
                    tkzr.try_token_type(TokenType.IDENTIFIER)
                    and tkzr.get_token_code() in ["else", "end"]
                ):
                    elif_stmt_list: typing.List[BlockStmt] = []
                    tkzr.assert_consume(TokenType.IDENTIFIER, "elseif")
                    elif_expr = ExpressionParser.parse_expr(tkzr)
                    tkzr.assert_consume(TokenType.IDENTIFIER, "then")
                    if tkzr.try_token_type(TokenType.NEWLINE):
                        tkzr.advance_pos()  # consume newline
                        # block statement list
                        while not (
                            tkzr.try_token_type(TokenType.IDENTIFIER)
                            and tkzr.get_token_code() in ["elseif", "else", "end"]
                        ):
                            elif_stmt_list.append(Parser.parse_block_stmt(tkzr))
                    else:
                        # inline statement
                        elif_stmt_list.append(
                            Parser.parse_inline_stmt(tkzr, TokenType.NEWLINE)
                        )
                        tkzr.assert_consume(TokenType.NEWLINE)
                    else_stmt_list.append(ElseStmt(elif_stmt_list, elif_expr=elif_expr))
                    del elif_expr, elif_stmt_list
            # check for 'Else' statement
            if tkzr.try_consume(TokenType.IDENTIFIER, "else"):
                else_block_list: typing.List[BlockStmt] = []
                if tkzr.try_token_type(TokenType.NEWLINE):
                    tkzr.advance_pos()  # consume newline
                    # block statement list
                    while not (
                        tkzr.try_token_type(TokenType.IDENTIFIER)
                        and tkzr.get_token_code() == "end"
                    ):
                        else_block_list.append(Parser.parse_block_stmt(tkzr))
                else:
                    # inline statement
                    else_block_list.append(
                        Parser.parse_inline_stmt(tkzr, TokenType.NEWLINE)
                    )
                    tkzr.assert_consume(TokenType.NEWLINE)
                else_stmt_list.append(ElseStmt(else_block_list, is_else=True))
                del else_block_list
            # finish if statement
            tkzr.assert_consume(TokenType.IDENTIFIER, "end")
            tkzr.assert_consume(TokenType.IDENTIFIER, "if")
            tkzr.assert_consume(TokenType.NEWLINE)
        else:
            # inline statement
            block_stmt_list.append(
                Parser.parse_inline_stmt(
                    tkzr,
                    terminal_pairs=[
                        (TokenType.IDENTIFIER, "else"),
                        (TokenType.IDENTIFIER, "end"),
                        (TokenType.NEWLINE, None),
                    ],
                )
            )
            # check for 'Else' statement
            if tkzr.try_consume(TokenType.IDENTIFIER, "else"):
                else_stmt_list.append(
                    ElseStmt(
                        [
                            Parser.parse_inline_stmt(
                                tkzr,
                                terminal_pairs=[
                                    (TokenType.IDENTIFIER, "end"),
                                    (TokenType.NEWLINE, None),
                                ],
                            )
                        ],
                        is_else=True,
                    )
                )
            # check for 'End' 'If'
            if tkzr.try_consume(TokenType.IDENTIFIER, "end"):
                tkzr.assert_consume(TokenType.IDENTIFIER, "if")
            # finish if statement
            tkzr.assert_consume(TokenType.NEWLINE)

        return IfStmt(if_expr, block_stmt_list, else_stmt_list)

    @staticmethod
    def parse_with_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "with")
        with_expr = ExpressionParser.parse_expr(tkzr)
        tkzr.assert_consume(TokenType.NEWLINE)
        block_stmt_list: typing.List[BlockStmt] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "end"
        ):
            block_stmt_list.append(Parser.parse_block_stmt(tkzr))
        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "with")
        tkzr.assert_consume(TokenType.NEWLINE)
        return WithStmt(with_expr, block_stmt_list)

    @staticmethod
    def parse_select_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "select")
        tkzr.assert_consume(TokenType.IDENTIFIER, "case")
        select_case_expr = ExpressionParser.parse_expr(tkzr)
        tkzr.assert_consume(TokenType.NEWLINE)
        case_stmt_list: typing.List[CaseStmt] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "end"
        ):
            tkzr.assert_consume(TokenType.IDENTIFIER, "case")
            is_else: bool = tkzr.try_consume(TokenType.IDENTIFIER, "else")
            case_expr_list: typing.List[Expr] = []
            if not is_else:
                # parse expression list
                parse_case_expr: bool = True
                while parse_case_expr:
                    case_expr_list.append(ExpressionParser.parse_expr(tkzr))
                    parse_case_expr = tkzr.try_consume(TokenType.SYMBOL, ",")
                del parse_case_expr
            # check for optional newline
            if tkzr.try_token_type(TokenType.NEWLINE):
                tkzr.advance_pos()  # consume newline
            # check for block statements
            block_stmt_list: typing.List[BlockStmt] = []
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() in ["case", "end"]
            ):
                block_stmt_list.append(Parser.parse_block_stmt(tkzr))
            case_stmt_list.append(
                CaseStmt(block_stmt_list, case_expr_list, is_else=is_else)
            )
            del is_else, case_expr_list, block_stmt_list
            if case_stmt_list[-1].is_else:
                # 'Case' 'Else' must be the last case statement
                break
        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "select")
        tkzr.assert_consume(TokenType.NEWLINE)
        return SelectStmt(select_case_expr, case_stmt_list)

    @staticmethod
    def parse_loop_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        assert tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() in [
            "do",
            "while",
        ], "Loop statement must start with 'Do' or 'While'"
        block_stmt_list: typing.List[BlockStmt] = []
        if tkzr.get_token_code() == "while":
            # loop type is 'While'
            loop_type: Token = tkzr.current_token
            tkzr.advance_pos()  # consume loop type
            loop_expr = ExpressionParser.parse_expr(tkzr)
            tkzr.assert_consume(TokenType.NEWLINE)
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() == "wend"
            ):
                block_stmt_list.append(Parser.parse_block_stmt(tkzr))
            tkzr.assert_consume(TokenType.IDENTIFIER, "wend")
            tkzr.assert_consume(TokenType.NEWLINE)
            return LoopStmt(block_stmt_list, loop_type=loop_type, loop_expr=loop_expr)

        # must be 'Do' loop
        tkzr.assert_consume(TokenType.IDENTIFIER, "do")
        loop_type: typing.Optional[Token] = None
        loop_expr: typing.Optional[Expr] = None

        def _check_for_loop_type() -> bool:
            nonlocal tkzr, loop_type, loop_expr
            if not tkzr.try_token_type(TokenType.NEWLINE):
                assert tkzr.try_token_type(
                    TokenType.IDENTIFIER
                ) and tkzr.get_token_code() in [
                    "while",
                    "until",
                ], "Loop type must be either 'While' or 'Until'"
                loop_type = tkzr.current_token
                tkzr.advance_pos()  # consume loop type
                loop_expr = ExpressionParser.parse_expr(tkzr)
                return True
            return False

        # check if loop type is at the beginning
        found_loop_type = _check_for_loop_type()
        tkzr.assert_consume(TokenType.NEWLINE)

        # block statement list
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER)
            and tkzr.get_token_code() == "loop"
        ):
            block_stmt_list.append(Parser.parse_block_stmt(tkzr))
        tkzr.assert_consume(TokenType.IDENTIFIER, "loop")

        # check if loop type is at the end
        if not found_loop_type:
            _check_for_loop_type()
        tkzr.assert_consume(TokenType.NEWLINE)

        return LoopStmt(block_stmt_list, loop_type=loop_type, loop_expr=loop_expr)

    @staticmethod
    def parse_for_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "for")

        # 'For' target_id '=' eq_expr 'To' to_expr [ 'Step' step_expr ]
        eq_expr: typing.Optional[Expr] = None
        to_expr: typing.Optional[Expr] = None
        step_expr: typing.Optional[Expr] = None
        # 'For' 'Each' target_id 'In' each_in_expr
        each_in_expr: typing.Optional[Expr] = None

        # check for loop type
        for_each: bool = tkzr.try_consume(TokenType.IDENTIFIER, "each")
        target_id = ExtendedID.from_tokenizer(tkzr)
        # parse expressions based on for loop type
        if for_each:
            tkzr.assert_consume(TokenType.IDENTIFIER, "in")
            each_in_expr = ExpressionParser.parse_expr(tkzr)
        else:
            tkzr.assert_consume(TokenType.SYMBOL, "=")
            eq_expr = ExpressionParser.parse_expr(tkzr)
            tkzr.assert_consume(TokenType.IDENTIFIER, "to")
            to_expr = ExpressionParser.parse_expr(tkzr)
            if tkzr.try_consume(TokenType.IDENTIFIER, "step"):
                step_expr = ExpressionParser.parse_expr(tkzr)
        tkzr.assert_consume(TokenType.NEWLINE)
        # parse block statement list
        block_stmt_list: typing.List[BlockStmt] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER)
            and tkzr.get_token_code() == "next"
        ):
            block_stmt_list.append(Parser.parse_block_stmt(tkzr))
        # finish for statement
        tkzr.assert_consume(TokenType.IDENTIFIER, "next")
        tkzr.assert_consume(TokenType.NEWLINE)
        return ForStmt(
            target_id,
            block_stmt_list,
            eq_expr=eq_expr,
            to_expr=to_expr,
            step_expr=step_expr,
            each_in_expr=each_in_expr,
        )

    @staticmethod
    def parse_subcall_stmt(
        tkzr: Tokenizer,
        left_expr: LeftExpr,
        terminal_type: typing.Optional[TokenType] = None,
        terminal_code: typing.Optional[str] = None,
        terminal_casefold: bool = True,
        *,
        terminal_pairs: typing.List[typing.Tuple[TokenType, typing.Optional[str]]] = [],
    ) -> GlobalStmt:
        """

        Parameters
        ----------
        left_expr : LeftExpr
        terminal_type : TokenType
        terminal_code : str | None, default=None,
        terminal_casefold : bool, default=True
        terminal_pairs : List[Tuple[TokenType, str | None]] = []
            If len(terminal_pairs) > 0, will compare against the contents of terminal_pairs
            instead of using terminal_type and terminal_code

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        assert (len(terminal_pairs) > 0) or (
            terminal_type is not None
        ), "Expected at least one terminal type or type/code pair"

        def _check_terminal() -> bool:
            """Check for the terminal token

            Returns
            -------
            bool
                True if the current token is the terminal token
            """
            nonlocal tkzr, terminal_type, terminal_code, terminal_casefold, terminal_pairs
            if len(terminal_pairs) > 0:
                return any(
                    map(
                        lambda tpair: tkzr.try_token_type(tpair[0])
                        and (
                            (tpair[1] is None)
                            or (tkzr.get_token_code(terminal_casefold) == tpair[1])
                        ),
                        terminal_pairs,
                    )
                )
            return tkzr.try_token_type(terminal_type) and (
                (terminal_code is None)
                or (tkzr.get_token_code(terminal_casefold) == terminal_code)
            )

        sub_safe_expr = None
        if len(left_expr.index_or_params) == 0 or len(left_expr.tail) >= 1:
            # left_expr = <QualifiedID>
            # or (
            #   left_expr = <QualifiedID> <IndexOrParamsList> '.' <LeftExprTail>
            #   or
            #   left_expr = <QualifiedID> <IndexOrParamsListDot> <LeftExprTail>
            # )
            # try to parse sub safe expression
            if not (
                _check_terminal()
                or (
                    tkzr.try_token_type(TokenType.SYMBOL)
                    and (tkzr.get_token_code() == ",")
                )
            ):
                sub_safe_expr = ExpressionParser.parse_expr(tkzr, True)
        else:
            # left_expr = <QualifiedID> <IndexOrParamsList>
            # make sure it matches:
            #   <QualifiedID> '(' [ <Expr> ] ')'
            assert (
                len(left_expr.index_or_params) == 1
                and 0 <= len(left_expr.index_or_params[0].expr_list) <= 1
                and left_expr.index_or_params[0].dot == False
                and len(left_expr.tail) == 0  # redundant check, but just in case
            ), "Expected left expression to have the form: <QualifiedID> '(' [ <Expr> ] ')'"

        # try to parse comma expression list
        comma_expr_list: typing.List[typing.Optional[Expr]] = []
        found_expr: bool = True  # fix: prevents erroneous None on first iteration
        while not _check_terminal():
            if tkzr.try_consume(TokenType.SYMBOL, ","):
                # was the previous entry not empty?
                if found_expr:
                    found_expr = False
                else:
                    comma_expr_list.append(None)
            else:
                # interpret as expression
                comma_expr_list.append(
                    ExpressionParser.parse_expr(tkzr)
                )  # don't need sub_safe here
                found_expr = True
        # DON'T CONSUME TERMINAL, LEAVE FOR CALLER
        del found_expr

        return SubCallStmt(left_expr, sub_safe_expr, comma_expr_list)

    @staticmethod
    def parse_inline_stmt(
        tkzr: Tokenizer,
        terminal_type: typing.Optional[TokenType] = None,
        terminal_code: typing.Optional[str] = None,
        terminal_casefold: bool = True,
        *,
        terminal_pairs: typing.List[typing.Tuple[TokenType, typing.Optional[str]]] = [],
    ) -> GlobalStmt:
        """If inline statement is a subcall statement, uses the given terminal token type
        to determine the where the statement ends

        Does not consume the terminal token

        Parameters
        ----------
        terminal_type : TokenType
        terminal_code : str | None, default=None
        terminal_casefold : bool, default=True

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        assert tkzr.try_multiple_token_type(
            [
                TokenType.IDENTIFIER,
                TokenType.IDENTIFIER_IDDOT,
                TokenType.IDENTIFIER_DOTID,
                TokenType.IDENTIFIER_DOTIDDOT,
            ]
        ), "Inline statement should start with an identifier or dotted identifier"
        # AssignStmt and SubCallStmt could start with a dotted identifier
        match tkzr.get_token_code():
            case "set":
                # 'Set' is optional for AssignStmt
                # need to also handle assignment without leading 'Set'
                return AssignStmt.from_tokenizer(tkzr)
            case "call":
                return CallStmt.from_tokenizer(tkzr)
            case "on":
                return ErrorStmt.from_tokenizer(tkzr)
            case "exit":
                return ExitStmt.from_tokenizer(tkzr)
            case "erase":
                return EraseStmt.from_tokenizer(tkzr)

        # no leading keyword, try parsing a left expression
        left_expr = ExpressionParser.parse_left_expr(tkzr)

        # assign statement?
        if tkzr.try_consume(TokenType.SYMBOL, "="):
            assign_expr = ExpressionParser.parse_expr(tkzr)
            return AssignStmt(left_expr, assign_expr)

        # must be a subcall statement
        return Parser.parse_subcall_stmt(
            tkzr,
            left_expr,
            terminal_type,
            terminal_code,
            terminal_casefold,
            terminal_pairs=terminal_pairs,
        )

    @staticmethod
    def parse_block_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        assert tkzr.try_multiple_token_type(
            [
                TokenType.IDENTIFIER,
                TokenType.IDENTIFIER_IDDOT,
                TokenType.IDENTIFIER_DOTID,
                TokenType.IDENTIFIER_DOTIDDOT,
            ]
        ), "Block statement should start with an identifier or dotted identifier"
        # AssignStmt and SubCallStmt could start with a dotted identifier
        match tkzr.get_token_code():
            case "dim":
                return Parser.parse_var_decl(tkzr)
            case "redim":
                return RedimStmt.from_tokenizer(tkzr)
            case "if":
                return Parser.parse_if_stmt(tkzr)
            case "with":
                return Parser.parse_with_stmt(tkzr)
            case "select":
                return Parser.parse_select_stmt(tkzr)
            case "do" | "while":
                return Parser.parse_loop_stmt(tkzr)
            case "for":
                return Parser.parse_for_stmt(tkzr)

        # try to parse as inline statement
        ret_inline = Parser.parse_inline_stmt(tkzr, TokenType.NEWLINE)
        tkzr.assert_consume(TokenType.NEWLINE)
        return ret_inline

    @staticmethod
    def parse_method_stmt(tkzr: Tokenizer) -> MethodStmt:
        """

        Returns
        -------
        MethodStmt
        """
        if tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() in [
            "const",
            "public",
            "private",
        ]:
            if tkzr.try_consume(TokenType.IDENTIFIER, "public"):
                access_mod = AccessModifierType.PUBLIC
            elif tkzr.try_consume(TokenType.IDENTIFIER, "private"):
                access_mod = AccessModifierType.PRIVATE
            else:
                access_mod = None
            return Parser.parse_const_decl(tkzr, access_mod)
        # assume block statement
        return Parser.parse_block_stmt(tkzr)

    @staticmethod
    def parse_global_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        assert tkzr.try_multiple_token_type(
            [
                TokenType.IDENTIFIER,
                TokenType.IDENTIFIER_IDDOT,
                TokenType.IDENTIFIER_DOTID,
                TokenType.IDENTIFIER_DOTIDDOT,
            ]
        ), "Global statement should start with an identifier or dotted identifier"
        # AssignStmt and SubCallStmt could start with a dotted identifier
        match tkzr.get_token_code():
            case "option":
                return OptionExplicit.from_tokenizer(tkzr)
            case "class" | "const" | "sub" | "function":
                # does not have an access modifier
                return Parser.parse_global_decl(tkzr)
            case "public" | "private":
                return Parser.parse_access_modifier(tkzr)
            case _:
                # try to parse as a block statement
                return Parser.parse_block_stmt(tkzr)

    @staticmethod
    def parse(tkzr: Tokenizer) -> Program:
        """

        Returns
        -------
        Program

        Raises
        ------
        RuntimeError
        """
        # program may optionally start with a newline token
        if tkzr.try_token_type(TokenType.NEWLINE):
            tkzr.advance_pos()  # consume newline

        global_stmts: typing.List[GlobalStmt] = []
        # don't catch any errors here!
        # if this method is run inside of a context, errors will be handled by __exit__()
        while tkzr.current_token is not None:
            global_stmts.append(Parser.parse_global_stmt(tkzr))
        return Program(global_stmts)
