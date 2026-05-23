"""Anotação de bounding boxes simples via terminal.
Abre a imagem no Windows e pede coordenadas no terminal.
Para uso futuro - recomendamos LabelImg para anotação visual.
"""
import shutil
import subprocess
import sys
from pathlib import Path

positives_dir = Path("data/bootstrap/positives")
images_out = Path("data/yolo/images/train")
labels_out = Path("data/yolo/labels/train")

images_out.mkdir(parents=True, exist_ok=True)
labels_out.mkdir(parents=True, exist_ok=True)

tiles = sorted(positives_dir.glob("*.png"))
total = len(tiles)

if total == 0:
    print("Nenhum tile positivo encontrado em data/bootstrap/positives/")
    sys.exit(0)

print(f"\n{'='*60}")
print(f"  Anotação de Bounding Boxes")
print(f"  Tiles positivos: {total}")
print(f"{'='*60}")
print(f"\n  RECOMENDAÇÃO: Use o LabelImg para anotar visualmente!")
print(f"  Instale com: pip install labelimg")
print(f"  Rode com:    labelimg data/bootstrap/positives/")
print(f"\n  Este script apenas copia as imagens para a pasta YOLO.")
print(f"  As anotações (.txt) devem ser feitas no LabelImg.\n")

resp = input("  Copiar imagens positivas para data/yolo/images/train? (s/n): ").strip()

if resp.lower() == 's':
    count = 0
    for tile in tiles:
        dest = images_out / tile.name
        shutil.copy2(tile, dest)
        count += 1
    print(f"\n  {count} imagens copiadas para {images_out}/")
    print(f"  Agora anote com LabelImg e salve os .txt em {labels_out}/")
else:
    print("  Cancelado.")
