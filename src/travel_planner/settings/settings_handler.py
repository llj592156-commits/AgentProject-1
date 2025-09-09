from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from travel_planner.helpers.general_utils import read_yaml


class OpenAISettings(BaseModel):
    large_model: str
    mini_model: str
    temperature: float = 0.0
    timeout: Optional[int] = Field(default=15, description="Timeout in seconds")


class AmadeusSettings(BaseModel):
    client_id: str
    client_secret: str
    base_url: str


class AppSettings(BaseModel):
    openai: OpenAISettings
    amadeus: AmadeusSettings

    @classmethod
    def read_from_yaml(cls) -> "AppSettings":
        """
        Loads YAML config and parses it into the AppSettings model.

        Args:
            yaml_path: Path to the settings.yaml file

        Returns:
            AppSettings instance with nested config
        """
        yaml_path = Path(__file__).parent / "yaml"
        return cls(
            openai=OpenAISettings(**read_yaml(yaml_path / "openai_settings.yaml")),
            amadeus=AmadeusSettings(**read_yaml(yaml_path / "amadeus_settings.yaml"))
        )
