from enum import Enum

from pydantic import BaseModel, Field


class Routes(Enum):
    TRAVEL_PLANNER = "travel_planner" #旅行规划流
    CHITCHAT = "chitchat" #闲聊流
    ESCALATION = "escalation" #升级流
    TURKISH_AIRLINES = "turkish_airlines" #土耳其航空公司流


class RoutingDecision(BaseModel):
    """Model for the router node to decide the task type"""

    predicted_route: Routes = Field(description="The type of task based on user input") #预测选择的路由
    reasoning: str = Field(description="Brief explanation of why this route was chosen") #路由选择理由
