from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    region: str = Field(default="eu-central-1", alias="AWS_REGION")


class ModelSettings(BaseSettings):
    model_id: str = Field(default="anthropic.claude-3-haiku-20240307-v1:0")
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.7)


class MemorySettings(BaseSettings):
    name: str = Field(default="AgentMemory")
    description: str = Field(default="Memory for agent conversations")
    event_expiry_days: int = Field(default=30)
    actor_id: str = Field(default="default_user")
    session_id: str = Field(default="session_001")


class Settings(BaseSettings):
    aws: AWSSettings = Field(default_factory=AWSSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )


settings = Settings()
