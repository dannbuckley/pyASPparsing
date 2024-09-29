"""Parser for classic ASP code"""

import sys
import traceback
import typing

import attrs

from . import ParserError, TokenizerError
from .tokenizer import *


@attrs.define(slots=False)
class GlobalStmt:
    """"""


@attrs.define(slots=False)
class OptionExplicit(GlobalStmt):
    """"""


@attrs.define(slots=False)
class ClassDecl(GlobalStmt):
    """"""


@attrs.define(slots=False)
class FieldDecl(GlobalStmt):
    """"""


@attrs.define(slots=False)
class ConstDecl(GlobalStmt):
    """"""


@attrs.define(slots=False)
class SubDecl(GlobalStmt):
    """"""


@attrs.define(slots=False)
class FunctionDecl(GlobalStmt):
    """"""


@attrs.define(slots=False)
class BlockStmt(GlobalStmt):
    """"""


@attrs.define
class Program:
    """"""

    global_stmt_list: typing.List[GlobalStmt] = attrs.field(default=attrs.Factory(list))


@attrs.define()
class Parser:
    """"""

    codeblock: str
    output_file: typing.IO = attrs.field(default=sys.stdout)
    _tkzr: typing.Optional[Tokenizer] = attrs.field(
        default=None, repr=False, init=False
    )
    _pos_tok: typing.Optional[Token] = attrs.field(default=None, repr=False, init=False)

    def __enter__(self):
        """"""
        self._tkzr = iter(Tokenizer(self.codeblock))
        # preload first token
        self._pos_tok = next(
            self._tkzr, None
        )  # use next(..., None) instead of handling StopIteration
        return self

    def __exit__(self, exc_type, exc_val, tb):
        """"""
        if tb is not None:
            print("Parser exited with an exception!", file=self.output_file)
            print("Exception type:", exc_type, file=self.output_file)
            print("Exception value:", str(exc_val), file=self.output_file)
            print("Traceback:", file=self.output_file)
            traceback.print_tb(tb, file=self.output_file)
        self._pos_tok = None
        self._tkzr = None
        # suppress exception
        return True

    def _advance_pos(self):
        """"""
        if self._pos_tok is None:
            # iterator already exhausted, or __enter__() not called yet
            return False
        self._pos_tok = next(self._tkzr, None)
        return self._pos_tok is not None

    def parse(self):
        """"""
        if self._tkzr is None:
            raise RuntimeError("Must use the Parser class within a runtime context!")
