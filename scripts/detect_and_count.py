"""Detecta e conta telhados em tiles usando o modelo treinado."""
import sys
from pathlib import Path

from ultralytics import YOLO

MODEL_PATH = Path("models/best.pt")
SOURCE = Path("data/raw")
CONFIDENCE = 0.5

def main():
    if not MODEL_PATH.exists():
        print(f"   Modelo não encontrado: {MODEL_PATH}")
        print("  Execute primeiro: python scripts/train_yolo.py")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  Detecção de Telhados")
    print(f"{'='*60}")
    print(f"  Modelo:     {MODEL_PATH}")
    print(f"  Source:     {SOURCE}")
    print(f"  Confiança:  {CONFIDENCE}")
    print(f"{'='*60}\n")

    model = YOLO(str(MODEL_PATH))

    results = model.predict(
        source=str(SOURCE),
        conf=CONFIDENCE,
        save=True,
        save_txt=True,
        project="results",
        name="detections",
        exist_ok=True,
    )

    print(f"\n{'='*60}")
    print("  RESULTADOS")
    print(f"{'='*60}\n")

    total = 0
    for r in results:
        n = len(r.boxes)
        total += n
        name = Path(r.path).name
        bar = "█" * n
        print(f"  {name:30s} | {n:3d} telhado(s) {bar}")

    print(f"\n{'='*60}")
    print(f"   TOTAL: {total} telhados detectados")
    print(f"{'='*60}")
    print("\n  Imagens salvas em: results/detections/\n")

if __name__ == "__main__":
    main()
