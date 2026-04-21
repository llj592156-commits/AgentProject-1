"""Skills Layer - Standardized capability units for travel planner.

Skill Architecture:
- Each skill is a standalone module with schema.py, impl.py, and SKILL.md
- Skills are pure functions with standardized input/output schemas
- Skills can be discovered and invoked dynamically

Available Skills:
- weather: Query real-time weather for travel destinations
"""

# Legacy skills (deprecated - use new skill modules)
from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult
from travel_planner.skills.planning_skill import PlanningSkill
from travel_planner.skills.booking_skill import BookingSkill
from travel_planner.skills.info_skill import InfoSkill

# New standard skill modules
from travel_planner.skills.weather import run as run_weather, WeatherInput, WeatherOutput

__all__ = [
    # New standard skills
    "run_weather",
    "WeatherInput",
    "WeatherOutput",
]
