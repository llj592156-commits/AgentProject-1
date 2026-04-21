"""Example: Using the new Weather Skill.

This example demonstrates how to use the standardized Weather Skill
to query real-time weather information.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from travel_planner.skills.weather import run, WeatherInput, WeatherOutput


async def main():
    """Test Weather Skill execution."""
    print("=" * 50)
    print("Weather Skill Example - Query Real-time Weather")
    print("=" * 50)

    # Test 1: Query weather for Suzhou
    print("\n[Test 1] Query weather for Suzhou, Jiangsu...")
    result = run({"city": "苏州", "province": "江苏省"})
    print(f"  City: {result.get('city')}")
    print(f"  Success: {result.get('success')}")
    if result.get('success'):
        print(f"  Temp: {result.get('temp')}°C")
        print(f"  Condition: {result.get('condition')}")
        print(f"  Humidity: {result.get('humidity')}%")
        print(f"  Wind: {result.get('wind_level')}")
        print(f"  Forecast: {result.get('forecast')}")
    else:
        print(f"  Error: {result.get('error')}")

    # Test 2: Query weather for invalid city
    print("\n[Test 2] Query weather for invalid city...")
    result = run({"city": "无效城市 XYZ"})
    print(f"  Success: {result.get('success')}")
    print(f"  Error: {result.get('error')}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
