from __future__ import annotations

from typing import TypeVar, cast

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.prompt_values import PromptValue
from langchain_community.chat_models.tongyi import ChatTongyi
from pydantic import BaseModel

from travel_planner.models.available_llm_models import LLMs
from travel_planner.settings.settings_handler import OpenAISettings

T = TypeVar("T", bound=BaseModel)

#异步调用LLM模型
async def invoke_llm(
    prompt_value: PromptValue,
    llm: ChatTongyi,
    response_model: type[T] | None = None,
    messages_history: list[BaseMessage] | None = None,
) -> T | BaseMessage | AIMessage:
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
    messages = prompt_value.to_messages()
    system_message = messages[0]
    human_message = messages[1]
    if messages_history is None:
        messages_history = []
    input_messages: list[BaseMessage] = [system_message, *messages_history, human_message]
    if response_model is not None:
        structured_llm = llm.with_structured_output(response_model) # 创建一个结构化输出的LLM模型
        result = await structured_llm.ainvoke(input=input_messages) #异步调用的结构化输出的LLM模型
        return cast(T, result) #这个cast纯粹是为了开发体验和代码静态检查。
    else:
        result = await llm.ainvoke(input=input_messages)
        return result

#创建LLM模型
def _create_models(settings: OpenAISettings, model_name: str) -> ChatTongyi:
    """
    Instantiates a ChatTongyi object using typed OpenAISettings.

    Args:
        settings: OpenAISettings object with model config.

    Returns:
        A configured ChatTongyi instance.
    """
    return ChatTongyi(
        model=model_name,
        temperature=settings.temperature,
        timeout=settings.timeout,
    )

#获取可用的LLM模型
def get_available_llms(settings: OpenAISettings) -> LLMs:
    return LLMs(
        large_model=_create_models(settings, settings.large_model),
        mini_model=_create_models(settings, settings.mini_model),
    )
