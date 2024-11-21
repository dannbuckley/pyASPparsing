"""Code generation return value helper type"""

from __future__ import annotations
import attrs
from attrs.validators import instance_of


@attrs.define
class CodegenReturn:
    """Return value for code generation functions"""

    indent_width: int = attrs.field(default=1, validator=instance_of(int), kw_only=True)
    _script_lines: list[str] = attrs.field(default=attrs.Factory(list), init=False)

    def __str__(self):
        return "\n".join(self._script_lines)

    def append(self, line: str):
        """Append a line of generated code to the function return value

        Parameters
        ----------
        line : str
        """
        if not isinstance(line, str):
            raise ValueError("line must be a string")
        self._script_lines.append(line)

    def combine(self, other: CodegenReturn, *, indent: bool = True):
        """Append the content of `other` to the current instance

        Parameters
        ----------
        other : CodegenReturn
        indent : bool, default=True
        """
        # pylint: disable=W0212
        #         ~~~~~~~~^^^^^ _script_lines is "protected",
        #                       but we're accessing from the same class
        if not isinstance(other, CodegenReturn):
            raise ValueError("other must be a CodegenReturn instance")
        if not isinstance(indent, bool):
            raise ValueError("indent must be a boolean")
        self._script_lines.extend(
            map(lambda x: (" " * self.indent_width) + x, other._script_lines)
            if indent
            else other._script_lines
        )
