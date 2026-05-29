from pathlib import Path

from src.aerial_housing_detection.services.demo_realistic_analysis import (
    RealisticAnalysisRequest,
    RealisticDemoAnalysisService,
)

REPORTS_DIR = Path("reports")
MAP_PATH = REPORTS_DIR / "realistic_operational_map.html"


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    service = RealisticDemoAnalysisService()
    analysis = service.analyze(
        RealisticAnalysisRequest(
            latitude=-7.9401,
            longitude=-34.8734,
            radius_meters=600,
        )
    )

    MAP_PATH.write_text(build_map_html(analysis), encoding="utf-8")

    print("Mapa realista gerado com sucesso.")
    print(f"Arquivo: {MAP_PATH}")


def build_map_html(analysis: dict) -> str:
    query = analysis["query"]
    transformers = analysis["transformers"]
    selected = analysis["selected_transformer"]

    markers = "\n".join(_build_marker(transformer) for transformer in transformers)

    return f"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Mapa Realista - Area 51</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  >
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f8fafc;
      color: #0f172a;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 360px 1fr;
      min-height: 100vh;
    }}
    aside {{
      padding: 24px;
      background: #0f172a;
      color: white;
    }}
    aside p {{
      color: #cbd5e1;
      line-height: 1.5;
    }}
    .metric {{
      padding: 12px;
      margin-bottom: 10px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.08);
    }}
    .metric span {{
      display: block;
      color: #cbd5e1;
      font-size: 13px;
    }}
    .metric strong {{
      display: block;
      margin-top: 4px;
      font-size: 18px;
    }}
    #map {{
      width: 100%;
      height: 100vh;
    }}
    .popup {{
      min-width: 280px;
      line-height: 1.5;
    }}
    .popup h3 {{
      margin: 0 0 8px;
    }}
    .download {{
      display: inline-block;
      margin-top: 16px;
      padding: 10px 14px;
      border-radius: 10px;
      color: white;
      background: #2563eb;
      text-decoration: none;
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <h1>Mapa Realista Area 51</h1>
      <p>
        Área analisada por latitude e longitude, com círculo de influência,
        transformadores próximos e estimativa de perdas.
      </p>

      <div class="metric">
        <span>Coordenadas analisadas</span>
        <strong>{query["latitude"]}, {query["longitude"]}</strong>
      </div>

      <div class="metric">
        <span>Transformador selecionado</span>
        <strong>{selected["transformer_code"] if selected else "-"}</strong>
      </div>

      <div class="metric">
        <span>Prioridade</span>
        <strong>{selected["priority"] if selected else "-"}</strong>
      </div>

      <div class="metric">
        <span>Perda estimada</span>
        <strong>{_format_loss(selected)}</strong>
      </div>

      <a class="download" href="/demo/realistic/export.csv?latitude={query["latitude"]}&longitude={query["longitude"]}">
        Baixar CSV da análise
      </a>
    </aside>

    <div id="map"></div>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map("map").setView([{query["latitude"]}, {query["longitude"]}], 15);

    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 19,
      attribution: "OpenStreetMap"
    }}).addTo(map);

    L.circle([{query["latitude"]}, {query["longitude"]}], {{
      color: "#2563eb",
      fillColor: "#60a5fa",
      fillOpacity: 0.22,
      radius: {query["radius_meters"]}
    }}).addTo(map);

    L.marker([{query["latitude"]}, {query["longitude"]}])
      .addTo(map)
      .bindPopup("Coordenada analisada");

    {markers}
  </script>
</body>
</html>
"""


def _build_marker(transformer: dict) -> str:
    popup = _build_popup(transformer)
    latitude = transformer["latitude"]
    longitude = transformer["longitude"]

    return f"""
    L.circleMarker([{latitude}, {longitude}], {{
      radius: 10,
      color: "{_priority_color(transformer["priority"])}",
      fillColor: "{_priority_color(transformer["priority"])}",
      fillOpacity: 0.85
    }})
      .addTo(map)
      .bindPopup(`{popup}`);
    """


def _build_popup(transformer: dict) -> str:
    houses = transformer["houses"]
    people = transformer["people"]
    energy = transformer["energy"]

    return f"""
      <div class="popup">
        <h3>{transformer["transformer_code"]}</h3>
        <strong>Alimentador:</strong> {transformer["feeder_code"]}<br>
        <strong>Subestação:</strong> {transformer["substation_code"]}<br>
        <strong>Potência:</strong> {transformer["power_kva"]} kVA<br>
        <strong>Energia medida:</strong> {energy["measured_energy_kwh"]} kWh<br>
        <strong>Energia recebida GD:</strong> {energy["received_gd_energy_kwh"]} kWh<br>
        <strong>Energia injetada:</strong> {energy["injected_energy_kwh"]} kWh<br>
        <strong>Clientes ligados:</strong> {transformer["customer_count"]}<br>
        <strong>Casas CRAS:</strong> {houses["cras"]}<br>
        <strong>Casas IBGE:</strong> {houses["ibge"]}<br>
        <strong>Telhados:</strong> {houses["roof_image"]}<br>
        <strong>Média estimada:</strong> {houses["average"]} casas<br>
        <strong>Pessoas CRAS:</strong> {people["cras"]}<br>
        <strong>Pessoas IBGE:</strong> {people["ibge"]}<br>
        <strong>Perda estimada:</strong> {energy["estimated_loss_kwh"]} kWh<br>
        <strong>Prioridade:</strong> {transformer["priority"]}
      </div>
    """


def _format_loss(selected: dict | None) -> str:
    if not selected:
        return "-"

    energy = selected["energy"]
    return f'{energy["estimated_loss_kwh"]} kWh ({energy["estimated_loss_percent"]}%)'


def _priority_color(priority: str) -> str:
    if priority == "Alta":
        return "#dc2626"
    if priority == "Média":
        return "#f59e0b"
    return "#16a34a"


if __name__ == "__main__":
    main()