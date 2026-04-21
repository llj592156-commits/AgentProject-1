"""Weather Skill - Query real-time weather for travel destinations.

This module provides the weather skill for the travel planner.
Usage:
    from travel_planner.skills.weather import run, WeatherInput, WeatherOutput

    result = run({"city": "成都", "province": "四川省"})
"""

from .schema import WeatherInput, WeatherOutput
from .impl import run

__all__ = ["WeatherInput", "WeatherOutput", "run"]
