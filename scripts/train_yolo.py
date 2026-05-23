"""Treina YOLOv8 para deteccao de telhados."""

import shutil
from pathlib import Path

from ultralytics import YOLO

DATASET = Path("data/yolo/dataset.yaml")
EPOCHS = 150
IMG_SIZE = 640
BATCH = 8
MODEL_BASE = "yolov8n.pt"
PROJECT_DIR = Path("runs")
RUN_NAME = "telhados"
BEST_MODEL_SOURCE = PROJECT_DIR / RUN_NAME / "weights" / "best.pt"
BEST_MODEL_DESTINATION = Path("models/best.pt")


def validate_paths() -> None:
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset nao encontrado: {DATASET}")

    if not Path(MODEL_BASE).exists():
        raise FileNotFoundError(f"Modelo base nao encontrado: {MODEL_BASE}")


def print_training_summary() -> None:
    separator = "=" * 60

    print(f"\n{separator}")
    print("Treinamento YOLOv8 - Deteccao de Telhados")
    print(separator)
    print(f"Modelo base:  {MODEL_BASE}")
    print(f"Dataset:      {DATASET}")
    print(f"Epocas:       {EPOCHS}")
    print(f"Img size:     {IMG_SIZE}")
    print(f"Batch:        {BATCH}")
    print(f"Projeto:      {PROJECT_DIR}")
    print(f"Execucao:     {RUN_NAME}")
    print(f"{separator}\n")


def copy_best_model() -> None:
    if not BEST_MODEL_SOURCE.exists():
        print(f"\nbest.pt nao encontrado em {BEST_MODEL_SOURCE}")
        return

    BEST_MODEL_DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BEST_MODEL_SOURCE, BEST_MODEL_DESTINATION)

    print(f"\nModelo salvo em: {BEST_MODEL_DESTINATION}")


def train_model() -> None:
    model = YOLO(MODEL_BASE)

    model.train(
        data=str(DATASET),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH,
        name=RUN_NAME,
        project=str(PROJECT_DIR),
        patience=30,
        augment=True,
        verbose=True,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.3,
        scale=0.5,
        translate=0.2,
        degrees=15.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        perspective=0.001,
        erasing=0.1,
        weight_decay=0.001,
        dropout=0.15,
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=5,
        cos_lr=True,
        val=True,
        plots=True,
    )


def main() -> None:
    validate_paths()
    print_training_summary()
    train_model()
    copy_best_model()

    print("\nTreinamento concluido!")


if __name__ == "__main__":
    main()