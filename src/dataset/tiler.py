"""Motor de tileamento de imagens aéreas com rastreabilidade."""

import json
import cv2
import numpy as np
from pathlib import Path

from src.detect.config import detect_settings
from .metadata import TileMetadata, TileRecord


class ImageTiler:
    """Divide imagens aéreas em tiles padronizados para construção de dataset."""

    def __init__(
        self,
        tile_size: int | None = None,
        overlap: float | None = None,
        min_content_ratio: float = 0.1,
        output_format: str = "png",
    ):
        self.tile_size = tile_size or detect_settings.tile_size
        self.overlap = overlap if overlap is not None else detect_settings.tile_overlap
        self.min_content_ratio = min_content_ratio
        self.output_format = output_format

        assert 0.0 <= self.overlap < 1.0, "overlap deve ser [0.0, 1.0)"
        assert self.tile_size > 0, "tile_size deve ser positivo"

    @property
    def stride(self) -> int:
        return max(1, int(self.tile_size * (1.0 - self.overlap)))

    def process(self, image_path: str | Path, output_dir: str | Path) -> dict:
        image_path = Path(image_path)
        output_dir = Path(output_dir)

        self._validate_input(image_path)

        tiles_dir = output_dir / image_path.stem
        tiles_dir.mkdir(parents=True, exist_ok=True)

        img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Nao foi possivel ler: {image_path}")

        h, w = img.shape[:2]
        metadata = TileMetadata(tiles_dir)

        stats = {
            "source": image_path.name,
            "source_resolution": f"{w}x{h}",
            "tile_size": self.tile_size,
            "overlap": self.overlap,
            "stride": self.stride,
            "total_tiles": 0,
            "skipped_empty": 0,
        }

        for y in range(0, h, self.stride):
            for x in range(0, w, self.stride):
                tile = self._extract_tile(img, x, y, h, w)

                if self._is_empty(tile):
                    stats["skipped_empty"] += 1
                    continue

                tile_name = f"tile_x{x:05d}_y{y:05d}.{self.output_format}"
                cv2.imwrite(str(tiles_dir / tile_name), tile)

                metadata.add(TileRecord(
                    tile_name=tile_name,
                    source_image=image_path.name,
                    x=x,
                    y=y,
                    tile_size=self.tile_size,
                    overlap=int(self.overlap * 100),
                    timestamp=TileMetadata.now_iso(),
                ))

                stats["total_tiles"] += 1

        metadata.flush()
        self._save_config(tiles_dir, stats)
        return stats

    def _validate_input(self, image_path: Path):
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem nao encontrada: {image_path}")

        if image_path.suffix.lower() not in detect_settings.allowed_extensions:
            raise ValueError(
                f"Extensao '{image_path.suffix}' nao permitida. "
                f"Aceitas: {detect_settings.allowed_extensions}"
            )

        size_mb = image_path.stat().st_size / (1024 * 1024)
        if size_mb > detect_settings.max_image_size_mb:
            raise ValueError(
                f"Imagem ({size_mb:.1f}MB) excede limite de "
                f"{detect_settings.max_image_size_mb}MB"
            )

    def _extract_tile(
        self, img: np.ndarray, x: int, y: int, h: int, w: int,
    ) -> np.ndarray:
        y_end = min(y + self.tile_size, h)
        x_end = min(x + self.tile_size, w)
        tile = img[y:y_end, x:x_end]

        th, tw = tile.shape[:2]
        if th < self.tile_size or tw < self.tile_size:
            padded = np.zeros((self.tile_size, self.tile_size, 3), dtype=np.uint8)
            padded[:th, :tw] = tile
            return padded

        return tile

    def _is_empty(self, tile: np.ndarray) -> bool:
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        non_zero = np.count_nonzero(gray)
        total = gray.shape[0] * gray.shape[1]
        return (non_zero / total) < self.min_content_ratio

    @staticmethod
    def _save_config(tiles_dir: Path, stats: dict):
        config_path = tiles_dir / "tiling_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)


def reconstruct_positions(tiles_dir: str | Path) -> list[dict]:
    """Reconstrói posições globais dos tiles para inferência futura."""
    tiles_dir = Path(tiles_dir)
    meta = TileMetadata(tiles_dir)

    return [
        {
            "tile": rec["tile_name"],
            "source": rec["source_image"],
            "bbox": {
                "x": int(rec["x"]),
                "y": int(rec["y"]),
                "w": int(rec["tile_size"]),
                "h": int(rec["tile_size"]),
            },
            "label": rec.get("label"),
        }
        for rec in meta.load_csv()
    ]
