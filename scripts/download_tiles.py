"""Download de tiles de imagens aereas por coordenadas."""

import argparse
import math
import sys
import time
import urllib.request
from pathlib import Path


def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def download_tile(
    x: int,
    y: int,
    zoom: int,
    output_dir: Path,
    base_url: str,
) -> Path | None:
    url = base_url.format(z=zoom, x=x, y=y)
    filename = output_dir / f"tile_{zoom}_{x}_{y}.png"

    if filename.exists():
        return filename

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AerialHousingDetection/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            filename.write_bytes(response.read())
        return filename
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Download de tiles por coordenadas")
    parser.add_argument("--lat-min", type=float, required=True, help="Latitude minima")
    parser.add_argument("--lat-max", type=float, required=True, help="Latitude maxima")
    parser.add_argument("--lon-min", type=float, required=True, help="Longitude minima")
    parser.add_argument("--lon-max", type=float, required=True, help="Longitude maxima")
    parser.add_argument("--zoom", type=int, default=18, help="Nivel de zoom (padrao: 18)")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/uploads",
        help="Diretorio de saida",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        help="URL base do tile server",
    )
    parser.add_argument("--delay", type=float, default=0.5, help="Delay entre requests (s)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    x_min, y_min = lat_lon_to_tile(args.lat_max, args.lon_min, args.zoom)
    x_max, y_max = lat_lon_to_tile(args.lat_min, args.lon_max, args.zoom)

    total = (x_max - x_min + 1) * (y_max - y_min + 1)
    print(f"Area: ({args.lat_min}, {args.lon_min}) -> ({args.lat_max}, {args.lon_max})")
    print(f"Zoom: {args.zoom}")
    print(f"Tiles: {x_max - x_min + 1} x {y_max - y_min + 1} = {total}")

    if total > 500:
        print(f"Atencao: {total} tiles e um volume alto. Considere reduzir a area ou o zoom.")
        response = input("Continuar? (s/n): ")
        if response.lower() != "s":
            sys.exit(0)

    downloaded = 0
    errors = 0

    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            result = download_tile(x, y, args.zoom, output_dir, args.base_url)
            if result:
                downloaded += 1
            else:
                errors += 1

            progress = downloaded + errors
            print(f"  [{progress}/{total}] {'OK' if result else 'ERRO'} tile_{args.zoom}_{x}_{y}")
            time.sleep(args.delay)

    print(f"\nConcluido: {downloaded} baixados, {errors} erros")
    print(f"Diretorio: {output_dir}")


if __name__ == "__main__":
    main()
