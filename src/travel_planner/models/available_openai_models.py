
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class OpenAIModels(BaseModel):
    gpt_4_1: ChatOpenAI
    gpt_4_1_mini: ChatOpenAI