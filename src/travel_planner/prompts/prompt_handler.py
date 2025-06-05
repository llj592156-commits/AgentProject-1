from pathlib import Path
from typing import Any

from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from travel_planner.helpers.general_utils import read_yaml


def read_yaml_and_parse_chat_prompt(yaml_path: Path) -> ChatPromptTemplate:
    """
    Reads a YAML file with 'system' and 'user' fields and converts them to a ChatPromptTemplate.
    """

    prompt_dict = read_yaml(yaml_path)
    system_prompt = SystemMessagePromptTemplate.from_template(prompt_dict["system_prompt"], template_format="jinja2")
    user_prompt = HumanMessagePromptTemplate.from_template(prompt_dict["user_prompt"], template_format="jinja2")

    return ChatPromptTemplate(messages=[system_prompt, user_prompt], template_format="jinja2")


class PromptTemplates(BaseModel):
    amadeus_hotel_search: ChatPromptTemplate

    @classmethod
    def read_from_yaml(cls) -> "PromptTemplates":
        yaml_dir = Path(__file__).parent / "yaml"
        return cls(
            amadeus_hotel_search=read_yaml_and_parse_chat_prompt(
                yaml_dir / "amadeus_hotel_search_params.yaml"
            )
        )