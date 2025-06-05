

from travel_planner.nodes.base_node import BaseNode
from travel_planner.models.state import TravelPlannerState


class CollectTripParamsNode(BaseNode):
    """
    First node in the graph: receives **raw** form data from Reflex,
    validates it via `TripParamsState`, logs, and passes the
    structured state downstream.
    """
    def __init__(self):
        super().__init__()
        # No additional initialization needed for this node

    # synchronous implementation (fast, no I/O)
    def run(self, state: TravelPlannerState) -> TravelPlannerState:  # type: ignore[override]
        self.logger.info(
            "Collected trip params: %s ➜ %s | %s → %s | €%.2f | pax=%d | interests=%s",
            state.origin,
            state.destination,
            state.date_from,
            state.date_to,
            state.budget,
            state.pax,
            state.interests,
        )
        # Nothing else to compute; state validation already happened.
        return state
