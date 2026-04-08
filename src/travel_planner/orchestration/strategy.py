"""Strategy patterns for routing and scheduling decisions."""

from abc import ABC, abstractmethod
from typing import Any, Callable

from travel_planner.models.state import TravelPlannerState
from travel_planner.helpers.logs import get_logger


class RoutingStrategy(ABC):
    """Abstract strategy for routing decisions.

    Subclasses implement specific routing logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this strategy."""
        pass

    @abstractmethod
    def matches(self, state: TravelPlannerState) -> bool:
        """Check if this strategy applies to the given state."""
        pass

    @abstractmethod
    def get_next_node(self, state: TravelPlannerState) -> str:
        """Get the next node/skill to execute."""
        pass


class IntentBasedRoutingStrategy(RoutingStrategy):
    """Route based on detected user intent."""

    def __init__(self, intent_map: dict[str, str]):
        """
        Args:
            intent_map: Mapping from intent labels to node names
        """
        self._intent_map = intent_map
        self._logger = get_logger()

    @property
    def name(self) -> str:
        return "intent_based"

    def matches(self, state: TravelPlannerState) -> bool:
        """Check if routing decision is available."""
        return state.routing_decision is not None

    def get_next_node(self, state: TravelPlannerState) -> str:
        """Get next node based on routing decision."""
        if not state.routing_decision:
            return "escalation_node"

        predicted_route = state.routing_decision.predicted_route.value
        return self._intent_map.get(predicted_route, "escalation_node")


class KeywordBasedRoutingStrategy(RoutingStrategy):
    """Route based on keywords in user message."""

    def __init__(
        self,
        keyword_map: dict[str, list[str]],
        default_node: str = "chitchat_node",
    ):
        """
        Args:
            keyword_map: Mapping from route names to keyword lists
            default_node: Default node if no keywords match
        """
        self._keyword_map = keyword_map
        self._default_node = default_node
        self._logger = get_logger()

    @property
    def name(self) -> str:
        return "keyword_based"

    def matches(self, state: TravelPlannerState) -> bool:
        """Always matches - falls back to default."""
        return True

    def get_next_node(self, state: TravelPlannerState) -> str:
        """Get next node based on keyword matching."""
        user_message = state.user_prompt.lower()

        for route, keywords in self._keyword_map.items():
            if any(keyword in user_message for keyword in keywords):
                self._logger.info(
                    f"Keyword routing matched '{route}' for message: {user_message[:50]}..."
                )
                return f"{route}_node"

        return self._default_node


class PriorityRoutingStrategy(RoutingStrategy):
    """Route based on priority rules.

    Useful for VIP users, urgent requests, etc.
    """

    def __init__(
        self,
        priority_rules: list[tuple[Callable[[TravelPlannerState], bool], str]],
        fallback_strategy: RoutingStrategy | None = None,
    ):
        """
        Args:
            priority_rules: List of (condition, node_name) tuples
            fallback_strategy: Strategy to use if no rules match
        """
        self._priority_rules = priority_rules
        self._fallback_strategy = fallback_strategy
        self._logger = get_logger()

    @property
    def name(self) -> str:
        return "priority_based"

    def matches(self, state: TravelPlannerState) -> bool:
        """Check if any priority rule applies."""
        return True

    def get_next_node(self, state: TravelPlannerState) -> str:
        """Get next node based on priority rules."""
        for condition, node_name in self._priority_rules:
            if condition(state):
                self._logger.info(f"Priority routing matched: {node_name}")
                return node_name

        # Fall back to fallback strategy
        if self._fallback_strategy:
            return self._fallback_strategy.get_next_node(state)

        return "escalation_node"


class RoutingStrategyRegistry:
    """Registry and executor for routing strategies."""

    def __init__(self):
        self._strategies: list[RoutingStrategy] = []
        self._logger = get_logger()

    def register(self, strategy: RoutingStrategy) -> None:
        """Register a routing strategy."""
        self._strategies.append(strategy)
        self._logger.info(f"Routing strategy registered: {strategy.name}")

    def execute(self, state: TravelPlannerState) -> str:
        """Execute strategies in order until one matches.

        Args:
            state: Current travel planner state

        Returns:
            Next node name to execute
        """
        for strategy in self._strategies:
            if strategy.matches(state):
                self._logger.debug(f"Using routing strategy: {strategy.name}")
                return strategy.get_next_node(state)

        # Default fallback
        self._logger.warning("No routing strategy matched, defaulting to escalation")
        return "escalation_node"
