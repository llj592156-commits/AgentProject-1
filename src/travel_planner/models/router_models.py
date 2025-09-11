from pydantic import BaseModel, Field
from typing import Literal


class RoutingDecision(BaseModel):
    """Model for the router node to decide the task type"""
    task_type: Literal["travel_planner", "chitchat", "escalation"] = Field(
        description="The type of task based on user input"
    )
    confidence: float = Field(
        description="Confidence score for the routing decision (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this route was chosen"
    )
