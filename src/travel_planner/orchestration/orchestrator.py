"""Orchestration Layer - Coordinates skills and tools to execute complex workflows.

This module provides:
- SkillOrchestrator: Manages skill registration, selection, and execution
- ExecutionPlan: Represents a sequence of skill executions
- Strategy patterns for routing and scheduling
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult
from travel_planner.models.state import TravelPlannerState
from travel_planner.helpers.logs import get_logger


@dataclass
class ExecutionPlan:
    """Represents a plan for executing skills in sequence or parallel."""

    steps: list[tuple[str, str]] = field(default_factory=list)  # (skill_name, method) 顺序执行的步骤
    parallel_groups: list[list[str]] = field(default_factory=list) #并行执行的技能组
    conditionals: dict[str, Callable[[TravelPlannerState], bool]] = field(
        default_factory=dict
    ) #条件检查

    def add_step(self, skill_name: str, method: str = "execute") -> None: 
        """Add a sequential step to the plan."""
        self.steps.append((skill_name, method))

    def add_parallel_group(self, skill_names: list[str]) -> None: 
        """Add a group of skills to execute in parallel."""
        self.parallel_groups.append(skill_names)

    def add_conditional( #添加条件检查
        self, name: str, condition: Callable[[TravelPlannerState], bool]
    ) -> None:
        """Add a conditional check."""
        self.conditionals[name] = condition


class SkillRegistry: #技能注册表 管理所有可用技能
    """Registry for all available skills."""

    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}
        self._logger = get_logger()

    def register(self, skill: BaseSkill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill
        self._logger.info(f"Skill registered: {skill.name}")

    def unregister(self, skill_name: str) -> None:
        """Unregister a skill by name."""
        if skill_name in self._skills:
            del self._skills[skill_name]
            self._logger.info(f"Skill unregistered: {skill_name}")

    def get(self, skill_name: str) -> BaseSkill | None:
        """Get a skill by name."""
        return self._skills.get(skill_name)

    def get_all(self) -> dict[str, BaseSkill]:
        """Get all registered skills."""
        return self._skills.copy()

    def list_skills(self) -> list[dict[str, str]]:
        """List all skills with their descriptions."""
        return [
            {"name": skill.name, "description": skill.description}
            for skill in self._skills.values()
        ]

#技能编排器
class SkillOrchestrator:
    """Orchestrates skill execution based on context and configuration.

    Usage:
        orchestrator = SkillOrchestrator()
        orchestrator.register_skill(PlanningSkill())
        result = await orchestrator.execute(context, "planning")
    """

    def __init__(self):
        self._registry = SkillRegistry() #技能注册表
        self._logger = get_logger() #日志器
        self._tools: dict[str, Any] = {} #工具列表

    def register_skill(self, skill: BaseSkill) -> None:
        """Register a skill."""
        self._registry.register(skill)

    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool for skills to use."""
        self._tools[name] = tool

    async def execute(
        self,
        state: TravelPlannerState,
        skill_name: str,
        preconditions: list[Callable[[TravelPlannerState], bool]] | None = None,
    ) -> SkillResult: #执行指定技能
        """Execute a skill by name.

        Args:
            state: Current travel planner state
            skill_name: Name of the skill to execute
            preconditions: Optional list of precondition checks

        Returns:
            SkillResult from the skill execution
        """
        skill = self._registry.get(skill_name) #根据调用的技能名称获取技能对象
        if not skill:
            return SkillResult.fail(
                message=f"Unknown skill: {skill_name}",
                error=f"Skill '{skill_name}' not found",
            )

        # Check preconditions
        if preconditions:
            for precondition in preconditions:
                if not precondition(state):
                    return SkillResult.fail(
                        message=f"Precondition failed for skill: {skill_name}",
                        error="Precondition check failed",
                    )

        # Check skill's own can_execute
        context = SkillContext(state=state, tools=self._tools)
        if not await skill.can_execute(context):
            return SkillResult.fail(
                message=f"Skill {skill_name} cannot execute with current context",
                error="Skill prerequisites not met",
            )

        # Execute the skill
        self._logger.info(f"Executing skill: {skill_name}")
        result = await skill.execute(context)

        # Apply state updates if any
        if result.state_updates:
            self._apply_state_updates(state, result.state_updates)

        return result

    async def execute_plan(
        self, state: TravelPlannerState, plan: ExecutionPlan
    ) -> list[SkillResult]:
        """Execute a sequence of skills according to a plan."""
        results: list[SkillResult] = []

        # Execute sequential steps
        for skill_name, method in plan.steps:
            result = await self.execute(state, skill_name)
            results.append(result)
            if not result.success:
                break  # Stop on first failure

        # Execute parallel groups
        for group in plan.parallel_groups:
            # TODO: Implement parallel execution with asyncio.gather
            for skill_name in group:
                result = await self.execute(state, skill_name)
                results.append(result)

        return results

    def _apply_state_updates(
        self, state: TravelPlannerState, updates: dict[str, Any]
    ) -> None:
        """Apply state updates from skill result."""
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                self._logger.warning(
                    f"State update ignored: '{key}' not found in TravelPlannerState"
                )

    def list_available_skills(self) -> list[dict[str, str]]:
        """List all available skills."""
        return self._registry.list_skills()
