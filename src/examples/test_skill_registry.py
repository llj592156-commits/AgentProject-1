"""Example: Testing SkillRegistry for dynamic skill discovery and loading.

This example demonstrates how to use the SkillRegistry to:
1. Discover skills from SKILL.md metadata files
2. List available skills (lightweight, no implementation loaded)
3. Load skill implementation on-demand (lazy loading)
4. Execute a skill
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import SkillRegistry from travel_planner.skills.skill_registry
from travel_planner.skills.skill_registry import SkillRegistry, get_skill_registry


def main():
    """Test SkillRegistry functionality."""
    print("=" * 50)
    print("SkillRegistry Test - Dynamic Skill Discovery")
    print("=" * 50)

    # Create registry and scan for skills
    registry = SkillRegistry()
    skill_ids = registry.scan()
    print(f"\nDiscovered skills: {skill_ids}")

    # List skill metadata (lightweight - no implementation loaded)
    print("\n--- Skill Metadata (no implementation loaded) ---")
    skills_meta = registry.list_skills()
    for skill in skills_meta:
        print(f"  - {skill['id']}: {skill['name']} ({skill['description']})")

    # Get single skill metadata
    print("\n--- Get weather skill metadata ---")
    meta = registry.get_skill_meta("skill_weather")
    if meta:
        print(f"  ID: {meta.id}")
        print(f"  Name: {meta.name}")
        print(f"  Description: {meta.description}")
        print(f"  Version: {meta.version}")
        print(f"  Tags: {meta.tags}")
        print(f"  Is Public: {meta.is_public}")

    # Load skill implementation on-demand (lazy loading)
    print("\n--- Load weather skill implementation ---")
    skill = registry.get_skill("skill_weather")
    if skill:
        print(f"  Loaded: {skill.metadata.name}")
        print(f"  Input Schema: {skill.input_schema}")
        print(f"  Output Schema: {skill.output_schema}")

        # Test skill execution
        print("\n--- Execute weather skill ---")
        result = skill.run_func({"city": "苏州", "province": "江苏省"})
        print(f"  Result success: {result.get('success', 'N/A')}")
        print(f"  Result data: city={result.get('city', 'N/A')}, temp={result.get('temp', 'N/A')}")

    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    main()
