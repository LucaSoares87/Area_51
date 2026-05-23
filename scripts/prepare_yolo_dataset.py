"""Organiza dataset YOLO: split train/val 80/20."""
import random
import shutil
from pathlib import Path

random.seed(42)

src_images = Path("data/yolo/images/train")
src_labels = Path("data/yolo/labels/train")

val_images = Path("data/yolo/images/val")
val_labels = Path("data/yolo/labels/val")

val_images.mkdir(parents=True, exist_ok=True)
val_labels.mkdir(parents=True, exist_ok=True)

# Pega apenas imagens que TEM anotação correspondente
annotated = []
for img in sorted(src_images.glob("*.png")):
    label = src_labels / f"{img.stem}.txt"
    if label.exists():
        annotated.append(img.stem)

if not annotated:
    print("Nenhuma imagem com anotação encontrada!")
    print(f"  Imagens em: {src_images}")
    print(f"  Labels em:  {src_labels}")
    raise SystemExit(1)

random.shuffle(annotated)
split = int(len(annotated) * 0.8)
train_set = annotated[:split]
val_set = annotated[split:]

# Move validação
moved = 0
for name in val_set:
    img_src = src_images / f"{name}.png"
    lbl_src = src_labels / f"{name}.txt"
    shutil.move(str(img_src), str(val_images / f"{name}.png"))
    shutil.move(str(lbl_src), str(val_labels / f"{name}.txt"))
    moved += 1

print("\n  Dataset organizado!")
print(f"  ├── train: {len(train_set)} imagens")
print(f"  └── val:   {len(val_set)} imagens")
print(f"\n  Total: {len(annotated)} imagens anotadas")
