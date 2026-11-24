from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BEAN_", extra="ignore")
    model_dir: Path = Path("artifacts/model")
    model_version: str = "1.0.0"
    not_sure_below: float = Field(0.80, ge=0, le=1)
    max_upload_bytes: int = Field(5 * 1024 * 1024, ge=1024, le=20 * 1024 * 1024)
    max_pixels: int = Field(16_000_000, ge=1)
    torch_threads: int = Field(2, ge=1, le=8)
    # Reserved for an optional private-model downloader; never sent in API responses.
    hf_token: SecretStr | None = Field(default=None, repr=False)
