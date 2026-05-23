from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class DetectSettings(BaseSettings):
    """Configurações do pipeline de detecção aérea."""

    model_config = SettingsConfigDict(
        env_prefix="DETECT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Modelos ---
    bootstrap_model_path: str = "models/bootstrap/model.pth"
    spacenet_model_path: str = "models/spacenet/model.pth"

    # --- Tiling ---
    tile_size: int = 224
    tile_overlap: float = 0.15

    # --- Inferência ---
    confidence_threshold: float = 0.5
    nms_iou_threshold: float = 0.45
    mock_inference: bool = False
    max_detections_per_image: int = 500
    batch_size: int = 16

    # --- Dados e extensões ---
    allowed_extensions: set[str] = {
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp",
    }
    max_image_size_mb: float = 50.0

    # --- Device ---
    force_cpu: bool = False

    # --- Caminhos ---
    output_dir: str = "outputs/detections"
    metrics_dir: str = "models/bootstrap"
    uploads_dir: Path = Path("data/uploads")
    results_dir: Path = Path("data/results")

    # --- Cross Reference ---
    cross_reference_enabled: bool = False
    cross_reference_api_url: str = ""
    cross_reference_timeout_seconds: float = 10.0

    # --- Batch ---
    batch_max_images: int = 20

    @property
    def model_path_resolved(self) -> Path:
        """Retorna o caminho do modelo bootstrap como Path resolvido."""
        return Path(self.bootstrap_model_path).resolve()

    @property
    def spacenet_model_path_resolved(self) -> Path:
        """Retorna o caminho do modelo SpaceNet como Path resolvido."""
        return Path(self.spacenet_model_path).resolve()

    @property
    def output_path_resolved(self) -> Path:
        """Retorna o diretório de saída como Path resolvido."""
        path = Path(self.output_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve()

    @property
    def metrics_path_resolved(self) -> Path:
        """Retorna o diretório de métricas como Path resolvido."""
        path = Path(self.metrics_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve()


detect_settings = DetectSettings()
