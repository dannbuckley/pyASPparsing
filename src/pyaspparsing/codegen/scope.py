"""Scope stack management"""

import enum
import attrs
import networkx as nx


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class ScopeType(enum.Enum):
    """Enumeration of valid scope types"""

    SCOPE_SCRIPT = enum.auto()
    SCOPE_CLASS = enum.auto()
    SCOPE_SUB = enum.auto()
    SCOPE_FUNCTION = enum.auto()
    SCOPE_IF = enum.auto()
    SCOPE_WITH = enum.auto()
    SCOPE_SELECT = enum.auto()
    SCOPE_LOOP = enum.auto()
    SCOPE_FOR = enum.auto()


@attrs.define
class ScopeManager:
    """
    Attributes
    ----------
    """

    scope_registry: nx.Graph = attrs.field(
        default=attrs.Factory(nx.Graph), repr=False, init=False
    )
    scope_stack: list[int] = attrs.field(default=attrs.Factory(list), init=False)
    _curr_scope_id: int = attrs.field(default=-1, repr=False, init=False)

    def __attrs_post_init__(self):
        # script scope will always be at ID 0 (zero)
        self.enter_scope(ScopeType.SCOPE_SCRIPT)

    @property
    def current_scope(self) -> int:
        """
        Returns
        -------
        int

        Raises
        ------
        AssertionError
        """
        assert len(self.scope_stack) > 0
        return self.scope_stack[-1]

    def enter_scope(self, scope_type: ScopeType):
        """Enter into a narrower scope and push it onto the stack

        Parameters
        ----------
        scope_type : ScopeType
        """
        self._curr_scope_id += 1
        self.scope_registry.add_node(self._curr_scope_id, scope_type=scope_type)
        if len(self.scope_stack) > 0:
            self.scope_registry.add_edge(self.scope_stack[-1], self._curr_scope_id)
        self.scope_stack.append(self._curr_scope_id)

    def exit_scope(self):
        """Pop the current scope off the stack"""
        assert len(self.scope_stack) > 0
        self.scope_stack.pop()

    def get_scope_environment(self, scope_id: int) -> list[int]:
        """Get list of enclosing scopes for the given `scope_id`

        Parameters
        ----------
        scope_id : int

        Returns
        -------
        List[int]
        """
        return nx.dijkstra_path(self.scope_registry, 0, scope_id)
