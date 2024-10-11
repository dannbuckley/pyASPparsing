"""ASP high-level constructs"""

import enum
import typing
import attrs
from .base import FormatterMixin, Expr, BlockStmt


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class IncludeType(enum.IntEnum):
    """"""

    INCLUDE_FILE = enum.auto()
    INCLUDE_VIRTUAL = enum.auto()


@attrs.define(repr=False, slots=False)
class IncludeFile(FormatterMixin, BlockStmt):
    """"""

    include_type: IncludeType
    include_path: slice


@attrs.define(repr=False, slots=False)
class OutputDirective(FormatterMixin):
    """"""

    extent: slice
    output_expr: Expr


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class OutputType(enum.IntEnum):
    """Enumeration of valid output types for defining stitch order of output text block"""

    OUTPUT_RAW = enum.auto()
    OUTPUT_DIRECTIVE = enum.auto()


@attrs.define(repr=False, slots=False)
class OutputText(FormatterMixin, BlockStmt):
    """
    Attributes
    ----------
    chunks : List[slice], default=[]
    directives : List[OutputDirective], default=[]
    stitch_order : List[Tuple[OutputType, int]], default=[]
    """

    chunks: typing.List[slice] = attrs.field(default=attrs.Factory(list))
    directives: typing.List[OutputDirective] = attrs.field(default=attrs.Factory(list))
    # stitch_order defines how the output is to be reconstructed when evaluating code
    # this will match the order in which output elements are encountered
    stitch_order: typing.List[typing.Tuple[OutputType, int]] = attrs.field(
        default=attrs.Factory(list), kw_only=True
    )

    def __attrs_post_init__(self):
        chunks_len = len(self.chunks)
        directives_len = len(self.directives)
        if len(self.chunks) > 0 or len(self.directives) > 0:
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
                        ), f"Invalid index {out_idx} for raw output element in output text block"
                        chunks_used = out_idx
                    case OutputType.OUTPUT_DIRECTIVE:
                        assert (
                            directives_used < out_idx < directives_len
                        ), f"Invalid index {out_idx} for output directive element in output text block"
                        directives_used = out_idx

    def stitch(
        self,
    ) -> typing.Generator[
        typing.Tuple[OutputType, typing.Union[slice, OutputDirective]], None, None
    ]:
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
