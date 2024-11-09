"""virtual_dir module"""

from contextlib import ExitStack
from io import StringIO
from pathlib import Path
from typing import Optional

import attrs

from ..ast.ast_types import Program
from ..ast.tokenizer.state_machine import Tokenizer


@attrs.define
class VirtualDirectory:
    """
    Attributes
    ----------
    root_name : Path
        Root path containing the virtual name of the directory
    actual_path : Path
        Physical path of the virtual directory
    """

    root_name: Path = attrs.field(validator=attrs.validators.instance_of(Path))
    actual_path: Path = attrs.field()
    # cache included files upon first request
    # if an error occurs during parsing, use None as placeholder
    _req_cache: dict[Path, Optional[Program]] = attrs.field(
        default=attrs.Factory(dict), init=False
    )

    @actual_path.validator
    def _check_actual_path(self, _, value: Path):
        if not isinstance(value, Path) or not value.exists() or not value.is_dir():
            raise ValueError(
                "actual_path must point to an accessible physical directory"
            )

    def request(self, file_path: Path) -> Optional[Program]:
        """
        Parameters
        ----------
        file_path : Path
            Path to a file in the virtual directory.
            Must be a subpath of root_name
        """
        rel_path = file_path.relative_to(self.root_name)
        if rel_path in self._req_cache:
            # file was requested once before, use cached program
            return self._req_cache[rel_path]
        # check for include file in physical directory
        phys_path = self.actual_path / rel_path
        if not phys_path.exists():
            # include file does not exist
            self._req_cache[rel_path] = None
            return None
        try:
            with ExitStack() as stack:
                # consume error messages with throwaway buffer
                err_msg = stack.enter_context(StringIO())
                inc_file = stack.enter_context(
                    open(phys_path, "r")  # pylint: disable=W1514
                )
                tkzr: Tokenizer = stack.enter_context(
                    Tokenizer(inc_file.read(), False, err_msg)
                )
                # try to parse file
                self._req_cache[rel_path] = Program.from_tokenizer(tkzr)
            return self._req_cache[rel_path]
        except Exception:  # pylint: disable=W0718
            # error type does not matter
            # something went wrong, so use None placeholder
            self._req_cache[rel_path] = None
            return None
