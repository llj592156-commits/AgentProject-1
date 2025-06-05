from __future__ import annotations

from typing import Type, TypeVar
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompt_values import PromptValue
from langchain_core.messages import BaseMessage

from travel_planner.models.available_openai_models import OpenAIModels
from travel_planner.settings.settings_handler import OpenAISettings

T = TypeVar("T", bound=BaseModel)

async def invoke_llm_with_structured_output(
    prompt_value: PromptValue,
    response_model: Type[T],
    llm: ChatOpenAI,
    messages_history: list[BaseMessage] = []
) -> T:
    """
    Uses OpenAI function calling / JSON mode to parse directly into a Pydantic model.
    This requires LangChain >= 0.1.14+ which supports .with_structured_output().

    Args:
        chat_prompt_value: Rendered prompt to pass to the LLM.
        response_model:    The Pydantic model to parse into.
        llm:               A LangChain ChatOpenAI instance with JSON support.

    Returns:
        An instance of the response_model populated from the LLM.
    """
    structured_llm = llm.with_structured_output(response_model)
    messages = prompt_value.to_messages()
    system_message = messages[0]
    human_message = messages[1]
    
    input_messages: list[BaseMessage] = [system_message, *messages_history, human_message]
    
    return await structured_llm.ainvoke(input=input_messages) # type: ignore[return-value]


def create_models(settings: OpenAISettings, model_name: str) -> ChatOpenAI:
    """
    Instantiates a ChatOpenAI object using typed OpenAISettings.

    Args:
        settings: OpenAISettings object with model config.

    Returns:
        A configured ChatOpenAI instance.
    """
    return ChatOpenAI(
        model=model_name,
        temperature=settings.temperature,
        timeout=settings.timeout,
    )


def get_available_llm_models(settings: OpenAISettings) -> OpenAIModels:
    return OpenAIModels(
        gpt_4_1=create_models(settings, settings.large_model),
        gpt_4_1_mini=create_models(settings, settings.small_model),
    )
