"""Scope stack management"""

from contextlib import contextmanager
import enum
import attrs
import networkx as nx


@enum.verify(enum.CONTINUOUS, enum.UNIQUE)
class ScopeType(enum.Enum):
    """Enumeration of valid scope types"""

    # built-in ASP objects and functions
    SCOPE_SCRIPT_BUILTIN = enum.auto()
    # user-defined objects and functions
    SCOPE_SCRIPT_USER = enum.auto()
    SCOPE_CLASS = enum.auto()
    # template scope for user-defined subs
    SCOPE_SUB_DEFINITION = enum.auto()
    # custom scope for calling user-defined subs
    # should start from a copy of the *_DEFINITION scope
    # (if the definition scope exists)
    SCOPE_SUB_CALL = enum.auto()
    # template scope for user-defined functions
    SCOPE_FUNCTION_DEFINITION = enum.auto()
    # custom scope for calling user-defined functions
    # should start from a copy of the *_DEFINITION scope
    # (if the definition scope exists)
    SCOPE_FUNCTION_CALL = enum.auto()
    # scope for the entire if statement
    SCOPE_IF = enum.auto()
    # scope for each if/elseif/else branch
    SCOPE_IF_BRANCH = enum.auto()
    SCOPE_WITH = enum.auto()
    # scope for the entire select statement
    SCOPE_SELECT = enum.auto()
    # scope for each case statement
    SCOPE_SELECT_CASE = enum.auto()
    SCOPE_LOOP = enum.auto()
    SCOPE_FOR = enum.auto()


@attrs.define
class ScopeManager:
    """
    Attributes
    ----------
    scope_registry : networkx.DiGraph
    scope_stack : list[int]

    Methods
    -------
    enter_scope(scope_type)
    exit_scope()
    temporary_scope(scope_type)
    get_scope_environment(scope_id)
    """

    scope_registry: nx.DiGraph = attrs.field(
        default=attrs.Factory(nx.DiGraph), repr=False, init=False
    )
    scope_stack: list[int] = attrs.field(default=attrs.Factory(list), init=False)
    _curr_scope_id: int = attrs.field(default=-1, repr=False, init=False)

    def __attrs_post_init__(self):
        # top-level script scope will always be at ID 0 (zero)
        self.enter_scope(ScopeType.SCOPE_SCRIPT_BUILTIN)

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

    @property
    def current_environment(self) -> list[int]:
        """Get all scopes visible to the current scope
        (including the current scope)

        Returns
        -------
        list[int]
        """
        return self.get_scope_environment(self.current_scope)

    def enter_scope(self, scope_type: ScopeType):
        """Enter into a narrower scope and push it onto the stack

        Parameters
        ----------
        scope_type : ScopeType
        """
        assert isinstance(scope_type, ScopeType)
        self._curr_scope_id += 1
        self.scope_registry.add_node(self._curr_scope_id, scope_type=scope_type)
        if len(self.scope_stack) > 0:
            # link to enclosing scope
            self.scope_registry.add_edge(self.scope_stack[-1], self._curr_scope_id)
        self.scope_stack.append(self._curr_scope_id)

    def exit_scope(self):
        """Pop the current scope off the stack"""
        assert len(self.scope_stack) > 0
        self.scope_stack.pop()

    @contextmanager
    def temporary_scope(self, scope_type: ScopeType):
        """Temporarily enter into a new scope using a context manager

        Parameters
        ----------
        scope_type : ScopeType
        """
        self.enter_scope(scope_type)
        try:
            yield
        finally:
            self.exit_scope()

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
