
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class LLMs(BaseModel):
    large_model: ChatOpenAI
    mini_model: ChatOpenAI
