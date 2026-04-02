#ok
from typing import Generic, TypeVar

from pydantic import BaseModel

from travel_planner.helpers.logs import get_logger

State = TypeVar("State", bound=BaseModel) # 犂点状态类型，必须是BaseModel的子类。


class BaseNode(Generic[State]): #Generic是用来 使用 这个占位符的，它让一个类能够接受这个类型作为参数（“我这个类能处理 T 或 State 这种东西”）
    def __init__(self) -> None:
        self.logger = get_logger()

    @property
    def node_id(self) -> str:
        return self.__class__.__name__

    # Either implement async_run or run or both.
    # That's why it's not annotated with @abstractmethod.
    async def async_run(self, state: State) -> State:
        return state

    def run(self, state: State) -> State:
        return state
