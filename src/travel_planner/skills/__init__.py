"""Capability Layer - Encapsulates domain-specific capabilities.

This module provides skills that combine tools to achieve higher-level goals:
- PlanningSkill: Create travel itineraries
- BookingSkill: Reserve flights, hotels, cars
- InfoSkill: Gather information (weather, visa, etc.)
- ConversationSkill: Handle chitchat and escalation
"""

from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult
from travel_planner.skills.planning_skill import PlanningSkill
from travel_planner.skills.booking_skill import BookingSkill
from travel_planner.skills.info_skill import InfoSkill
from travel_planner.skills.conversation_skill import ConversationSkill

__all__ = [
    "BaseSkill",
    "SkillContext",
    "SkillResult",
    "PlanningSkill",
    "BookingSkill",
    "InfoSkill",
    "ConversationSkill",
]
