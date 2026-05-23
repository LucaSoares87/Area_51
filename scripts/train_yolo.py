"""Treina YOLOv8 para deteccao de telhados."""
from ultralytics import YOLO
from pathlib import Path

DATASET = Path("data/yolo/dataset.yaml")
EPOCHS = 150
IMG_SIZE = 640
BATCH = 8
MODEL_BASE = "yolov8n.pt"

def main():
    print(f"\n{'='*60}")
    print(f"  Treinamento YOLOv8 - Deteccao de Telhados")
    print(f"{'='*60}")
    print(f"  Modelo base:  {MODEL_BASE}")
    print(f"  Dataset:      {DATASET}")
    print(f"  Epocas:       {EPOCHS}")
    print(f"  Img size:     {IMG_SIZE}")
    print(f"  Batch:        {BATCH}")
    print(f"{'='*60}\n")

    model = YOLO(MODEL_BASE)

    results = model.train(
        data=str(DATASET),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH,
        name="telhados",
        project="runs",
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

    best = Path("runs/telhados/weights/best.pt")
    if best.exists():
        dest = Path("models/best.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(best, dest)
        print(f"\nModelo salvo em: {dest}")
    else:
        print(f"\nbest.pt nao encontrado em {best}")

    print(f"\nTreinamento concluido!")

if __name__ == "__main__":
    main()
