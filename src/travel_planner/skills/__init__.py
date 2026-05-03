"""Skills Layer - Standardized capability units for travel planner.

Skill Architecture:
- Each skill is a standalone module with schema.py, impl.py, and SKILL.md
- Skills are pure functions with standardized input/output schemas
- Skills can be discovered and invoked dynamically

Available Skills:
- weather: Query real-time weather for travel destinations
"""

from travel_planner.skills.weather import run as run_weather, WeatherInput, WeatherOutput

__all__ = [
    "run_weather",
    "WeatherInput",
    "WeatherOutput",
]
