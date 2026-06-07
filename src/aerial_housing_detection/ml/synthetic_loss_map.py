import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
MAP_PATH = Path("reports/synthetic_loss_heatmap_map.html")


@dataclass(frozen=True)
class SyntheticLossMapResult:
    database_path: str
    map_path: str
    transformer_points: int
    feeder_points: int
    high_heat_transformers: int
    high_heat_feeders: int


class SyntheticLossMapBuilder:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        map_path: Path = MAP_PATH,
    ) -> None:
        self.db_path = db_path
        self.map_path = map_path

    def run(self) -> SyntheticLossMapResult:
        transformer_rows = self._read_transformer_rows()
        feeder_rows = self._read_feeder_rows()

        transformer_points = [
            build_transformer_map_point(row) for row in transformer_rows
        ]
        feeder_points = [build_feeder_map_point(row) for row in feeder_rows]

        document = build_map_html(
            transformer_points=transformer_points,
            feeder_points=feeder_points,
        )

        self.map_path.parent.mkdir(parents=True, exist_ok=True)
        self.map_path.write_text(document, encoding="utf-8")

        return SyntheticLossMapResult(
            database_path=str(self.db_path),
            map_path=str(self.map_path),
            transformer_points=len(transformer_points),
            feeder_points=len(feeder_points),
            high_heat_transformers=sum(
                1 for point in transformer_points if point["nivel_calor"] == "ALTO"
            ),
            high_heat_feeders=sum(
                1 for point in feeder_points if point["nivel_calor"] == "ALTO"
            ),
        )

    def _read_transformer_rows(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            if not _table_exists(connection, "synthetic_transformer_heatmap"):
                return []

            rows = connection.execute(
                """
                SELECT
                    codigo_transformador,
                    codigo_subestacao,
                    codigo_alimentador,
                    mes_referencia,
                    latitude,
                    longitude,
                    consumo_faturado_kwh,
                    energia_injetada_total,
                    perda_estimada_kwh,
                    perda_estimada_percentual,
                    qtd_irregularidades_confirmadas,
                    target_irregularidade_confirmada,
                    nivel_calor
                FROM synthetic_transformer_heatmap
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def _read_feeder_rows(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            if not _table_exists(connection, "synthetic_feeder_heatmap"):
                return []

            rows = connection.execute(
                """
                SELECT
                    codigo_subestacao,
                    codigo_alimentador,
                    mes_referencia,
                    qtd_transformadores,
                    latitude_centroide,
                    longitude_centroide,
                    consumo_faturado_kwh,
                    perda_estimada_kwh,
                    perda_estimada_percentual_media,
                    qtd_irregularidades_confirmadas,
                    nivel_calor_alimentador
                FROM synthetic_feeder_heatmap
                WHERE latitude_centroide IS NOT NULL
                  AND longitude_centroide IS NOT NULL
                """
            ).fetchall()

            return [dict(row) for row in rows]


def build_transformer_map_point(row: dict[str, Any]) -> dict[str, Any]:
    nivel_calor = str(row.get("nivel_calor") or "BAIXO").upper()

    return {
        "tipo": "transformador",
        "codigo": str(row.get("codigo_transformador") or ""),
        "codigo_subestacao": str(row.get("codigo_subestacao") or ""),
        "codigo_alimentador": str(row.get("codigo_alimentador") or ""),
        "mes_referencia": str(row.get("mes_referencia") or ""),
        "latitude": _to_float(row.get("latitude")),
        "longitude": _to_float(row.get("longitude")),
        "consumo_faturado_kwh": _to_float(row.get("consumo_faturado_kwh")),
        "energia_injetada_total": _to_float(row.get("energia_injetada_total")),
        "perda_estimada_kwh": _to_float(row.get("perda_estimada_kwh")),
        "perda_estimada_percentual": _to_float(row.get("perda_estimada_percentual")),
        "qtd_irregularidades_confirmadas": _to_int(
            row.get("qtd_irregularidades_confirmadas")
        ),
        "target_irregularidade_confirmada": _to_int(
            row.get("target_irregularidade_confirmada")
        ),
        "nivel_calor": nivel_calor,
        "intensidade": _heat_intensity(nivel_calor),
    }


def build_feeder_map_point(row: dict[str, Any]) -> dict[str, Any]:
    nivel_calor = str(row.get("nivel_calor_alimentador") or "BAIXO").upper()

    return {
        "tipo": "alimentador",
        "codigo": str(row.get("codigo_alimentador") or ""),
        "codigo_subestacao": str(row.get("codigo_subestacao") or ""),
        "codigo_alimentador": str(row.get("codigo_alimentador") or ""),
        "mes_referencia": str(row.get("mes_referencia") or ""),
        "latitude": _to_float(row.get("latitude_centroide")),
        "longitude": _to_float(row.get("longitude_centroide")),
        "qtd_transformadores": _to_int(row.get("qtd_transformadores")),
        "consumo_faturado_kwh": _to_float(row.get("consumo_faturado_kwh")),
        "perda_estimada_kwh": _to_float(row.get("perda_estimada_kwh")),
        "perda_estimada_percentual": _to_float(
            row.get("perda_estimada_percentual_media")
        ),
        "qtd_irregularidades_confirmadas": _to_int(
            row.get("qtd_irregularidades_confirmadas")
        ),
        "nivel_calor": nivel_calor,
        "intensidade": _heat_intensity(nivel_calor),
    }


def build_map_html(
    transformer_points: list[dict[str, Any]],
    feeder_points: list[dict[str, Any]],
) -> str:
    all_points = transformer_points + feeder_points

    summary = {
        "transformer_points": len(transformer_points),
        "feeder_points": len(feeder_points),
        "high_heat_transformers": sum(
            1 for point in transformer_points if point["nivel_calor"] == "ALTO"
        ),
        "high_heat_feeders": sum(
            1 for point in feeder_points if point["nivel_calor"] == "ALTO"
        ),
    }

    center_latitude = _average([point["latitude"] for point in all_points])
    center_longitude = _average([point["longitude"] for point in all_points])

    points_json = json.dumps(all_points, ensure_ascii=False)
    summary_json = json.dumps(summary, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Area 51 - Mapa Sintético de Perdas</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #0f172a;
      color: #e5e7eb;
    }}
    header {{
      padding: 18px 24px;
      background: #111827;
      border-bottom: 1px solid #374151;
    }}
    header h1 {{
      margin: 0;
      font-size: 22px;
    }}
    header p {{
      margin: 6px 0 0;
      color: #cbd5e1;
      font-size: 14px;
    }}
    main {{
      display: grid;
      grid-template-columns: 340px 1fr;
      min-height: calc(100vh - 78px);
    }}
    aside {{
      padding: 18px;
      background: #020617;
      border-right: 1px solid #374151;
      overflow: auto;
    }}
    .metric {{
      padding: 12px;
      margin-bottom: 12px;
      border: 1px solid #334155;
      border-radius: 10px;
      background: #0f172a;
    }}
    .metric strong {{
      display: block;
      font-size: 24px;
      margin-bottom: 4px;
    }}
    .metric span {{
      color: #cbd5e1;
      font-size: 13px;
    }}
    .legend {{
      margin-top: 18px;
      padding: 12px;
      border: 1px solid #334155;
      border-radius: 10px;
      background: #0f172a;
    }}
    .legend-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 8px 0;
      font-size: 13px;
    }}
    .dot {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      display: inline-block;
    }}
    .high {{ background: #ef4444; }}
    .medium {{ background: #f59e0b; }}
    .low {{ background: #22c55e; }}
    #map {{
      position: relative;
      min-height: calc(100vh - 78px);
      background:
        linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
        linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
        #1e293b;
      background-size: 48px 48px;
      overflow: hidden;
    }}
    .point {{
      position: absolute;
      width: 16px;
      height: 16px;
      border-radius: 999px;
      border: 2px solid white;
      transform: translate(-50%, -50%);
      cursor: pointer;
      box-shadow: 0 0 18px rgba(255, 255, 255, 0.32);
    }}
    .point.transformador {{
      width: 13px;
      height: 13px;
    }}
    .point.alimentador {{
      width: 22px;
      height: 22px;
      opacity: 0.72;
    }}
    .tooltip {{
      position: absolute;
      display: none;
      min-width: 260px;
      max-width: 360px;
      background: #020617;
      color: #e5e7eb;
      border: 1px solid #475569;
      border-radius: 10px;
      padding: 12px;
      font-size: 13px;
      z-index: 10;
      box-shadow: 0 12px 36px rgba(0,0,0,0.35);
    }}
    .tooltip h3 {{
      margin: 0 0 8px;
      font-size: 15px;
    }}
    .tooltip p {{
      margin: 4px 0;
      color: #cbd5e1;
    }}
    .notice {{
      margin-top: 18px;
      color: #94a3b8;
      font-size: 12px;
      line-height: 1.45;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Area 51 - Mapa Sintético de Perdas</h1>
    <p>Visualização sintética de criticidade por transformador e alimentador. Dados fictícios para simulação segura.</p>
  </header>
  <main>
    <aside>
      <div class="metric">
        <strong id="transformer-count">0</strong>
        <span>Pontos de transformadores</span>
      </div>
      <div class="metric">
        <strong id="feeder-count">0</strong>
        <span>Pontos de alimentadores</span>
      </div>
      <div class="metric">
        <strong id="high-transformer-count">0</strong>
        <span>Transformadores em calor alto</span>
      </div>
      <div class="metric">
        <strong id="high-feeder-count">0</strong>
        <span>Alimentadores em calor alto</span>
      </div>

      <div class="legend">
        <strong>Legenda</strong>
        <div class="legend-row"><span class="dot high"></span> Alto calor operacional</div>
        <div class="legend-row"><span class="dot medium"></span> Médio calor operacional</div>
        <div class="legend-row"><span class="dot low"></span> Baixo calor operacional</div>
      </div>

      <div class="notice">
        Esta visualização usa dados sintéticos. A finalidade é validar a camada
        de mapa antes da integração com dados reais, CRAS, IBGE, imagem e
        inspeções de campo.
      </div>
    </aside>
    <section id="map">
      <div id="tooltip" class="tooltip"></div>
    </section>
  </main>

  <script>
    const points = {points_json};
    const summary = {summary_json};
    const center = {{
      latitude: {center_latitude},
      longitude: {center_longitude}
    }};

    document.getElementById("transformer-count").textContent = summary.transformer_points;
    document.getElementById("feeder-count").textContent = summary.feeder_points;
    document.getElementById("high-transformer-count").textContent = summary.high_heat_transformers;
    document.getElementById("high-feeder-count").textContent = summary.high_heat_feeders;

    const map = document.getElementById("map");
    const tooltip = document.getElementById("tooltip");

    const latitudes = points.map(point => point.latitude);
    const longitudes = points.map(point => point.longitude);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLng = Math.min(...longitudes);
    const maxLng = Math.max(...longitudes);

    function colorForLevel(level) {{
      if (level === "ALTO") return "#ef4444";
      if (level === "MEDIO") return "#f59e0b";
      return "#22c55e";
    }}

    function normalize(value, min, max) {{
      if (max === min) return 50;
      return ((value - min) / (max - min)) * 86 + 7;
    }}

    function yPosition(latitude) {{
      return 100 - normalize(latitude, minLat, maxLat);
    }}

    function xPosition(longitude) {{
      return normalize(longitude, minLng, maxLng);
    }}

    function formatNumber(value) {{
      return Number(value || 0).toLocaleString("pt-BR", {{
        maximumFractionDigits: 2
      }});
    }}

    function renderTooltip(point) {{
      const title = point.tipo === "alimentador"
        ? `Alimentador ${{point.codigo_alimentador}}`
        : `Transformador ${{point.codigo}}`;

      return `
        <h3>${{title}}</h3>
        <p><strong>Subestação:</strong> ${{point.codigo_subestacao}}</p>
        <p><strong>Mês:</strong> ${{point.mes_referencia}}</p>
        <p><strong>Nível:</strong> ${{point.nivel_calor}}</p>
        <p><strong>Consumo:</strong> ${{formatNumber(point.consumo_faturado_kwh)}} kWh</p>
        <p><strong>Perda estimada:</strong> ${{formatNumber(point.perda_estimada_kwh)}} kWh</p>
        <p><strong>Perda percentual:</strong> ${{formatNumber(point.perda_estimada_percentual * 100)}}%</p>
        <p><strong>Irregularidades:</strong> ${{point.qtd_irregularidades_confirmadas || 0}}</p>
      `;
    }}

    points.forEach(point => {{
      const element = document.createElement("div");
      element.className = `point ${{point.tipo}}`;
      element.style.left = `${{xPosition(point.longitude)}}%`;
      element.style.top = `${{yPosition(point.latitude)}}%`;
      element.style.background = colorForLevel(point.nivel_calor);
      element.style.opacity = point.tipo === "alimentador" ? "0.58" : "0.9";

      element.addEventListener("mouseenter", event => {{
        tooltip.innerHTML = renderTooltip(point);
        tooltip.style.display = "block";
        tooltip.style.left = `${{event.clientX + 12}}px`;
        tooltip.style.top = `${{event.clientY + 12}}px`;
      }});

      element.addEventListener("mousemove", event => {{
        tooltip.style.left = `${{event.clientX + 12}}px`;
        tooltip.style.top = `${{event.clientY + 12}}px`;
      }});

      element.addEventListener("mouseleave", () => {{
        tooltip.style.display = "none";
      }});

      map.appendChild(element);
    }});
  </script>
</body>
</html>
"""


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def _heat_intensity(level: str) -> int:
    if level == "ALTO":
        return 100

    if level == "MEDIO":
        return 60

    return 25


def _average(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(sum(values) / len(values), 6)


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0

    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0

    return int(float(value))
