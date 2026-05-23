from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings for the aerial housing detection system."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="aerial_housing_detection")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    data_dir: Path = Field(default=Path("data"))
    raw_data_dir: Path = Field(default=Path("data/raw"))
    processed_data_dir: Path = Field(default=Path("data/processed"))
    output_data_dir: Path = Field(default=Path("data/outputs"))

    reports_dir: Path = Field(default=Path("reports"))
    models_dir: Path = Field(default=Path("models"))

    max_image_size_mb: int = Field(default=50)
    allowed_image_extensions: tuple[str, ...] = Field(default=(".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"))

    default_confidence_score: float = Field(default=0.65)
    min_roof_area_px: int = Field(default=120)
    max_roof_area_px: int = Field(default=2_000_000)

    csv_delimiter: str = Field(default=",")
    html_map_filename_suffix: str = Field(default="_map.html")
    csv_report_filename_suffix: str = Field(default="_report.csv")

    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=False)

    def ensure_directories(self) -> None:
        """Create required runtime directories when they do not exist."""
        directories = (
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.output_data_dir,
            self.reports_dir,
            self.models_dir,
        )

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> AppSettings:
    """Return cached application settings."""
    settings = AppSettings()
    settings.ensure_directories()
    return settings
