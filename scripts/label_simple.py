"""Rotulacao simples - abre imagem no Windows e pergunta no terminal."""
import shutil
import subprocess
import sys
from pathlib import Path

tiles_dir = Path("data/raw")
bootstrap = Path("data/bootstrap")

for d in ["positives", "negatives", "uncertain"]:
    (bootstrap / d).mkdir(parents=True, exist_ok=True)

already = set()
for d in ["positives", "negatives", "uncertain"]:
    for f in (bootstrap / d).glob("*.png"):
        already.add(f.name)

tiles = sorted([t for t in tiles_dir.glob("*.png") if t.name not in already])
total = len(tiles)

if total == 0:
    print("Nenhum tile para rotular!")
    sys.exit(0)

print(f"\n  Tiles para rotular: {total}")
print(f"  1 = positivo | 0 = negativo | 2 = incerto | q = sair\n")

count = 0
for i, tile in enumerate(tiles):
    win_path = subprocess.run(
        ["wslpath", "-w", str(tile)], capture_output=True, text=True
    ).stdout.strip()
    proc = subprocess.Popen(
        ["cmd.exe", "/C", "start", "", win_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    label = input(f"  [{i+1}/{total}] {tile.name} -> (1/0/2/q): ").strip()

    if label == "q":
        break
    elif label == "1":
        dest = bootstrap / "positives" / tile.name
    elif label == "0":
        dest = bootstrap / "negatives" / tile.name
    elif label == "2":
        dest = bootstrap / "uncertain" / tile.name
    else:
        print("    Invalido, pulando...")
        continue

    shutil.copy2(tile, dest)
    count += 1
    print(f"    -> {dest.parent.name}/")

print(f"\n  Rotulados: {count}")
