"""linker module"""

from pathlib import Path
import typing
import attrs
from ..ast.ast_types import Program
from .virtual_dir import VirtualDirectory


@attrs.define
class Linker:
    """
    Attributes
    ----------
    virtual_dirs : Dict[str, VirtualDirectory]
        Registry of virtual directories

    Methods
    -------
    register_dir(root_name, act_path)
        Register a virtual directory in virtual_dirs
    request(file_path)
        Request a file from a registered virtual directory
    """

    virtual_dirs: typing.Dict[str, VirtualDirectory] = attrs.field(
        default=attrs.Factory(dict), init=False
    )

    def register_dir(self, root_name: str, act_path: Path):
        """
        Parameters
        ----------
        root_name : str
            The name used to identify the virtual directory
        act_path : Path
            Physical path of the virtual directory

        Raises
        ------
        AssertionError
            If another virtual directory has already been registered under root_name
        """
        assert (
            root_name not in self.virtual_dirs
        ), f"A virtual directory already exists under the name '{root_name}'"
        self.virtual_dirs[root_name] = VirtualDirectory(Path(f"/{root_name}"), act_path)

    def request(self, file_path: Path) -> typing.Optional[Program]:
        """
        Parameters
        ----------
        file_path : Path
            Path to a file in a virtual directory.
            The virtual directory must already have been registered using register_dir()

        Returns
        -------
        Program | None
            Program if the file exists and can be parsed;
            otherwise, None

        Raises
        ------
        AssertionError
            If the virtual directory associated with file_path has not been registered
        """
        root_name = file_path.parts[1]
        assert (
            root_name in self.virtual_dirs
        ), f"No virtual directory has been registered for the name '{root_name}'"
        return self.virtual_dirs[root_name].request(file_path)
