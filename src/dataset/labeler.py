"""Ferramenta de rotulacao rapida de tiles via teclado."""

import shutil
from pathlib import Path

import cv2
import numpy as np

from src.detect.config import detect_settings

from .metadata import TileMetadata

LABEL_MAP = {
    ord("1"): "positives",
    ord("0"): "negatives",
    ord("2"): "uncertain",
}

WINDOW_NAME = "Area 51 - Tile Labeler"


class TileLabeler:
    """Classifica tiles manualmente com teclado e organiza no layout do bootstrap."""

    def __init__(
        self,
        tiles_dir: str | Path,
        bootstrap_dir: str | Path = "data/bootstrap",
        copy_files: bool = True,
    ) -> None:
        self.tiles_dir = Path(tiles_dir)
        self.bootstrap_dir = Path(bootstrap_dir)
        self.copy_files = copy_files
        self.metadata = TileMetadata(self.tiles_dir)

        for label in LABEL_MAP.values():
            (self.bootstrap_dir / label).mkdir(parents=True, exist_ok=True)

    def _get_unlabeled_tiles(self) -> list[Path]:
        records = self.metadata.load_csv()
        labeled = {record["tile_name"] for record in records if record.get("label")}

        tiles: list[Path] = []

        for extension in detect_settings.allowed_extensions:
            tiles.extend(self.tiles_dir.glob(f"tile_*{extension}"))

        return sorted(tile for tile in tiles if tile.name not in labeled)

    def _render_hud(
        self,
        img: np.ndarray,
        tile_name: str,
        idx: int,
        total: int,
    ) -> np.ndarray:
        display = img.copy()
        height, width = display.shape[:2]

        scale = max(1, 512 // max(height, width))

        if scale > 1:
            display = cv2.resize(
                display,
                (width * scale, height * scale),
                interpolation=cv2.INTER_NEAREST,
            )

        display_height, display_width = display.shape[:2]

        cv2.rectangle(
            display,
            (0, 0),
            (display_width, 36),
            (30, 30, 30),
            -1,
        )
        cv2.putText(
            display,
            f"[{idx + 1}/{total}] {tile_name}",
            (8, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.rectangle(
            display,
            (0, display_height - 32),
            (display_width, display_height),
            (30, 30, 30),
            -1,
        )
        cv2.putText(
            display,
            "1=POSITIVO  0=NEGATIVO  2=INCERTO  ESC=SAIR",
            (8, display_height - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (200, 200, 200),
            1,
        )

        return display

    def run(self, resume: bool = True) -> int:
        if resume:
            tiles = self._get_unlabeled_tiles()
        else:
            tiles = []

            for extension in detect_settings.allowed_extensions:
                tiles.extend(self.tiles_dir.glob(f"tile_*{extension}"))

            tiles = sorted(tiles)

        total = len(tiles)

        if total == 0:
            print("Todos os tiles ja foram rotulados.")
            return 0

        print(f"Tiles para rotular: {total}")
        print("1 = positivo (telhado) | 0 = negativo | 2 = incerto | ESC = sair\n")

        labeled_count = 0

        for index, tile_path in enumerate(tiles):
            image = cv2.imread(str(tile_path))

            if image is None:
                continue

            display = self._render_hud(image, tile_path.name, index, total)
            cv2.imshow(WINDOW_NAME, display)

            while True:
                key = cv2.waitKey(0) & 0xFF

                if key == 27:
                    print(f"\nSessao encerrada. {labeled_count} tiles rotulados.")
                    cv2.destroyAllWindows()
                    return labeled_count

                if key in LABEL_MAP:
                    label = LABEL_MAP[key]
                    self._apply_label(tile_path, label)
                    labeled_count += 1
                    print(f"{tile_path.name} -> {label}")
                    break

        cv2.destroyAllWindows()
        print(f"\nSessao completa. {labeled_count} tiles rotulados.")

        return labeled_count

    def _apply_label(self, tile_path: Path, label: str) -> None:
        destination = self.bootstrap_dir / label / tile_path.name

        if self.copy_files:
            shutil.copy2(tile_path, destination)
        else:
            shutil.move(str(tile_path), destination)

        self.metadata.update_label(tile_path.name, label)

    def stats(self) -> dict[str, int]:
        result = {}

        for label in LABEL_MAP.values():
            label_dir = self.bootstrap_dir / label
            count = len(list(label_dir.glob("*"))) if label_dir.exists() else 0
            result[label] = count

        result["total"] = sum(result.values())

        return result