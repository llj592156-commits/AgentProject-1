"""Skill Tool Adapter - Wrap skills as LangChain tools for MCP integration."""

from typing import Any, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from travel_planner.skills.skill_registry import LoadedSkill, get_skill_registry
from travel_planner.helpers.logs import get_logger


class SkillTool(BaseTool):
    """Adapter that wraps a skill as a LangChain BaseTool.

    Usage:
        # Get skill from registry
        registry = get_skill_registry()
        skill = registry.get_skill("weather")

        # Create tool
        tool = SkillTool.from_skill(skill)

        # Use with LLM
        llm_with_tools = llm.bind_tools([tool])
    """

    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = None

    @classmethod
    def from_skill(cls, skill: LoadedSkill) -> "SkillTool":
        """Create a SkillTool from a loaded skill.

        Args:
            skill: LoadedSkill instance

        Returns:
            SkillTool instance ready for use
        """
        if not skill:
            raise ValueError("Skill cannot be None")

        meta = skill.metadata
        args_schema = skill.input_schema or cls._default_input_schema()

        # Create instance first
        tool = cls(
            name=meta.id.replace("skill_", "") if meta.id.startswith("skill_") else meta.id,
            description=meta.description,
            args_schema=args_schema,
        )
        # Then set _skill directly (cannot pass to __init__ as Pydantic filters unknown fields)
        tool._skill = skill  # type: ignore
        return tool

    @staticmethod
    def _default_input_schema() -> Type[BaseModel]:
        """Default input schema for skills without explicit schema."""
        from pydantic import Field

        class DefaultInput(BaseModel):
            """Default input - accepts any parameters."""
            query: str = Field(..., description="Input query")

        return DefaultInput

    def _run(self, **kwargs) -> Any:
        """Synchronous execution."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            return asyncio.create_task(self._ainvoke(kwargs))
        except RuntimeError:
            return asyncio.run(self._ainvoke(kwargs))

    async def _ainvoke(self, input_data: dict, **kwargs: Any) -> Any:
        """Async execution for LangChain tool interface."""
        if not self._skill:
            raise ValueError("Skill not initialized")

        # Call the skill's run function
        result = self._skill.run_func(input_data)
        return result


def create_skill_tools() -> list[SkillTool]:
    """Create LangChain tools from all public skills.

    Returns:
        List of SkillTool instances
    """
    registry = get_skill_registry()
    tools = []

    for skill in registry.get_public_tools():
        if skill:
            tool = SkillTool.from_skill(skill)
            tools.append(tool)
            get_logger().info(f"Created skill tool: {tool.name}")

    return tools


def get_skill_tools() -> list[BaseTool]:
    """Get all skill-based tools for MCP integration.

    Returns:
        List of LangChain BaseTool instances
    """
    return create_skill_tools()
