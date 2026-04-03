#ok
from langchain_community.chat_models.tongyi import ChatTongyi
from pydantic import BaseModel


class LLMs(BaseModel):
    large_model: ChatTongyi
    mini_model: ChatTongyi
