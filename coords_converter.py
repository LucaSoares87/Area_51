"""
Conversor de Coordenadas + Download automático de tiles.
Projeto: Identificação Aérea

Uso:
    python coords_converter.py

Cola direto do Google Earth no formato:
    8°06'49.86"S 34°56'46.11"W
"""

import re
import sys
import math
import subprocess


def dms_to_decimal(dms_string: str) -> float:
    """Converte UMA coordenada DMS para decimal."""
    try:
        return float(dms_string.strip())
    except ValueError:
        pass

    pattern = r"""
        (-?\d+)[°\s]+
        (\d+)['\s]+
        ([\d.]+)["\s]*
        ([NSEWnsew]?)
    """
    match = re.search(pattern, dms_string.strip(), re.VERBOSE)

    if not match:
        raise ValueError(f"Formato não reconhecido: '{dms_string}'")

    graus = abs(int(match.group(1)))
    minutos = int(match.group(2))
    segundos = float(match.group(3))
    direcao = match.group(4).upper()

    decimal = graus + minutos / 60 + segundos / 3600

    if direcao in ('S', 'W') or int(match.group(1)) < 0:
        decimal = -abs(decimal)

    return round(decimal, 6)


def parse_coordenada_completa(linha: str):
    """
    Recebe a linha inteira copiada do Google Earth e extrai lat e lon.
    Aceita: 8°06'49.86"S 34°56'46.11"W  ou  -8.113294, -34.946142
    """
    linha = linha.strip()

    pattern_dms = r"""
        (\d+°\d+'\d+\.?\d*"[NSns])
        [\s,]+
        (\d+°\d+'\d+\.?\d*"[EWew])
    """
    match = re.search(pattern_dms, linha, re.VERBOSE)

    if match:
        lat = dms_to_decimal(match.group(1))
        lon = dms_to_decimal(match.group(2))
        return lat, lon

    partes = re.split(r'[\s,]+', linha)
    if len(partes) == 2:
        try:
            return float(partes[0]), float(partes[1])
        except ValueError:
            pass

    raise ValueError(f"Não consegui interpretar: '{linha}'")


def calcular_area_km(bbox):
    """Estimativa da área em km."""
    lat_medio = (bbox['lat_min'] + bbox['lat_max']) / 2
    delta_lat = abs(bbox['lat_max'] - bbox['lat_min'])
    delta_lon = abs(bbox['lon_max'] - bbox['lon_min'])

    altura_km = delta_lat * 111.32
    largura_km = delta_lon * 111.32 * math.cos(math.radians(abs(lat_medio)))
    area_km2 = altura_km * largura_km

    return altura_km, largura_km, area_km2


def main():
    print("=" * 60)
    print("  🛰️  CONVERSOR + DOWNLOAD — Identificação Aérea")
    print("=" * 60)
    print()
    print("Cole as coordenadas DIRETO do Google Earth.")
    print("Formato: 8°06'49.86\"S 34°56'46.11\"W")
    print()

    # Quantos pontos
    qtd_str = input("Quantos pontos? [4] → ").strip()
    qtd = int(qtd_str) if qtd_str else 4

    # Coletar pontos
    pontos = []
    print()
    for i in range(1, qtd + 1):
        while True:
            entrada = input(f"📍 Ponto {i} → ").strip()
            try:
                lat, lon = parse_coordenada_completa(entrada)
                pontos.append((lat, lon))
                print(f"    Lat: {lat}  |  Lon: {lon}")
                break
            except ValueError as e:
                print(f"    {e}")
                print(f"   Tenta de novo...")

    # Bounding box
    lats = [p[0] for p in pontos]
    lons = [p[1] for p in pontos]
    bbox = {
        'lat_min': round(min(lats), 6),
        'lat_max': round(max(lats), 6),
        'lon_min': round(min(lons), 6),
        'lon_max': round(max(lons), 6),
    }

    altura, largura, area = calcular_area_km(bbox)

    # Configurações
    print("\n" + "─" * 60)
    print("  CONFIGURAÇÕES:\n")

    output_dir = input("  Pasta de saída (ex: data/raw_area2) → ").strip()
    if not output_dir:
        output_dir = "data/raw_area_nova"

    zoom_str = input("  Zoom [19] → ").strip()
    zoom = int(zoom_str) if zoom_str else 19

    delay_str = input("  Delay entre downloads [0.5] → ").strip()
    delay = float(delay_str) if delay_str else 0.5

    # Exibir resumo
    print("\n" + "=" * 60)
    print("    RESUMO DA ÁREA")
    print("=" * 60)

    print(f"\n  Bounding Box:")
    print(f"    lat_min: {bbox['lat_min']}")
    print(f"    lat_max: {bbox['lat_max']}")
    print(f"    lon_min: {bbox['lon_min']}")
    print(f"    lon_max: {bbox['lon_max']}")

    print(f"\n   Dimensões estimadas:")
    print(f"    Altura:  {altura:.3f} km")
    print(f"    Largura: {largura:.3f} km")
    print(f"    Área:    {area:.3f} km²")

    # Confirmação e execução
    print(f"\n   Saída:  {output_dir}")
    print(f"   Zoom:   {zoom}")
    print(f"  ⏱  Delay:  {delay}s")
    print()

    confirma = input("   Iniciar download? (s/n) [s] → ").strip().lower()

    if confirma in ('', 's', 'sim', 'y', 'yes'):
        print("\n" + "=" * 60)
        print("  ⬇  INICIANDO DOWNLOAD DOS TILES...")
        print("=" * 60 + "\n")

        comando = [
            sys.executable, "-m", "scripts.download_tiles",
            "--lat-min", str(bbox['lat_min']),
            "--lat-max", str(bbox['lat_max']),
            "--lon-min", str(bbox['lon_min']),
            "--lon-max", str(bbox['lon_max']),
            "--zoom", str(zoom),
            "--output-dir", output_dir,
            "--delay", str(delay),
        ]

        try:
            resultado = subprocess.run(comando)

            if resultado.returncode == 0:
                print("\n" + "=" * 60)
                print("    DOWNLOAD CONCLUÍDO COM SUCESSO!")
                print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print(f"    Download finalizou com código: {resultado.returncode}")
                print("=" * 60)

        except FileNotFoundError:
            print("   Erro: script 'scripts.download_tiles' não encontrado.")
            print("  Verifique se está rodando na raiz do projeto.")
        except KeyboardInterrupt:
            print("\n\n   Download cancelado pelo usuário.")

    else:
        # Se não quiser rodar, pelo menos mostra o comando
        cmd_str = (
            f"python -m scripts.download_tiles \\\n"
            f"    --lat-min {bbox['lat_min']} \\\n"
            f"    --lat-max {bbox['lat_max']} \\\n"
            f"    --lon-min {bbox['lon_min']} \\\n"
            f"    --lon-max {bbox['lon_max']} \\\n"
            f"    --zoom {zoom} \\\n"
            f"    --output-dir {output_dir} \\\n"
            f"    --delay {delay}"
        )
        print(f"\n  Comando para rodar depois:\n")
        print(cmd_str)

    print()


if __name__ == "__main__":
    main()
