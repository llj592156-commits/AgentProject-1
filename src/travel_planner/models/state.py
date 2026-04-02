from datetime import date
from typing import Annotated

from langgraph.graph.message import BaseMessage, add_messages
from pydantic import BaseModel, Field

from travel_planner.models.router_models import RoutingDecision

#酒店信息模型
class HotelInfo(BaseModel):
    name: str
    address: str
    price_per_nfght: float
    currency: str = "EUR"
    rating: float | None = None
    provider_id: str

#酒店API参数模型
class HotelAPIParams(BaseModel):
    cityCode: str = Field(..., description="IATA city code (e.g. PAR)")
    checkInDate: date
    checkOutDate: date
    adults: int
    roomQuantity: int = 1
    currency: str = "EUR"
    priceRange: str = Field(..., description="Format 'min-max', e.g. '0-150'")
    sort: str = "PRICE"


#旅行参数模型
class TravelParams(BaseModel):
    origin: str | None = None
    destination: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    budget: float | None = None

#全局工作状态
class TravelPlannerState(BaseModel):
    """State object produced by ExtractTripParamsNode."""
    user_prompt: str # 用户输入的原始提示
    messages: Annotated[list[BaseMessage], add_messages] = [] # 与用户交互的消息列表
    travel_params: TravelParams | None = None # 提取的旅行参数对象
    missing_trip_params: list[str] = [] # 缺少的旅行参数列表
    routing_decision: RoutingDecision | None = None # 路由决策对象
    last_ai_message: str | None = None # 最后一条AI回复
