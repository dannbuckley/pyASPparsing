"""Parser for classic ASP code"""

import sys
import traceback
import typing

import attrs

from .. import ParserError

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
    def parse_extended_id(tkzr: Tokenizer) -> ExtendedID:
        """

        Returns
        -------
        ExtendedID

        Raises
        ------
        ParserError
        """
        if (safe_kw := tkzr.try_safe_keyword_id()) is not None:
            tkzr.advance_pos()  # consume safe keyword
            return ExtendedID(safe_kw)
        if tkzr.try_token_type(TokenType.IDENTIFIER):
            id_token = tkzr.current_token
            tkzr.advance_pos()  # consume identifier
            return ExtendedID(id_token)
        raise ParserError(
            "Expected an identifier token for the extended identifier symbol"
        )

    @staticmethod
    def parse_option_explicit(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        tkzr.assert_consume(TokenType.IDENTIFIER, "option")
        tkzr.assert_consume(TokenType.IDENTIFIER, "explicit")
        tkzr.assert_consume(TokenType.NEWLINE)
        return OptionExplicit()

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
            return self._parse_var_decl()

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
                return self._parse_const_decl(access_mod)
            case "sub":
                return self._parse_sub_decl(access_mod)
            case "function":
                return self._parse_function_decl(access_mod)
            case "property":
                return self._parse_property_decl(access_mod)

        # assume this is a field declaration
        assert access_mod is not None, "Expected access modifier in field declaration"
        return self._parse_field_decl(access_mod)

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
        try:
            self._assert_consume(TokenType.IDENTIFIER, "class")
            class_id = self._parse_extended_id()
            self._assert_consume(TokenType.NEWLINE)

            # member declaration list could be empty
            member_decl_list: typing.List[MemberDecl] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                member_decl_list.append(self._parse_member_decl())

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "class")
            self._assert_consume(TokenType.NEWLINE)
            return ClassDecl(class_id, member_decl_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_class_decl()") from ex

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
        try:
            # if access_mod == AccessModifierType.PUBLIC_DEFAULT:
            # raise ParserError(
            #     "'Public Default' access modifier cannot be used with field declaration"
            # )
            assert (
                access_mod != AccessModifierType.PUBLIC_DEFAULT
            ), "'Public Default' access modifier cannot be used with field declaration"

            # did not match token, parse as a field declaration
            if not self._try_token_type(TokenType.IDENTIFIER):
                raise ParserError("Expected field name identifier in field declaration")
            field_id: FieldID = FieldID(self._pos_tok)
            self._advance_pos()  # consume identifier

            int_literals: typing.List[Token] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                find_int_literal = (
                    self._try_token_type(TokenType.LITERAL_INT)
                    or self._try_token_type(TokenType.LITERAL_HEX)
                    or self._try_token_type(TokenType.LITERAL_OCT)
                )
                while find_int_literal:
                    if not (
                        self._try_token_type(TokenType.LITERAL_INT)
                        or self._try_token_type(TokenType.LITERAL_HEX)
                        or self._try_token_type(TokenType.LITERAL_OCT)
                    ):
                        raise ParserError(
                            "Invalid token type found in array rank list "
                            "of field name declaration"
                        )
                    int_literals.append(self._pos_tok)
                    self._advance_pos()  # consume int literal

                    self._try_consume(TokenType.SYMBOL, ",")

                    # last int literal is optional, check for ending ')'
                    if (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() == ")"
                    ):
                        find_int_literal = False
                # should have an ending ')'
                self._assert_consume(TokenType.SYMBOL, ")")
                del find_int_literal
            field_name: FieldName = FieldName(field_id, int_literals)
            del int_literals

            # prepare for other vars
            self._try_consume(TokenType.SYMBOL, ",")

            other_vars: typing.List[VarName] = []
            parse_var_name = self._try_token_type(TokenType.IDENTIFIER)
            while parse_var_name:
                var_id = self._parse_extended_id()
                if self._try_consume(TokenType.SYMBOL, "("):
                    find_int_literal = (
                        self._try_token_type(TokenType.LITERAL_INT)
                        or self._try_token_type(TokenType.LITERAL_HEX)
                        or self._try_token_type(TokenType.LITERAL_OCT)
                    )
                    int_literals: typing.List[Token] = []
                    while find_int_literal:
                        if not (
                            self._try_token_type(TokenType.LITERAL_INT)
                            or self._try_token_type(TokenType.LITERAL_HEX)
                            or self._try_token_type(TokenType.LITERAL_OCT)
                        ):
                            raise ParserError(
                                "Invalid token type found in array rank list "
                                "of variable name declaration (part of field declaration)"
                            )
                        int_literals.append(self._pos_tok)
                        self._advance_pos()  # consume int literal

                        self._try_consume(TokenType.SYMBOL, ",")

                        # last int literal is optional, check for ending ')'
                        if (
                            self._try_token_type(TokenType.SYMBOL)
                            and self._get_token_code() == ")"
                        ):
                            find_int_literal = False
                    # should have and ending ')'
                    self._assert_consume(TokenType.SYMBOL, ")")
                    other_vars.append(VarName(var_id, int_literals))
                    del find_int_literal, int_literals
                else:
                    other_vars.append(VarName(var_id))

                # another variable name?
                if (
                    not self._try_token_type(TokenType.SYMBOL)
                    or self._get_token_code() != ","
                ):
                    parse_var_name = False
                else:
                    self._advance_pos()  # consume ','

            self._assert_consume(TokenType.NEWLINE)
            return FieldDecl(field_name, other_vars, access_mod=access_mod)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_field_decl()") from ex

    @staticmethod
    def parse_const_decl(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "const")
            const_list: typing.List[ConstListItem] = []
            while not self._try_token_type(TokenType.NEWLINE):
                const_id = self._parse_extended_id()
                self._assert_consume(TokenType.SYMBOL, "=")
                const_expr: typing.Optional[Expr] = None
                num_paren: int = 0
                # signs expand to the right, use a stack
                sign_stack: typing.List[Token] = []
                while not (
                    self._try_token_type(TokenType.NEWLINE)
                    or (
                        self._try_token_type(TokenType.SYMBOL)
                        and (self._get_token_code() == ",")
                    )
                ):
                    if self._try_consume(TokenType.SYMBOL, "("):
                        num_paren += 1
                    elif (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() in "-+"
                    ):
                        sign_stack.append(self._pos_tok)
                        self._advance_pos()  # consume
                    elif (
                        self._try_token_type(TokenType.SYMBOL)
                        and self._get_token_code() in ")"
                    ):
                        assert (
                            const_expr is not None
                        ), "Expected const expression before ')' in const list item"
                        break
                    else:
                        assert (
                            const_expr is None
                        ), "Can only have one const expression per const list item"
                        const_expr = self._parse_const_expr()
                assert (
                    const_expr is not None
                ), "Expected const expression in const list item"

                # verify correct number of closing parentheses
                while num_paren > 0:
                    self._assert_consume(TokenType.SYMBOL, ")")
                    num_paren -= 1

                # combine signs into one expression
                while len(sign_stack) > 0:
                    const_expr = UnaryExpr(sign_stack.pop(), const_expr)
                const_list.append(ConstListItem(const_id, const_expr))
                del const_id, const_expr, num_paren, sign_stack

                # advance to next item
                self._try_consume(TokenType.SYMBOL, ",")
            self._assert_consume(TokenType.NEWLINE)
            return ConstDecl(const_list, access_mod=access_mod)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_const_decl()") from ex

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
        try:
            self._assert_consume(TokenType.IDENTIFIER, "sub")
            sub_id: ExtendedID = self._parse_extended_id()
            method_arg_list: typing.List[Arg] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    if self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in ["byval", "byref"]:
                        arg_modifier = self._pos_tok
                        self._advance_pos()  # consume modifier
                    else:
                        arg_modifier = None
                    arg_id = self._parse_extended_id()
                    has_paren = self._try_consume(TokenType.SYMBOL, "(")
                    if has_paren:
                        self._assert_consume(TokenType.SYMBOL, ")")
                    method_arg_list.append(
                        Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                    )

                    self._try_consume(TokenType.SYMBOL, ",")
                self._assert_consume(TokenType.SYMBOL, ")")

            method_stmt_list: typing.List[MethodStmt] = []
            if self._try_token_type(TokenType.NEWLINE):
                self._advance_pos()  # consume newline
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "end"
                ):
                    method_stmt_list.append(self._parse_method_stmt())
            else:
                method_stmt_list.append(
                    self._parse_inline_stmt(TokenType.IDENTIFIER, "end")
                )

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "sub")
            self._assert_consume(TokenType.NEWLINE)
            return SubDecl(
                sub_id, method_arg_list, method_stmt_list, access_mod=access_mod
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_sub_decl()") from ex

    @staticmethod
    def parse_function_decl(
        tkzr: Tokenizer, access_mod: typing.Optional[AccessModifierType] = None
    ) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "function")
            function_id: ExtendedID = self._parse_extended_id()
            method_arg_list: typing.List[Arg] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    if self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in ["byval", "byref"]:
                        arg_modifier = self._pos_tok
                        self._advance_pos()  # consume modifier
                    else:
                        arg_modifier = None
                    arg_id = self._parse_extended_id()
                    has_paren = self._try_consume(TokenType.SYMBOL, "(")
                    if has_paren:
                        self._assert_consume(TokenType.SYMBOL, ")")
                    method_arg_list.append(
                        Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                    )

                    self._try_consume(TokenType.SYMBOL, ",")
                self._assert_consume(TokenType.SYMBOL, ")")

            method_stmt_list: typing.List[MethodStmt] = []
            if self._try_token_type(TokenType.NEWLINE):
                self._advance_pos()  # consume newline
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "end"
                ):
                    method_stmt_list.append(self._parse_method_stmt())
            else:
                method_stmt_list.append(
                    self._parse_inline_stmt(TokenType.IDENTIFIER, "end")
                )

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "function")
            self._assert_consume(TokenType.NEWLINE)
            return FunctionDecl(
                function_id, method_arg_list, method_stmt_list, access_mod=access_mod
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_function_decl()") from ex

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
        try:
            self._assert_consume(TokenType.IDENTIFIER, "property")

            assert self._try_token_type(TokenType.IDENTIFIER) and (
                self._get_token_code() in ["get", "let", "set"]
            ), "Expected property access type after 'Property'"
            prop_access_type: Token = self._pos_tok
            self._advance_pos()  # consume access type

            property_id: ExtendedID = self._parse_extended_id()

            method_arg_list: typing.List[Arg] = []
            if self._try_consume(TokenType.SYMBOL, "("):
                while not (
                    self._try_token_type(TokenType.SYMBOL)
                    and self._get_token_code() == ")"
                ):
                    if self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in ["byval", "byref"]:
                        arg_modifier = self._pos_tok
                        self._advance_pos()  # consume modifier
                    else:
                        arg_modifier = None
                    arg_id = self._parse_extended_id()
                    has_paren = self._try_consume(TokenType.SYMBOL, "(")
                    if has_paren:
                        self._assert_consume(TokenType.SYMBOL, ")")
                    method_arg_list.append(
                        Arg(arg_id, arg_modifier=arg_modifier, has_paren=has_paren)
                    )
                    self._try_consume(TokenType.SYMBOL, ",")
                self._assert_consume(TokenType.SYMBOL, ")")

            # property declaration requires newline after arg list
            self._assert_consume(TokenType.NEWLINE)

            method_stmt_list: typing.List[MethodStmt] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                method_stmt_list.append(self._parse_method_stmt())

            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "property")
            self._assert_consume(TokenType.NEWLINE)
            return PropertyDecl(
                prop_access_type,
                property_id,
                method_arg_list,
                method_stmt_list,
                access_mod=access_mod,
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_property_decl()") from ex

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
        if self._try_token_type(TokenType.IDENTIFIER):
            try:
                # identify access modifier
                if self._try_consume(TokenType.IDENTIFIER, "public"):
                    if self._try_consume(TokenType.IDENTIFIER, "default"):
                        access_mod = AccessModifierType.PUBLIC_DEFAULT
                    else:
                        access_mod = AccessModifierType.PUBLIC
                elif self._try_consume(TokenType.IDENTIFIER, "private"):
                    access_mod = AccessModifierType.PRIVATE

                # must have identifier after access modifier
                assert self._try_token_type(
                    TokenType.IDENTIFIER
                ), "Expected an identifier token after access modifier"

                # check for other declaration types
                match self._get_token_code():
                    case "const":
                        # cannot use 'Default' with const declaration
                        assert (
                            access_mod != AccessModifierType.PUBLIC_DEFAULT
                        ), "'Public Default' access modifier cannot be used with const declaration"
                        return self._parse_const_decl(access_mod)
                    case "sub":
                        return self._parse_sub_decl(access_mod)
                    case "function":
                        return self._parse_function_decl(access_mod)

                # assume this is a field declaration
                return self._parse_field_decl(access_mod)
            except AssertionError as ex:
                raise ParserError(
                    "An error occurred in _parse_access_modifier()"
                ) from ex
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
        if self._try_token_type(TokenType.IDENTIFIER):
            match self._get_token_code():
                case "class":
                    return self._parse_class_decl()
                case "const":
                    return self._parse_const_decl()
                case "sub":
                    return self._parse_sub_decl()
                case "function":
                    return self._parse_function_decl()
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
        try:
            self._assert_consume(TokenType.IDENTIFIER, "dim")
            var_name: typing.List[VarName] = []
            parse_var_name = True
            while parse_var_name:
                var_id = self._parse_extended_id()
                if self._try_consume(TokenType.SYMBOL, "("):
                    # parse array rank list
                    # first int literal is also optional
                    find_int_literal = (
                        self._try_token_type(TokenType.LITERAL_INT)
                        or self._try_token_type(TokenType.LITERAL_HEX)
                        or self._try_token_type(TokenType.LITERAL_OCT)
                    )
                    int_literals: typing.List[Token] = []
                    while find_int_literal:
                        if not (
                            self._try_token_type(TokenType.LITERAL_INT)
                            or self._try_token_type(TokenType.LITERAL_HEX)
                            or self._try_token_type(TokenType.LITERAL_OCT)
                        ):
                            raise ParserError(
                                "Invalid token type found in array rank list "
                                "of variable name declaration"
                            )
                        int_literals.append(self._pos_tok)
                        self._advance_pos()  # consume int literal

                        self._try_consume(TokenType.SYMBOL, ",")

                        # last int literal is optional, check for ending ')'
                        if (
                            self._try_token_type(TokenType.SYMBOL)
                            and self._get_token_code() == ")"
                        ):
                            find_int_literal = False
                    # should have an ending ')'
                    self._assert_consume(TokenType.SYMBOL, ")")
                    var_name.append(VarName(var_id, int_literals))
                    del find_int_literal, int_literals
                else:
                    var_name.append(VarName(var_id))

                # another variable name?
                if (
                    not self._try_token_type(TokenType.SYMBOL)
                    or self._get_token_code() != ","
                ):
                    parse_var_name = False
                else:
                    self._advance_pos()  # consume ','

            self._assert_consume(TokenType.NEWLINE)
            return VarDecl(var_name)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_var_decl()") from ex

    @staticmethod
    def parse_redim_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        return RedimStmt.from_tokenizer(tkzr)

    @staticmethod
    def parse_if_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "if")
            if_expr = self._parse_expr()
            self._assert_consume(TokenType.IDENTIFIER, "then")

            block_stmt_list: typing.List[BlockStmt] = []
            else_stmt_list: typing.List[ElseStmt] = []
            if self._try_token_type(TokenType.NEWLINE):
                self._advance_pos()  # consume newline
                # block statement list
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() in ["elseif", "else", "end"]
                ):
                    block_stmt_list.append(self._parse_block_stmt())
                # check for 'ElseIf' statements
                if (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "elseif"
                ):
                    while not (
                        self._try_token_type(TokenType.IDENTIFIER)
                        and self._get_token_code() in ["else", "end"]
                    ):
                        elif_stmt_list: typing.List[BlockStmt] = []
                        self._assert_consume(TokenType.IDENTIFIER, "elseif")
                        elif_expr: Expr = self._parse_expr()
                        self._assert_consume(TokenType.IDENTIFIER, "then")
                        if self._try_token_type(TokenType.NEWLINE):
                            self._advance_pos()  # consume newline
                            # block statement list
                            while not (
                                self._try_token_type(TokenType.IDENTIFIER)
                                and self._get_token_code() in ["elseif", "else", "end"]
                            ):
                                elif_stmt_list.append(self._parse_block_stmt())
                        else:
                            # inline statement
                            elif_stmt_list.append(
                                self._parse_inline_stmt(TokenType.NEWLINE)
                            )
                            self._assert_consume(TokenType.NEWLINE)
                        else_stmt_list.append(
                            ElseStmt(elif_stmt_list, elif_expr=elif_expr)
                        )
                        del elif_expr, elif_stmt_list
                # check for 'Else' statement
                if self._try_consume(TokenType.IDENTIFIER, "else"):
                    else_block_list: typing.List[BlockStmt] = []
                    if self._try_token_type(TokenType.NEWLINE):
                        self._advance_pos()  # consume newline
                        # block statement list
                        while not (
                            self._try_token_type(TokenType.IDENTIFIER)
                            and self._get_token_code() == "end"
                        ):
                            else_block_list.append(self._parse_block_stmt())
                    else:
                        # inline statement
                        else_block_list.append(
                            self._parse_inline_stmt(TokenType.NEWLINE)
                        )
                        self._assert_consume(TokenType.NEWLINE)
                    else_stmt_list.append(ElseStmt(else_block_list, is_else=True))
                    del else_block_list
                # finish if statement
                self._assert_consume(TokenType.IDENTIFIER, "end")
                self._assert_consume(TokenType.IDENTIFIER, "if")
                self._assert_consume(TokenType.NEWLINE)
            else:
                # inline statement
                block_stmt_list.append(
                    self._parse_inline_stmt(
                        terminal_pairs=[
                            (
                                TokenType.IDENTIFIER,
                                "else",
                            ),  # optional 'Else' <InlineStmt>
                            (TokenType.IDENTIFIER, "end"),  # optional 'End' 'If'
                            (TokenType.NEWLINE),  # if statement terminator
                        ]
                    )
                )
                # check for 'Else' statement
                if self._try_consume(TokenType.IDENTIFIER, "else"):
                    else_stmt_list.append(
                        ElseStmt(
                            [
                                self._parse_inline_stmt(
                                    terminal_pairs=[
                                        (
                                            TokenType.IDENTIFIER,
                                            "end",
                                        ),  # optional 'End' 'If'
                                        (TokenType.NEWLINE),  # if statement terminator
                                    ]
                                )
                            ],
                            is_else=True,
                        )
                    )
                # check for 'End' 'If'
                if self._try_consume(TokenType.IDENTIFIER, "end"):
                    self._assert_consume(TokenType.IDENTIFIER, "if")
                # finish if statement
                self._assert_consume(TokenType.NEWLINE)

            return IfStmt(if_expr, block_stmt_list, else_stmt_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_if_stmt()") from ex

    @staticmethod
    def parse_with_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "with")
            with_expr = self._parse_expr()
            self._assert_consume(TokenType.NEWLINE)
            block_stmt_list: typing.List[BlockStmt] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                block_stmt_list.append(self._parse_block_stmt())
            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "with")
            self._assert_consume(TokenType.NEWLINE)
            return WithStmt(with_expr, block_stmt_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_with_stmt()") from ex

    @staticmethod
    def parse_select_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "select")
            self._assert_consume(TokenType.IDENTIFIER, "case")
            select_case_expr = self._parse_expr()
            self._assert_consume(TokenType.NEWLINE)
            case_stmt_list: typing.List[CaseStmt] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "end"
            ):
                self._assert_consume(TokenType.IDENTIFIER, "case")
                is_else: bool = self._try_consume(TokenType.IDENTIFIER, "else")
                case_expr_list: typing.List[Expr] = []
                if not is_else:
                    # parse expression list
                    parse_case_expr: bool = True
                    while parse_case_expr:
                        case_expr_list.append(self._parse_expr())
                        parse_case_expr = self._try_consume(TokenType.SYMBOL, ",")
                    del parse_case_expr
                # check for optional newline
                if self._try_token_type(TokenType.NEWLINE):
                    self._advance_pos()  # consume newline
                # check for block statements
                block_stmt_list: typing.List[BlockStmt] = []
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() in ["case", "end"]
                ):
                    block_stmt_list.append(self._parse_block_stmt())
                case_stmt_list.append(
                    CaseStmt(block_stmt_list, case_expr_list, is_else=is_else)
                )
                del is_else, case_expr_list, block_stmt_list
                if case_stmt_list[-1].is_else:
                    # 'Case' 'Else' must be the last case statement
                    break
            self._assert_consume(TokenType.IDENTIFIER, "end")
            self._assert_consume(TokenType.IDENTIFIER, "select")
            self._assert_consume(TokenType.NEWLINE)
            return SelectStmt(select_case_expr, case_stmt_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_select_stmt()") from ex

    @staticmethod
    def parse_loop_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        try:
            assert self._try_token_type(
                TokenType.IDENTIFIER
            ) and self._get_token_code() in [
                "do",
                "while",
            ], "Loop statement must start with 'Do' or 'While'"
            block_stmt_list: typing.List[BlockStmt] = []
            if self._get_token_code() == "while":
                # loop type is 'While'
                loop_type: Token = self._pos_tok
                self._advance_pos()  # consume loop type
                loop_expr: Expr = self._parse_expr()
                self._assert_consume(TokenType.NEWLINE)
                while not (
                    self._try_token_type(TokenType.IDENTIFIER)
                    and self._get_token_code() == "wend"
                ):
                    block_stmt_list.append(self._parse_block_stmt())
                self._assert_consume(TokenType.IDENTIFIER, "wend")
                self._assert_consume(TokenType.NEWLINE)
                return LoopStmt(
                    block_stmt_list, loop_type=loop_type, loop_expr=loop_expr
                )

            # must be 'Do' loop
            self._assert_consume(TokenType.IDENTIFIER, "do")
            loop_type: typing.Optional[Token] = None
            loop_expr: typing.Optional[Expr] = None

            def _check_for_loop_type() -> bool:
                nonlocal self, loop_type, loop_expr
                if not self._try_token_type(TokenType.NEWLINE):
                    assert self._try_token_type(
                        TokenType.IDENTIFIER
                    ) and self._get_token_code() in [
                        "while",
                        "until",
                    ], "Loop type must be either 'While' or 'Until'"
                    loop_type = self._pos_tok
                    self._advance_pos()  # consume loop type
                    loop_expr = self._parse_expr()
                    return True
                return False

            # check if loop type is at the beginning
            found_loop_type = _check_for_loop_type()
            self._assert_consume(TokenType.NEWLINE)

            # block statement list
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "loop"
            ):
                block_stmt_list.append(self._parse_block_stmt())
            self._assert_consume(TokenType.IDENTIFIER, "loop")

            # check if loop type is at the end
            if not found_loop_type:
                _check_for_loop_type()
            self._assert_consume(TokenType.NEWLINE)

            return LoopStmt(block_stmt_list, loop_type=loop_type, loop_expr=loop_expr)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_loop_stmt()") from ex

    @staticmethod
    def parse_for_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """"""
        try:
            self._assert_consume(TokenType.IDENTIFIER, "for")

            # 'For' target_id '=' eq_expr 'To' to_expr [ 'Step' step_expr ]
            eq_expr: typing.Optional[Expr] = None
            to_expr: typing.Optional[Expr] = None
            step_expr: typing.Optional[Expr] = None
            # 'For' 'Each' target_id 'In' each_in_expr
            each_in_expr: typing.Optional[Expr] = None

            # check for loop type
            for_each: bool = self._try_consume(TokenType.IDENTIFIER, "each")
            target_id: ExtendedID = self._parse_extended_id()
            # parse expressions based on for loop type
            if for_each:
                self._assert_consume(TokenType.IDENTIFIER, "in")
                each_in_expr = self._parse_expr()
            else:
                self._assert_consume(TokenType.SYMBOL, "=")
                eq_expr = self._parse_expr()
                self._assert_consume(TokenType.IDENTIFIER, "to")
                to_expr = self._parse_expr()
                if self._try_consume(TokenType.IDENTIFIER, "step"):
                    step_expr = self._parse_expr()
            self._assert_consume(TokenType.NEWLINE)
            # parse block statement list
            block_stmt_list: typing.List[BlockStmt] = []
            while not (
                self._try_token_type(TokenType.IDENTIFIER)
                and self._get_token_code() == "next"
            ):
                block_stmt_list.append(self._parse_block_stmt())
            # finish for statement
            self._assert_consume(TokenType.IDENTIFIER, "next")
            self._assert_consume(TokenType.NEWLINE)
            return ForStmt(
                target_id,
                block_stmt_list,
                eq_expr=eq_expr,
                to_expr=to_expr,
                step_expr=step_expr,
                each_in_expr=each_in_expr,
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_for_stmt()") from ex

    @staticmethod
    def parse_assign_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        # 'Set' is optional, don't throw if missing
        self._try_consume(TokenType.IDENTIFIER, "set")
        target_expr = self._parse_left_expr()

        # check for '='
        try:
            self._assert_consume(TokenType.SYMBOL, "=")
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_assign_stmt()") from ex

        # check for 'New'
        is_new = self._try_consume(TokenType.IDENTIFIER, "new")

        # parse assignment expression
        assign_expr = self._parse_left_expr() if is_new else self._parse_expr()
        return AssignStmt(target_expr, assign_expr, is_new=is_new)

    @staticmethod
    def parse_call_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "call")
            return CallStmt(self._parse_left_expr())
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_call_stmt()") from ex

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
        try:
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
                nonlocal self, terminal_type, terminal_code, terminal_casefold, terminal_pairs
                if len(terminal_pairs) > 0:
                    return any(
                        map(
                            lambda tpair: self._try_token_type(tpair[0])
                            and (
                                (tpair[1] is None)
                                or (self._get_token_code(terminal_casefold) == tpair[1])
                            ),
                            terminal_pairs,
                        )
                    )
                return self._try_token_type(terminal_type) and (
                    (terminal_code is None)
                    or (self._get_token_code(terminal_casefold) == terminal_code)
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
                        self._try_token_type(TokenType.SYMBOL)
                        and (self._get_token_code() == ",")
                    )
                ):
                    sub_safe_expr = self._parse_expr(True)
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
                if self._try_consume(TokenType.SYMBOL, ","):
                    # was the previous entry not empty?
                    if found_expr:
                        found_expr = False
                    else:
                        comma_expr_list.append(None)
                else:
                    # interpret as expression
                    comma_expr_list.append(
                        self._parse_expr()
                    )  # don't need sub_safe here
                    found_expr = True
            # DON'T CONSUME TERMINAL, LEAVE FOR CALLER
            del found_expr

            return SubCallStmt(left_expr, sub_safe_expr, comma_expr_list)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_inline_stmt()") from ex

    @staticmethod
    def parse_error_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "on")
            self._assert_consume(TokenType.IDENTIFIER, "error")

            # check for 'Resume'
            if self._try_consume(TokenType.IDENTIFIER, "resume"):
                self._assert_consume(TokenType.IDENTIFIER, "next")
                return ErrorStmt(resume_next=True)

            # check for 'GoTo'
            if self._try_consume(TokenType.IDENTIFIER, "goto"):
                if not self._try_token_type(TokenType.LITERAL_INT):
                    raise ParserError(
                        "Expected an integer literal after 'On Error GoTo'"
                    )
                goto_spec = self._pos_tok
                self._advance_pos()  # consume int literal
                return ErrorStmt(goto_spec=goto_spec)

            raise ParserError(
                "Expected either 'Resume Next' or 'GoTo <int>' after 'On Error'"
            )
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_error_stmt()") from ex

    @staticmethod
    def parse_exit_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "exit")
            # get exit type
            assert self._try_token_type(
                TokenType.IDENTIFIER
            ) and self._get_token_code() in [
                "do",
                "for",
                "function",
                "property",
                "sub",
            ], "Expected one of the following after 'Exit': 'Do', 'For', 'Function', 'Property', or 'Sub'"
            exit_tok = self._pos_tok
            self._advance_pos()  # consume exit type token
            return ExitStmt(exit_tok)
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_exit_stmt()") from ex

    @staticmethod
    def parse_erase_stmt(tkzr: Tokenizer) -> GlobalStmt:
        """

        Returns
        -------
        GlobalStmt

        Raises
        ------
        ParserError
        """
        try:
            self._assert_consume(TokenType.IDENTIFIER, "erase")
            return EraseStmt(self._parse_extended_id())
        except AssertionError as ex:
            raise ParserError("An error occurred in _parse_erase_stmt()") from ex

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
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            or self._try_token_type(TokenType.IDENTIFIER_IDDOT)
            or self._try_token_type(TokenType.IDENTIFIER_DOTID)
            or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
        ):
            # AssignStmt and SubCallStmt could start with a dotted identifier
            match self._get_token_code():
                case "set":
                    # 'Set' is optional for AssignStmt
                    # need to also handle assignment without leading 'Set'
                    return self._parse_assign_stmt()
                case "call":
                    return self._parse_call_stmt()
                case "on":
                    return self._parse_error_stmt()
                case "exit":
                    return self._parse_exit_stmt()
                case "erase":
                    return self._parse_erase_stmt()

            # no leading keyword, try parsing a left expression
            left_expr: LeftExpr = self._parse_left_expr()

            # assign statement?
            if self._try_consume(TokenType.SYMBOL, "="):
                assign_expr = self._parse_expr()
                return AssignStmt(left_expr, assign_expr)

            # must be a subcall statement
            return self._parse_subcall_stmt(
                left_expr,
                terminal_type,
                terminal_code,
                terminal_casefold,
                terminal_pairs=terminal_pairs,
            )
        raise ParserError(
            "Inline statement should start with an identifier or dotted identifier"
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
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            or self._try_token_type(TokenType.IDENTIFIER_IDDOT)
            or self._try_token_type(TokenType.IDENTIFIER_DOTID)
            or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
        ):
            # AssignStmt and SubCallStmt could start with a dotted identifier
            match self._get_token_code():
                case "dim":
                    return self._parse_var_decl()
                case "redim":
                    return self._parse_redim_stmt()
                case "if":
                    return self._parse_if_stmt()
                case "with":
                    return self._parse_with_stmt()
                case "select":
                    return self._parse_select_stmt()
                case "do" | "while":
                    return self._parse_loop_stmt()
                case "for":
                    return self._parse_for_stmt()

            # try to parse as inline statement
            ret_inline = self._parse_inline_stmt(TokenType.NEWLINE)
            try:
                self._assert_consume(TokenType.NEWLINE)
            except AssertionError as ex:
                raise ParserError("An error occurred in _parse_block_stmt()") from ex
            return ret_inline
        raise ParserError(
            "Block statement should start with an identifier or dotted identifier"
        )

    @staticmethod
    def parse_method_stmt(tkzr: Tokenizer) -> MethodStmt:
        """

        Returns
        -------
        MethodStmt
        """
        if self._try_token_type(TokenType.IDENTIFIER) and self._get_token_code() in [
            "const",
            "public",
            "private",
        ]:
            if self._try_consume(TokenType.IDENTIFIER, "public"):
                access_mod = AccessModifierType.PUBLIC
            elif self._try_consume(TokenType.IDENTIFIER, "private"):
                access_mod = AccessModifierType.PRIVATE
            else:
                access_mod = None
            return self._parse_const_decl(access_mod)
        # assume block statement
        return self._parse_block_stmt()

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
        if (
            self._try_token_type(TokenType.IDENTIFIER)
            or self._try_token_type(TokenType.IDENTIFIER_IDDOT)
            or self._try_token_type(TokenType.IDENTIFIER_DOTID)
            or self._try_token_type(TokenType.IDENTIFIER_DOTIDDOT)
        ):
            # AssignStmt and SubCallStmt could start with a dotted identifier
            match self._get_token_code():
                case "option":
                    return self._parse_option_explicit()
                case "class" | "const" | "sub" | "function":
                    # does not have an access modifier
                    return self._parse_global_decl()
                case "public" | "private":
                    return self._parse_access_modifier()
                case _:
                    # try to parse as a block statement
                    return self._parse_block_stmt()
        raise ParserError(
            "Global statement should start with an identifier or dotted identifier"
        )

    def parse(self) -> Program:
        """

        Returns
        -------
        Program

        Raises
        ------
        RuntimeError
        """
        if self._tkzr is None:
            raise RuntimeError("Must use the Parser class within a runtime context!")

        # program may optionally start with a newline token
        if self._try_token_type(TokenType.NEWLINE):
            self._advance_pos()  # consume newline

        global_stmts: typing.List[GlobalStmt] = []
        # don't catch any errors here!
        # if this method is run inside of a context, errors will be handled by __exit__()
        while self._pos_tok is not None:
            global_stmts.append(self._parse_global_stmt())
        return Program(global_stmts)
