"""
Tileamento de imagens aereas para construcao de dataset.

Uso:
    python -m scripts.tile_image data/raw/mapa.png
    python -m scripts.tile_image data/raw/ --tile-size 512 --overlap 0.25
    python -m scripts.tile_image data/raw/area.png --output data/bootstrap/tiles
"""

import argparse
import sys
import time
from pathlib import Path

from src.dataset import ImageTiler
from src.detect.config import detect_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tilear imagens aereas — Identificacao Aerea",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=str,
        help="Caminho da imagem ou diretorio com imagens",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/bootstrap/tiles",
        help="Diretorio de saida dos tiles",
    )
    parser.add_argument(
        "--tile-size",
        type=int,
        default=detect_settings.tile_size,
        help="Tamanho do tile em pixels",
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=detect_settings.tile_overlap,
        help="Overlap entre tiles (0.0 a 0.9)",
    )
    parser.add_argument(
        "--min-content",
        type=float,
        default=0.1,
        help="Ratio minimo de conteudo para manter tile",
    )
    return parser.parse_args()


def collect_images(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        images = []
        for ext in detect_settings.allowed_extensions:
            images.extend(input_path.glob(f"*{ext}"))
        return sorted(images)
    return []


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    images = collect_images(input_path)
    if not images:
        print(f"Nenhuma imagem encontrada em: {input_path}")
        sys.exit(1)

    tiler = ImageTiler(
        tile_size=args.tile_size,
        overlap=args.overlap,
        min_content_ratio=args.min_content,
    )

    output_dir = Path(args.output)

    print("=" * 60)
    print("  Identificacao Aerea — Tileamento de Imagens")
    print("=" * 60)
    print(f"\nTile size:    {tiler.tile_size}x{tiler.tile_size}")
    print(f"Overlap:      {int(tiler.overlap * 100)}%")
    print(f"Stride:       {tiler.stride}px")
    print(f"Min content:  {int(args.min_content * 100)}%")
    print(f"Output:       {output_dir}")
    print(f"Imagens:      {len(images)}")
    print("-" * 60)

    total_tiles = 0
    total_skipped = 0

    for img_path in images:
        print(f"\nProcessando: {img_path.name}")
        t0 = time.perf_counter()

        try:
            stats = tiler.process(img_path, output_dir)
            elapsed = time.perf_counter() - t0

            print(
                f"  {stats['total_tiles']} tiles | "
                f"{stats['skipped_empty']} descartados | "
                f"{elapsed:.2f}s | "
                f"{stats['source_resolution']}"
            )

            total_tiles += stats["total_tiles"]
            total_skipped += stats["skipped_empty"]

        except Exception as e:
            print(f"  ERRO: {e}")

    print("-" * 60)
    print(f"Total: {total_tiles} tiles gerados, {total_skipped} descartados")
    print(f"Salvos em: {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
