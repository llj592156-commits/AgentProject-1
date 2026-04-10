"""Base class for all skills in the capability layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
import time

from travel_planner.models.state import TravelPlannerState
from travel_planner.tools.base_tool import ToolResult
from travel_planner.helpers.logs import get_logger


@dataclass
class SkillResult: #技能执行结果类
    """Result from skill execution."""

    success: bool
    message: str
    state_updates: dict[str, Any] = field(default_factory=dict)
    data: Any | None = None
    error: str | None = None

    @classmethod
    def ok(
        cls, message: str, state_updates: dict[str, Any] | None = None, data: Any = None
    ) -> "SkillResult":
        """Create a successful result."""
        return cls(success=True, message=message, state_updates=state_updates or {}, data=data)

    @classmethod
    def fail(cls, message: str, error: str | None = None) -> "SkillResult":
        """Create a failed result."""
        return cls(success=False, message=message, error=error or message)


@dataclass
class SkillContext: #技能执行状态类
    """Context passed to skills during execution.

    Provides access to:
    - Current state
    - Tool layer components
    - Shared resources
    """

    state: TravelPlannerState 
    tools: dict[str, Any] = field(default_factory=dict)

    def get_tool(self, name: str) -> Any | None:
        """Get a tool by name."""
        return self.tools.get(name)


class BaseSkill(ABC):
    """Abstract base class for all skills.

    Skills are higher-level than tools - they combine multiple tools
    to achieve a specific capability.

    Example: BookingSkill combines FlightSearchTool + HotelSearchTool + PaymentTool
    """

    def __init__(self):
        self._logger = get_logger()

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this skill."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this skill does."""
        pass

    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the skill with the given context.

        Args:
            context: The execution context containing state and tools

        Returns:
            SkillResult with success status and state updates
        """
        pass

    async def can_execute(self, context: SkillContext) -> bool:
        """Check if this skill can execute with the given context.

        Override to add precondition checks.
        """
        return True

    def _log_execution(
        self, phase: str, message: str, level: str = "info"
    ) -> None:
        """Log skill execution phases."""
        log_method = getattr(self._logger, level, self._logger.info) #获取logger实例的方法，如果不存在则使用info方法
        log_method(f"[{self.name}] {phase}: {message}") #打印这些信息
