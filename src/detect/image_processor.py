import hashlib
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image

from src.detect.config import detect_settings
from src.detect.models import BBox, ImageMetadata, Tile


class ImageProcessor:
    def __init__(self):
        self.uploads_dir = detect_settings.uploads_dir
        self.tile_size = detect_settings.tile_size
        self.tile_overlap = detect_settings.tile_overlap
        self.max_size_mb = detect_settings.max_image_size_mb
        self.allowed_extensions = detect_settings.allowed_extensions
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, file_path: Path) -> list[str]:
        errors = []
        if not file_path.exists():
            errors.append(f"Arquivo nao encontrado: {file_path}")
            return errors

        suffix = file_path.suffix.lower()
        if suffix not in self.allowed_extensions:
            errors.append(
                f"Extensao '{suffix}' nao permitida. Use: {self.allowed_extensions}"
            )

        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_size_mb:
            errors.append(
                f"Arquivo excede {self.max_size_mb}MB (tamanho: {size_mb:.1f}MB)"
            )

        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception:
            errors.append("Arquivo de imagem corrompido ou invalido")

        return errors

    def extract_metadata(self, file_path: Path) -> ImageMetadata:
        with Image.open(file_path) as img:
            width, height = img.size
            mode = img.mode

        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

        return ImageMetadata(
            filename=file_path.name,
            width=width,
            height=height,
            channels=len(mode),
            format=file_path.suffix.lower().strip("."),
            size_bytes=file_path.stat().st_size,
            hash_sha256=file_hash,
        )

    def generate_tiles(self, file_path: Path) -> list[Tile]:
        with Image.open(file_path) as img:
            width, height = img.size

        tiles = []
        step = int(self.tile_size * (1 - self.tile_overlap))  # 224 * 0.85 = 190
        tile_index = 0

        for y in range(0, height, step):
            for x in range(0, width, step):
                x_end = min(x + self.tile_size, width)
                y_end = min(y + self.tile_size, height)

                tiles.append(
                    Tile(
                        index=tile_index,
                        bbox=BBox(x=x, y=y, width=x_end - x, height=y_end - y),
                        file_path=file_path,
                    )
                )
                tile_index += 1

        return tiles

    def crop_detection(
        self,
        file_path: Path,
        bbox: BBox,
        output_dir: Optional[Path] = None,
    ) -> Path:
        output_dir = output_dir or detect_settings.results_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(file_path) as img:
            cropped = img.crop((
                bbox.x,
                bbox.y,
                bbox.x + bbox.width,
                bbox.y + bbox.height,
            ))
            output_path = output_dir / f"crop_{uuid.uuid4().hex[:12]}.png"
            cropped.save(output_path)

        return output_path

    async def save_upload(self, content: bytes, filename: str) -> Path:
        file_id = uuid.uuid4().hex[:12]
        safe_name = f"{file_id}_{filename}"
        dest = self.uploads_dir / safe_name
        dest.write_bytes(content)
        return dest
