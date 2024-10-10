"""program module"""

import typing
import attrs
from ... import ParserError
from ..tokenizer.token_types import Token, TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import *
from .declarations import *
from .expressions import *
from .statements import *
from .parse_expressions import ExpressionParser


__all__ = [
    "Program",
]


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
            return VarDecl.from_tokenizer(tkzr)

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
                return ConstDecl.from_tokenizer(tkzr, access_mod)
            case "sub":
                return Parser.parse_sub_decl(tkzr, access_mod)
            case "function":
                return Parser.parse_function_decl(tkzr, access_mod)
            case "property":
                return Parser.parse_property_decl(tkzr, access_mod)

        # assume this is a field declaration
        assert access_mod is not None, "Expected access modifier in field declaration"
        return FieldDecl.from_tokenizer(tkzr, access_mod)

    @staticmethod
    def parse_class_decl(tkzr: Tokenizer) -> ClassDecl:
        """"""
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
    def parse_sub_decl(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ) -> SubDecl:
        """"""
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
    ) -> FunctionDecl:
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
    ) -> PropertyDecl:
        """"""
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
                    return ConstDecl.from_tokenizer(tkzr, access_mod)
                case "sub":
                    return Parser.parse_sub_decl(tkzr, access_mod)
                case "function":
                    return Parser.parse_function_decl(tkzr, access_mod)

            # assume this is a field declaration
            return FieldDecl.from_tokenizer(tkzr, access_mod)
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
                    return ConstDecl.from_tokenizer(tkzr)
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
    def parse_if_stmt(tkzr: Tokenizer) -> IfStmt:
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
    def parse_with_stmt(tkzr: Tokenizer) -> WithStmt:
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
    def parse_select_stmt(tkzr: Tokenizer) -> SelectStmt:
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
    def parse_loop_stmt(tkzr: Tokenizer) -> LoopStmt:
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
    def parse_for_stmt(tkzr: Tokenizer) -> ForStmt:
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
    def parse_inline_stmt(
        tkzr: Tokenizer,
        terminal_type: typing.Optional[TokenType] = None,
        terminal_code: typing.Optional[str] = None,
        terminal_casefold: bool = True,
        *,
        terminal_pairs: typing.List[typing.Tuple[TokenType, typing.Optional[str]]] = [],
    ) -> InlineStmt:
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
        return SubCallStmt.from_tokenizer(
            tkzr,
            left_expr,
            terminal_type,
            terminal_code,
            terminal_casefold,
            terminal_pairs=terminal_pairs,
        )

    @staticmethod
    def parse_block_stmt(tkzr: Tokenizer) -> BlockStmt:
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
                return VarDecl.from_tokenizer(tkzr)
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
            return ConstDecl.from_tokenizer(tkzr, access_mod)
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


@attrs.define
class Program:
    """The starting symbol for the VBScript grammar.
    Defined on grammar line 267

    Attributes
    ----------
    global_stmt_list : List[GlobalStmt], default=[]
    """

    global_stmt_list: typing.List[GlobalStmt] = attrs.field(default=attrs.Factory(list))

    @staticmethod
    def from_tokenizer(tkzr: Tokenizer):
        """
        Parameters
        ----------
        tkzr : Tokenizer
            Tokenizer that has entered into a runtime context

        Returns
        -------
        Program
        """
        # program may optionally start with a newline token
        if tkzr.try_token_type(TokenType.NEWLINE):
            tkzr.advance_pos()  # consume newline

        global_stmts: typing.List[GlobalStmt] = []
        # don't catch any errors here!
        # they should be caught by the Tokenizer runtime context
        while tkzr.current_token is not None:
            global_stmts.append(Parser.parse_global_stmt(tkzr))
        return Program(global_stmts)
