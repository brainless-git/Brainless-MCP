"""Configuration via environment variables / .env files."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env files in priority order
for _candidate in [
    Path.home() / ".brainless-mcp" / ".env.local",
    Path.home() / ".brainless-mcp" / ".env",
    Path(".env.local"),
    Path(".env"),
]:
    if _candidate.exists():
        load_dotenv(_candidate, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Unraid connection
    unraid_api_url: str = "https://tower.local"
    unraid_api_key: str = ""
    unraid_verify_ssl: str = "false"  # "true", "false", or path to CA bundle

    # MCP server auth
    brainless_mcp_bearer_token: str = ""

    # Transport
    brainless_mcp_transport: str = "stdio"
    brainless_mcp_port: int = 8000

    # Logging
    brainless_mcp_log_level: str = "INFO"
    brainless_mcp_log_file: str = ""

    # Subscriptions
    unraid_auto_start_subscriptions: bool = False
    unraid_max_reconnect_attempts: int = 10

    # Timeouts (seconds)
    request_timeout: int = 30
    disk_op_timeout: int = 90

    @field_validator("unraid_verify_ssl", mode="before")
    @classmethod
    def normalise_ssl(cls, v: str) -> str:
        return str(v)

    @property
    def ssl_verify(self) -> bool | str:
        low = self.unraid_verify_ssl.lower()
        if low in ("true", "1", "yes"):
            return True
        if low in ("false", "0", "no"):
            return False
        return self.unraid_verify_ssl  # treat as CA bundle path

    @property
    def graphql_url(self) -> str:
        base = self.unraid_api_url.rstrip("/")
        return f"{base}/graphql"

    @property
    def ws_url(self) -> str:
        base = self.unraid_api_url.rstrip("/")
        ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
        return f"{ws_base}/graphql"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
