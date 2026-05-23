"""
Auditoria de rotulacao — revisao por amostragem.

Seleciona tiles aleatorios ja rotulados e mostra para
re-confirmacao humana. Detecta inconsistencias.

Uso:
    python -m scripts.audit_labels --sample 20
    python -m scripts.audit_labels --sample 30 --class positives
    python -m scripts.audit_labels --seed 42 --sample 15
"""

import argparse
import random
import sys
from pathlib import Path

import cv2

from src.detect.config import detect_settings


WINDOW_NAME = "Area 51 - Auditoria"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auditoria de rotulacao — Identificacao Aerea",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bootstrap-dir",
        type=str,
        default="data/bootstrap",
        help="Diretorio base do bootstrap",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=20,
        help="Quantidade de tiles para auditar",
    )
    parser.add_argument(
        "--class",
        dest="target_class",
        type=str,
        choices=["positives", "negatives", "uncertain"],
        default=None,
        help="Auditar apenas uma classe especifica",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed para reproducibilidade da amostragem",
    )
    return parser.parse_args()


def collect_labeled_tiles(
    bootstrap_dir: Path,
    target_class: str | None,
) -> list[tuple[Path, str]]:
    """Coleta tiles rotulados com seu label atual."""
    classes = (
        [target_class] if target_class
        else ["positives", "negatives", "uncertain"]
    )
    tiles = []

    for cls in classes:
        cls_dir = bootstrap_dir / cls
        if not cls_dir.exists():
            continue
        for ext in detect_settings.allowed_extensions:
            for f in cls_dir.glob(f"*{ext}"):
                tiles.append((f, cls))

    return tiles


def render_display(
    img, tile_path: Path, current_label: str, idx: int, total: int,
):
    """Monta a visualizacao com HUD superior e inferior."""
    h, w = img.shape[:2]
    scale = max(1, 512 // max(h, w))
    if scale > 1:
        display = cv2.resize(
            img, (w * scale, h * scale),
            interpolation=cv2.INTER_NEAREST,
        )
    else:
        display = img.copy()

    dh, dw = display.shape[:2]

    # HUD superior
    cv2.rectangle(display, (0, 0), (dw, 40), (30, 30, 30), -1)
    cv2.putText(
        display,
        f"[{idx + 1}/{total}] {tile_path.name}  |  LABEL: {current_label.upper()}",
        (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1,
    )

    # HUD inferior
    cv2.rectangle(display, (0, dh - 30), (dw, dh), (30, 30, 30), -1)
    cv2.putText(
        display, "ENTER=ok  1=pos  0=neg  2=incerto  ESC=sair",
        (8, dh - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1,
    )

    return display


def print_report(
    correct: int, wrong: int, corrections: list[dict], reviewed: int,
):
    """Imprime relatorio final da auditoria."""
    print("\n" + "=" * 60)
    print("  RELATORIO DE AUDITORIA")
    print("=" * 60)

    accuracy = (correct / reviewed * 100) if reviewed > 0 else 0

    print(f"\n  Revisados:    {reviewed}")
    print(f"  Corretos:     {correct}")
    print(f"  Incorretos:   {wrong}")
    print(f"  Acuracia:     {accuracy:.1f}%")

    if accuracy >= 95:
        print(f"\n  ✓ Qualidade EXCELENTE. Dataset confiavel.")
    elif accuracy >= 85:
        print(f"\n  ⚠ Qualidade ACEITAVEL. Revise os erros abaixo.")
    else:
        print(f"\n  ✗ Qualidade INSUFICIENTE. Re-rotule o dataset.")

    if corrections:
        print(f"\n  Correcoes necessarias:")
        for c in corrections:
            print(f"    {c['file']}: {c['was']} → {c['should_be']}")

        print(f"\n  Para corrigir manualmente:")
        for c in corrections:
            src = c["path"]
            dest = src.replace(f"/{c['was']}/", f"/{c['should_be']}/")
            print(f"    mv {src} {dest}")

    print("=" * 60)


def main() -> None:
    args = parse_args()
    bootstrap_dir = Path(args.bootstrap_dir)

    all_tiles = collect_labeled_tiles(bootstrap_dir, args.target_class)

    if not all_tiles:
        print("Nenhum tile rotulado encontrado.")
        sys.exit(1)

    if args.seed is not None:
        random.seed(args.seed)

    sample_size = min(args.sample, len(all_tiles))
    sample = random.sample(all_tiles, sample_size)

    print("=" * 60)
    print("  Identificacao Aerea — Auditoria de Rotulacao")
    print("=" * 60)
    print(f"\n  Total rotulados: {len(all_tiles)}")
    print(f"  Amostra:         {sample_size}")
    if args.target_class:
        print(f"  Classe filtrada: {args.target_class}")
    if args.seed is not None:
        print(f"  Seed:            {args.seed}")
    print(f"\n  Instrucoes:")
    print(f"    ENTER = confirma label atual (correto)")
    print(f"    1     = deveria ser POSITIVO")
    print(f"    0     = deveria ser NEGATIVO")
    print(f"    2     = deveria ser INCERTO")
    print(f"    ESC   = encerrar auditoria")
    print("-" * 60)

    correct = 0
    wrong = 0
    corrections: list[dict] = []

    remap = {
        ord("1"): "positives",
        ord("0"): "negatives",
        ord("2"): "uncertain",
    }

    for i, (tile_path, current_label) in enumerate(sample):
        img = cv2.imread(str(tile_path))
        if img is None:
            print(f"  {tile_path.name}: nao foi possivel ler, pulando...")
            continue

        display = render_display(img, tile_path, current_label, i, sample_size)
        cv2.imshow(WINDOW_NAME, display)

        while True:
            key = cv2.waitKey(0) & 0xFF

            if key == 27:  # ESC
                print(f"\n  Auditoria encerrada na amostra {i + 1}.")
                cv2.destroyAllWindows()
                print_report(correct, wrong, corrections, correct + wrong)
                return

            if key in (13, 10):  # ENTER
                correct += 1
                print(f"  {tile_path.name}: {current_label} ✓")
                break

            if key in remap:
                new_label = remap[key]
                if new_label == current_label:
                    correct += 1
                    print(f"  {tile_path.name}: {current_label} ✓")
                else:
                    wrong += 1
                    corrections.append({
                        "file": tile_path.name,
                        "was": current_label,
                        "should_be": new_label,
                        "path": str(tile_path),
                    })
                    print(f"  {tile_path.name}: {current_label} ✗ → {new_label}")
                break

    cv2.destroyAllWindows()
    print_report(correct, wrong, corrections, correct + wrong)


if __name__ == "__main__":
    main()
