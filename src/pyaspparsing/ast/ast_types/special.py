"""ASP high-level constructs"""

import enum
from typing import Self, Generator, Union
import attrs
from attrs.validators import deep_iterable, instance_of
from .base import FormatterMixin, Expr, GlobalStmt, BlockStmt
from ..tokenizer.token_types import Token


@attrs.define(repr=False, slots=False)
class ProcessingSetting(FormatterMixin):
    """Key-value pair contained within processing directive

    Attributes
    ----------
    config_kw : Token
    config_value : Token
    """

    config_kw: Token
    config_value: Token


@attrs.define(repr=False, slots=False)
class ProcessingDirective(FormatterMixin, GlobalStmt):
    """Processing directive AST type (&lt;%@ ... %&gt;)

    Attributes
    ----------
    settings : List[ProcessingSetting], default=[]
    """

    settings: list[ProcessingSetting] = attrs.field(default=attrs.Factory(list))


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class IncludeType(enum.IntEnum):
    """Enumeration of valid include file types"""

    INCLUDE_FILE = enum.auto()
    INCLUDE_VIRTUAL = enum.auto()


@attrs.define(repr=False, slots=False)
class IncludeFile(FormatterMixin, BlockStmt):
    """Include file AST type

    Attributes
    ----------
    include_type : IncludeType
    include_path : Token
    """

    include_type: IncludeType = attrs.field(validator=instance_of(IncludeType))
    include_path: str = attrs.field(validator=instance_of(str))


@attrs.define(repr=False, slots=False)
class OutputDirective(FormatterMixin):
    """Output directive for writing expressions directly to response (&lt;%= ... %&gt;)

    Attributes
    ----------
    extent : slice
    output_expr : Expr
    """

    extent: slice
    output_expr: Expr


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class OutputType(enum.IntEnum):
    """Enumeration of valid output types for defining stitch order of output text block"""

    OUTPUT_RAW = enum.auto()
    OUTPUT_DIRECTIVE = enum.auto()


@attrs.define(repr=False, slots=False)
class OutputText(FormatterMixin, BlockStmt):
    """Output text AST type

    Represents content that is written directly to the response

    Attributes
    ----------
    chunks : List[str], default=[]
    directives : List[OutputDirective], default=[]
    stitch_order : List[Tuple[OutputType, int]], default=[]

    Methods
    -------
    merge(other)
        Combine two output text objects
    stitch()
        Reconstruct the correct output
    """

    chunks: list[str] = attrs.field(
        default=attrs.Factory(list), validator=deep_iterable(instance_of(str))
    )
    directives: list[OutputDirective] = attrs.field(default=attrs.Factory(list))
    # stitch_order defines how the output is to be reconstructed when evaluating code
    # this will match the order in which output elements are encountered
    stitch_order: list[tuple[OutputType, int]] = attrs.field(
        default=attrs.Factory(list), kw_only=True
    )

    def __attrs_post_init__(self):
        chunks_len = len(self.chunks)
        directives_len = len(self.directives)
        if len(self.chunks) > 0 or len(self.directives) > 0:
            try:
                # must provide reconstruction info
                assert len(self.stitch_order) > 0
                # verify that indices are valid, unique, and provided in increasing order
                chunks_used: int = -1
                directives_used: int = -1
                for out_type, out_idx in self.stitch_order:
                    match out_type:
                        case OutputType.OUTPUT_RAW:
                            assert (
                                chunks_used < out_idx < chunks_len
                            ), f"Invalid index {out_idx} for raw output element"
                            chunks_used = out_idx
                        case OutputType.OUTPUT_DIRECTIVE:
                            assert (
                                directives_used < out_idx < directives_len
                            ), f"Invalid index {out_idx} for output directive element"
                            directives_used = out_idx
            except AssertionError as ex:
                raise ValueError(
                    "An error occurred when validating OutputText object"
                ) from ex

    def merge(self, other: Self) -> Self:
        """Combines this OutputText with `other` to produce a merged OutputText object

        Parameters
        ----------
        other : OutputText
        """
        num_chunks = len(self.chunks)
        num_directives = len(self.directives)
        return OutputText(
            [*self.chunks, *other.chunks],
            [*self.directives, *other.directives],
            stitch_order=[
                *self.stitch_order,
                *map(
                    lambda x: (
                        x[0],
                        # adjust stitch index
                        x[1]
                        + (
                            num_chunks
                            if x[0] == OutputType.OUTPUT_RAW
                            else num_directives
                        ),
                    ),
                    other.stitch_order,
                ),
            ],
        )

    def stitch(
        self,
    ) -> Generator[tuple[OutputType, Union[str, OutputDirective]], None, None]:
        """Stitch the output text block together in the order it was originally specified

        Yields
        ------
        Tuple[OutputType, slice | OutputDirective]
        """
        for out_type, out_idx in self.stitch_order:
            match out_type:
                case OutputType.OUTPUT_RAW:
                    yield (out_type, self.chunks[out_idx])
                case OutputType.OUTPUT_DIRECTIVE:
                    yield (out_type, self.directives[out_idx])
