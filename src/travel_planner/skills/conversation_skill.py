"""Conversation Skill - Handles general conversation and escalation.

Provides:
- Chitchat responses
- FAQ handling
- Escalation to human agents
"""

from travel_planner.skills.base_skill import BaseSkill, SkillContext, SkillResult


class ConversationSkill(BaseSkill):
    """Skill for handling general conversation."""

    @property
    def name(self) -> str:
        return "conversation"

    @property
    def description(self) -> str:
        return "Handle chitchat, FAQs, and escalation requests."

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the conversation skill."""
        self._log_execution("start", "Processing conversation")

        user_message = context.state.user_prompt.lower()

        # Check for escalation keywords
        # 有这些关键词就是升级
        escalation_keywords = ["agent", "human", "support", "help", "complaint", "manager"]
        if any(keyword in user_message for keyword in escalation_keywords):
            self._log_execution("escalation", "User requested human assistance")
            return SkillResult.ok(
                message="Your request has been escalated to a human agent.",
                state_updates={"escalated": True},
            )

        # General chitchat - LLM will handle this
        self._log_execution("chitchat", "Generating chitchat response")
        return SkillResult.ok(
            message="chitchat",  # Signal to LLM node to generate response
            state_updates={},
        )

    async def can_execute(self, context: SkillContext) -> bool:
        """Always can execute - handles any message."""
        return True
