"""parser module"""

import typing
from ... import ParserError
from ..tokenizer.token_types import Token, TokenType
from ..tokenizer.state_machine import Tokenizer
from .base import *
from .declarations import *
from .expressions import *
from .statements import *
from .special import *
from .expression_parser import ExpressionParser


__all__ = ["Parser"]


class Parser:
    """"""

    @staticmethod
    def parse_processing_direc(tkzr: Tokenizer) -> ProcessingDirective:
        """Parse a starting processing directive ('<%@ %>')

        Returns
        -------
        ProcessingDirective
        """
        tkzr.assert_consume(TokenType.DELIM_START_PROCESSING)
        settings: typing.List[ProcessingSetting] = []
        while not tkzr.try_token_type(TokenType.DELIM_END):
            assert tkzr.try_token_type(
                TokenType.IDENTIFIER
            ) and tkzr.get_token_code() in [
                "language",
                "enablesessionstate",
                "codepage",
                "lcid",
                "transaction",
            ], "Invalid identifier in processing directive"
            config_kw = tkzr.current_token
            tkzr.advance_pos()  # consume keyword
            tkzr.assert_consume(TokenType.SYMBOL, "=")
            config_value = tkzr.current_token
            tkzr.advance_pos()
            settings.append(ProcessingSetting(config_kw, config_value))
            del config_kw, config_value
        tkzr.assert_consume(TokenType.DELIM_END)
        return ProcessingDirective(settings)

    @staticmethod
    def parse_output_text(tkzr: Tokenizer) -> OutputText:
        """Parse text that should be written directly to the response

        Returns
        -------
        OutputText
        """
        chunks: typing.List[Token] = []
        directives: typing.List[OutputDirective] = []
        stitch_order: typing.List[typing.Tuple[OutputType, int]] = []

        while tkzr.try_multiple_token_type(
            [TokenType.FILE_TEXT, TokenType.DELIM_START_OUTPUT]
        ):
            if tkzr.try_token_type(TokenType.FILE_TEXT):
                # reconstruction info for OutputText.stitch()
                stitch_order.append((OutputType.OUTPUT_RAW, len(chunks)))
                chunks.append(tkzr.current_token)
                tkzr.advance_pos()  # consume raw text block
            else:
                # <%= Expr %>
                start_direc: int = tkzr.current_token.token_src.start
                tkzr.advance_pos()  # consume delimiter
                output_expr = ExpressionParser.parse_expr(tkzr)
                assert tkzr.try_token_type(
                    TokenType.DELIM_END
                ), "Expected ending delimiter in output directive"
                end_direc: int = tkzr.current_token.token_src.stop
                tkzr.advance_pos()  # consume delimiter
                # reconstruction info for OutputText.stitch()
                stitch_order.append((OutputType.OUTPUT_DIRECTIVE, len(directives)))
                directives.append(
                    OutputDirective(slice(start_direc, end_direc), output_expr)
                )
        return OutputText(chunks, directives, stitch_order=stitch_order)

    @staticmethod
    def parse_html_comment(tkzr: Tokenizer) -> typing.Union[IncludeFile, OutputText]:
        """"""
        assert tkzr.try_token_type(TokenType.HTML_START_COMMENT)
        cmnt_start = tkzr.current_token
        tkzr.advance_pos()
        if tkzr.try_token_type(TokenType.INCLUDE_KW):
            tkzr.advance_pos()
            # get include type
            if tkzr.try_consume(TokenType.INCLUDE_TYPE, "file"):
                inc_type = IncludeType.INCLUDE_FILE
            elif tkzr.try_consume(TokenType.INCLUDE_TYPE, "virtual"):
                inc_type = IncludeType.INCLUDE_VIRTUAL
            else:
                raise ParserError(
                    "Expected either a 'file' or 'virtual' include type for the include directive"
                )
            tkzr.assert_consume(TokenType.SYMBOL, "=")  # consume '='
            # get include path
            assert tkzr.try_token_type(TokenType.INCLUDE_PATH)
            inc_path = tkzr.current_token
            tkzr.advance_pos()
            # should be at the end of the HTML comment
            tkzr.assert_consume(TokenType.HTML_END_COMMENT)
            return IncludeFile(inc_type, inc_path)
        # not an include statement, treat as a regular HTML comment
        # (i.e., reinterpret as FILE_TEXT and write directly to output)
        assert tkzr.try_token_type(TokenType.HTML_END_COMMENT)
        cmnt_end = tkzr.current_token
        tkzr.advance_pos()
        return OutputText(
            [Token.file_text(cmnt_start.token_src.start, cmnt_end.token_src.stop)],
            stitch_order=[(OutputType.OUTPUT_RAW, 0)],
        )

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
    def parse_block_stmt(tkzr: Tokenizer) -> BlockStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        if tkzr.try_token_type(TokenType.DELIM_END):
            tkzr.advance_pos()  # consume delimiter
            if tkzr.try_token_type(TokenType.DELIM_START_SCRIPT):
                tkzr.assert_consume(TokenType.DELIM_START_SCRIPT)
            else:
                nonscript_stmts: typing.List[BlockStmt] = []
                while tkzr.current_token is not None and not tkzr.try_token_type(
                    TokenType.DELIM_START_SCRIPT
                ):
                    if tkzr.try_token_type(TokenType.HTML_START_COMMENT):
                        cmnt = Parser.parse_html_comment(tkzr)
                        if (
                            len(nonscript_stmts) > 0
                            and isinstance(nonscript_stmts[-1], OutputText)
                            and isinstance(cmnt, OutputText)
                        ):
                            prev_out: OutputText = nonscript_stmts.pop()
                            nonscript_stmts.append(prev_out.merge(cmnt))
                            del prev_out
                        else:
                            nonscript_stmts.append(cmnt)
                        del cmnt
                    else:
                        out_text: OutputText = Parser.parse_output_text(tkzr)
                        if len(nonscript_stmts) > 0 and isinstance(
                            nonscript_stmts[-1], OutputText
                        ):
                            prev_out: OutputText = nonscript_stmts.pop()
                            nonscript_stmts.append(prev_out.merge(out_text))
                            del prev_out
                        else:
                            nonscript_stmts.append(out_text)
                        del out_text
                # nonscript statements occured in the middle of a statement
                # need to return to script mode
                tkzr.assert_consume(TokenType.DELIM_START_SCRIPT)
                if tkzr.try_token_type(TokenType.NEWLINE):
                    tkzr.advance_pos()
                if len(nonscript_stmts) == 1:
                    return nonscript_stmts.pop()
                if len(nonscript_stmts) > 1:
                    return NonscriptBlock(nonscript_stmts)
                # else, len(nonscript_stmts) == 0

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
        ret_inline = Parser.parse_inline_stmt(
            tkzr,
            terminal_pairs=[(TokenType.NEWLINE, None), (TokenType.DELIM_END, None)],
        )
        tkzr.assert_newline_or_script_end()
        return ret_inline

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
        tkzr.assert_newline_or_script_end()
        return ClassDecl(class_id, member_decl_list)

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
        if tkzr.try_multiple_token_type([TokenType.NEWLINE, TokenType.DELIM_END]):
            if tkzr.try_token_type(TokenType.NEWLINE):
                tkzr.advance_pos()  # consume newline
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() == "end"
            ):
                new_stmt = Parser.parse_method_stmt(tkzr)
                if isinstance(new_stmt, NonscriptBlock):
                    method_stmt_list.extend(new_stmt.nonscript_stmt_list)
                else:
                    method_stmt_list.append(new_stmt)
                del new_stmt
        else:
            method_stmt_list.append(
                Parser.parse_inline_stmt(tkzr, TokenType.IDENTIFIER, "end")
            )

        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "sub")
        tkzr.assert_newline_or_script_end()
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
        if tkzr.try_multiple_token_type([TokenType.NEWLINE, TokenType.DELIM_END]):
            if tkzr.try_token_type(TokenType.NEWLINE):
                tkzr.advance_pos()  # consume newline
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() == "end"
            ):
                new_stmt = Parser.parse_method_stmt(tkzr)
                if isinstance(new_stmt, NonscriptBlock):
                    method_stmt_list.extend(new_stmt.nonscript_stmt_list)
                else:
                    method_stmt_list.append(new_stmt)
                del new_stmt
        else:
            method_stmt_list.append(
                Parser.parse_inline_stmt(tkzr, TokenType.IDENTIFIER, "end")
            )

        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "function")
        tkzr.assert_newline_or_script_end()
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
        tkzr.assert_newline_or_script_end()

        method_stmt_list: typing.List[MethodStmt] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "end"
        ):
            new_stmt = Parser.parse_method_stmt(tkzr)
            if isinstance(new_stmt, NonscriptBlock):
                method_stmt_list.extend(new_stmt.nonscript_stmt_list)
            else:
                method_stmt_list.append(new_stmt)
            del new_stmt

        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "property")
        tkzr.assert_newline_or_script_end()
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
        if tkzr.try_multiple_token_type([TokenType.NEWLINE, TokenType.DELIM_END]):
            if tkzr.try_token_type(TokenType.NEWLINE):
                tkzr.advance_pos()  # consume newline
            # block statement list
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() in ["elseif", "else", "end"]
            ):
                new_block = Parser.parse_block_stmt(tkzr)
                if isinstance(new_block, NonscriptBlock):
                    block_stmt_list.extend(new_block.nonscript_stmt_list)
                else:
                    block_stmt_list.append(new_block)
                del new_block
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
                    if tkzr.try_multiple_token_type(
                        [TokenType.NEWLINE, TokenType.DELIM_END]
                    ):
                        if tkzr.try_token_type(TokenType.NEWLINE):
                            tkzr.advance_pos()  # consume newline
                        # block statement list
                        while not (
                            tkzr.try_token_type(TokenType.IDENTIFIER)
                            and tkzr.get_token_code() in ["elseif", "else", "end"]
                        ):
                            new_block = Parser.parse_block_stmt(tkzr)
                            if isinstance(new_block, NonscriptBlock):
                                elif_stmt_list.extend(new_block.nonscript_stmt_list)
                            else:
                                elif_stmt_list.append(new_block)
                            del new_block
                    else:
                        # inline statement
                        elif_stmt_list.append(
                            Parser.parse_inline_stmt(
                                tkzr,
                                terminal_pairs=[
                                    (TokenType.NEWLINE, None),
                                    (TokenType.DELIM_END, None),
                                ],
                            )
                        )
                        if tkzr.try_token_type(TokenType.NEWLINE):
                            tkzr.advance_pos()
                    else_stmt_list.append(ElseStmt(elif_stmt_list, elif_expr=elif_expr))
                    del elif_expr, elif_stmt_list
            # check for 'Else' statement
            if tkzr.try_consume(TokenType.IDENTIFIER, "else"):
                else_block_list: typing.List[BlockStmt] = []
                if tkzr.try_multiple_token_type(
                    [TokenType.NEWLINE, TokenType.DELIM_END]
                ):
                    if tkzr.try_token_type(TokenType.NEWLINE):
                        tkzr.advance_pos()  # consume newline
                    # block statement list
                    while not (
                        tkzr.try_token_type(TokenType.IDENTIFIER)
                        and tkzr.get_token_code() == "end"
                    ):
                        new_block = Parser.parse_block_stmt(tkzr)
                        if isinstance(new_block, NonscriptBlock):
                            else_block_list.extend(new_block.nonscript_stmt_list)
                        else:
                            else_block_list.append(new_block)
                        del new_block
                else:
                    # inline statement
                    else_block_list.append(
                        Parser.parse_inline_stmt(
                            tkzr,
                            terminal_pairs=[
                                (TokenType.NEWLINE, None),
                                (TokenType.DELIM_END, None),
                            ],
                        )
                    )
                    if tkzr.try_token_type(TokenType.NEWLINE):
                        tkzr.advance_pos()
                else_stmt_list.append(ElseStmt(else_block_list, is_else=True))
                del else_block_list
            # finish if statement
            tkzr.assert_consume(TokenType.IDENTIFIER, "end")
            tkzr.assert_consume(TokenType.IDENTIFIER, "if")
        else:
            # inline statement
            block_stmt_list.append(
                Parser.parse_inline_stmt(
                    tkzr,
                    terminal_pairs=[
                        (TokenType.IDENTIFIER, "else"),
                        (TokenType.IDENTIFIER, "end"),
                        (TokenType.NEWLINE, None),
                        (TokenType.DELIM_END, None),
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
                                    (TokenType.DELIM_END, None),
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
        tkzr.assert_newline_or_script_end()
        return IfStmt(if_expr, block_stmt_list, else_stmt_list)

    @staticmethod
    def parse_with_stmt(tkzr: Tokenizer) -> WithStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "with")
        with_expr = ExpressionParser.parse_expr(tkzr)
        tkzr.assert_newline_or_script_end()
        block_stmt_list: typing.List[BlockStmt] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER) and tkzr.get_token_code() == "end"
        ):
            new_block = Parser.parse_block_stmt(tkzr)
            if isinstance(new_block, NonscriptBlock):
                block_stmt_list.extend(new_block.nonscript_stmt_list)
            else:
                block_stmt_list.append(new_block)
            del new_block
        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "with")
        tkzr.assert_newline_or_script_end()
        return WithStmt(with_expr, block_stmt_list)

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
            tkzr.assert_newline_or_script_end()
            while not (
                tkzr.try_token_type(TokenType.IDENTIFIER)
                and tkzr.get_token_code() == "wend"
            ):
                new_block = Parser.parse_block_stmt(tkzr)
                if isinstance(new_block, NonscriptBlock):
                    block_stmt_list.extend(new_block.nonscript_stmt_list)
                else:
                    block_stmt_list.append(new_block)
                del new_block
            tkzr.assert_consume(TokenType.IDENTIFIER, "wend")
            tkzr.assert_newline_or_script_end()
            return LoopStmt(block_stmt_list, loop_type=loop_type, loop_expr=loop_expr)

        # must be 'Do' loop
        tkzr.assert_consume(TokenType.IDENTIFIER, "do")
        loop_type: typing.Optional[Token] = None
        loop_expr: typing.Optional[Expr] = None

        def _check_for_loop_type() -> bool:
            nonlocal tkzr, loop_type, loop_expr
            if not tkzr.try_multiple_token_type(
                [TokenType.NEWLINE, TokenType.DELIM_END]
            ):
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
        tkzr.assert_newline_or_script_end()

        # block statement list
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER)
            and tkzr.get_token_code() == "loop"
        ):
            new_block = Parser.parse_block_stmt(tkzr)
            if isinstance(new_block, NonscriptBlock):
                block_stmt_list.extend(new_block.nonscript_stmt_list)
            else:
                block_stmt_list.append(new_block)
            del new_block
        tkzr.assert_consume(TokenType.IDENTIFIER, "loop")

        # check if loop type is at the end
        if not found_loop_type:
            _check_for_loop_type()
        tkzr.assert_newline_or_script_end()
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
        tkzr.assert_newline_or_script_end()
        # parse block statement list
        block_stmt_list: typing.List[BlockStmt] = []
        while not (
            tkzr.try_token_type(TokenType.IDENTIFIER)
            and tkzr.get_token_code() == "next"
        ):
            new_block = Parser.parse_block_stmt(tkzr)
            if isinstance(new_block, NonscriptBlock):
                block_stmt_list.extend(new_block.nonscript_stmt_list)
            else:
                block_stmt_list.append(new_block)
            del new_block
        # finish for statement
        tkzr.assert_consume(TokenType.IDENTIFIER, "next")
        tkzr.assert_newline_or_script_end()
        return ForStmt(
            target_id,
            block_stmt_list,
            eq_expr=eq_expr,
            to_expr=to_expr,
            step_expr=step_expr,
            each_in_expr=each_in_expr,
        )

    @staticmethod
    def parse_select_stmt(tkzr: Tokenizer) -> SelectStmt:
        """"""
        tkzr.assert_consume(TokenType.IDENTIFIER, "select")
        tkzr.assert_consume(TokenType.IDENTIFIER, "case")
        select_case_expr = ExpressionParser.parse_expr(tkzr)
        tkzr.assert_newline_or_script_end()
        if tkzr.try_token_type(TokenType.DELIM_END):
            # not parsing statements yet, ignore nonscript text
            while not tkzr.try_token_type(TokenType.DELIM_START_SCRIPT):
                tkzr.advance_pos()
            tkzr.assert_consume(TokenType.DELIM_START_SCRIPT)
            if tkzr.try_token_type(TokenType.NEWLINE):
                tkzr.advance_pos()
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
                new_block = Parser.parse_block_stmt(tkzr)
                if isinstance(new_block, NonscriptBlock):
                    block_stmt_list.extend(new_block.nonscript_stmt_list)
                else:
                    block_stmt_list.append(new_block)
            case_stmt_list.append(
                CaseStmt(block_stmt_list, case_expr_list, is_else=is_else)
            )
            del is_else, case_expr_list, block_stmt_list
            if case_stmt_list[-1].is_else:
                # 'Case Else' must be the last case statement
                break
        tkzr.assert_consume(TokenType.IDENTIFIER, "end")
        tkzr.assert_consume(TokenType.IDENTIFIER, "select")
        tkzr.assert_newline_or_script_end()
        return SelectStmt(select_case_expr, case_stmt_list)
