"""
Rotulacao rapida de tiles via teclado.

Uso:
    python -m scripts.label_tiles data/bootstrap/tiles/mapa_piedade
    python -m scripts.label_tiles data/bootstrap/tiles/mapa_piedade --move
    python -m scripts.label_tiles data/bootstrap/tiles/mapa_piedade --stats
"""

import argparse
import sys
from pathlib import Path

from src.dataset import TileLabeler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rotulacao rapida de tiles — Identificacao Aerea",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "tiles_dir",
        type=str,
        help="Diretorio com tiles para rotular",
    )
    parser.add_argument(
        "--bootstrap-dir",
        type=str,
        default="data/bootstrap",
        help="Diretorio base do dataset bootstrap",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Mover tiles em vez de copiar",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Mostrar todos os tiles (inclusive ja rotulados)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Mostrar estatisticas e sair",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tiles_dir = Path(args.tiles_dir)

    if not tiles_dir.exists():
        print(f"Diretorio nao encontrado: {tiles_dir}")
        sys.exit(1)

    labeler = TileLabeler(
        tiles_dir=tiles_dir,
        bootstrap_dir=Path(args.bootstrap_dir),
        copy_files=not args.move,
    )

    if args.stats:
        stats = labeler.stats()
        print("=" * 60)
        print("  Identificacao Aerea — Estatisticas de Rotulacao")
        print("=" * 60)
        for label, count in stats.items():
            if label != "total":
                print(f"  {label:12s} {count}")
        print(f"  {'total':12s} {stats['total']}")
        print("=" * 60)
        return

    print("=" * 60)
    print("  Identificacao Aerea — Rotulacao de Tiles")
    print("=" * 60)
    print(f"\nTiles:      {tiles_dir}")
    print(f"Bootstrap:  {args.bootstrap_dir}")
    print(f"Modo:       {'MOVER' if args.move else 'COPIAR'}")
    print("-" * 60)

    labeled = labeler.run(resume=not args.all)

    if labeled > 0:
        stats = labeler.stats()
        print(f"\nResultado final:")
        print(f"  positives:  {stats.get('positives', 0)}")
        print(f"  negatives:  {stats.get('negatives', 0)}")
        print(f"  uncertain:  {stats.get('uncertain', 0)}")
        print(f"  total:      {stats['total']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
