from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    region: str = Field(default="eu-central-1")


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


class CognitoSettings(BaseSettings):
    user_pool_id: str | None = Field(default=None)
    client_id: str | None = Field(default=None)
    client_secret: str | None = Field(default=None)
    domain: str | None = Field(default=None)


class GatewaySettings(BaseSettings):
    gateway_id: str | None = Field(default=None)
    gateway_url: str | None = Field(default=None)
    name: str = Field(default="AgentGateway")
    enable_semantic_search: bool = Field(default=True)
    lambda_target_name: str = Field(default="AgentTools")


class LambdaSettings(BaseSettings):
    function_name: str = Field(default="agentcore-gateway-tools")
    role_name: str = Field(default="AgentCoreGatewayLambdaRole")
    timeout: int = Field(default=30)
    memory_size: int = Field(default=256)


class BrowserSettings(BaseSettings):
    name: str = Field(default="AgentBrowser")
    description: str = Field(default="AgentCore Browser for web interactions")


class S3Settings(BaseSettings):
    documents_bucket: str = Field(default="model-optimized-bucket")


class Settings(BaseSettings):
    aws: AWSSettings = Field(default_factory=AWSSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    cognito: CognitoSettings = Field(default_factory=CognitoSettings)
    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    lambda_settings: LambdaSettings = Field(default_factory=LambdaSettings)
    browser_tool: BrowserSettings = Field(default_factory=BrowserSettings)
    s3: S3Settings = Field(default_factory=S3Settings)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )


settings = Settings()
