import json
import sqlite3
from pathlib import Path

DATA_PATH = Path("data/demo/area51_demo_assets.json")
DB_PATH = Path("data/area51.db")
REPORTS_DIR = Path("reports")
MAP_PATH = REPORTS_DIR / "transformer_operational_map.html"


def main() -> None:
    demo_data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assets = demo_data["assets"]

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        create_tables(connection)
        insert_assets(connection, demo_data["reference_month"], assets)

    MAP_PATH.write_text(build_map_html(assets), encoding="utf-8")

    print("Dados demo carregados com sucesso.")
    print(f"Banco local: {DB_PATH}")
    print(f"Mapa operacional: {MAP_PATH}")
    print("Use na interface:")
    print("Transformador: TR-001")
    print("Alimentador: AL-01")
    print("Subestação: SE-01")
    print("Coordenadas: -7.9401, -34.8734")


def create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_operational_assets (
            reference_month TEXT NOT NULL,
            area_id TEXT NOT NULL,
            transformer_code TEXT NOT NULL PRIMARY KEY,
            feeder_code TEXT NOT NULL,
            substation_code TEXT NOT NULL,
            city TEXT NOT NULL,
            neighborhood TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            customer_count INTEGER NOT NULL,
            supplied_energy_kwh REAL NOT NULL,
            billed_energy_kwh REAL NOT NULL,
            estimated_loss_kwh REAL NOT NULL,
            loss_percent REAL NOT NULL,
            loss_recurrence_months INTEGER NOT NULL,
            solar_estimated_kwh REAL NOT NULL,
            adjusted_loss_kwh REAL NOT NULL,
            adjusted_loss_percent REAL NOT NULL,
            estimated_roofs INTEGER NOT NULL,
            cras_territory TEXT NOT NULL,
            ibge_sector_id TEXT NOT NULL,
            vulnerability_index REAL NOT NULL,
            priority TEXT NOT NULL,
            risk_label TEXT NOT NULL
        )
        """
    )


def insert_assets(
    connection: sqlite3.Connection,
    reference_month: str,
    assets: list[dict],
) -> None:
    connection.execute("DELETE FROM demo_operational_assets")

    for asset in assets:
        connection.execute(
            """
            INSERT INTO demo_operational_assets (
                reference_month,
                area_id,
                transformer_code,
                feeder_code,
                substation_code,
                city,
                neighborhood,
                latitude,
                longitude,
                customer_count,
                supplied_energy_kwh,
                billed_energy_kwh,
                estimated_loss_kwh,
                loss_percent,
                loss_recurrence_months,
                solar_estimated_kwh,
                adjusted_loss_kwh,
                adjusted_loss_percent,
                estimated_roofs,
                cras_territory,
                ibge_sector_id,
                vulnerability_index,
                priority,
                risk_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reference_month,
                asset["area_id"],
                asset["transformer_code"],
                asset["feeder_code"],
                asset["substation_code"],
                asset["city"],
                asset["neighborhood"],
                asset["latitude"],
                asset["longitude"],
                asset["customer_count"],
                asset["supplied_energy_kwh"],
                asset["billed_energy_kwh"],
                asset["estimated_loss_kwh"],
                asset["loss_percent"],
                asset["loss_recurrence_months"],
                asset["solar_estimated_kwh"],
                asset["adjusted_loss_kwh"],
                asset["adjusted_loss_percent"],
                asset["estimated_roofs"],
                asset["cras_territory"],
                asset["ibge_sector_id"],
                asset["vulnerability_index"],
                asset["priority"],
                asset["risk_label"],
            ),
        )


def build_map_html(assets: list[dict]) -> str:
    rows = "\n".join(
        f"""
        <tr>
          <td>{asset["transformer_code"]}</td>
          <td>{asset["feeder_code"]}</td>
          <td>{asset["substation_code"]}</td>
          <td>{asset["neighborhood"]}</td>
          <td>{asset["customer_count"]}</td>
          <td>{asset["estimated_loss_kwh"]:,.0f} kWh</td>
          <td>{asset["solar_estimated_kwh"]:,.0f} kWh</td>
          <td>{asset["adjusted_loss_kwh"]:,.0f} kWh</td>
          <td>{asset["priority"]}</td>
        </tr>
        """
        for asset in assets
    )

    cards = "\n".join(
        f"""
        <section class="asset-card priority-{asset["priority"].lower()}">
          <h2>{asset["transformer_code"]}</h2>
          <p><strong>Área:</strong> {asset["area_id"]}</p>
          <p><strong>Localidade:</strong> {asset["neighborhood"]} - {asset["city"]}</p>
          <p><strong>Clientes:</strong> {asset["customer_count"]}</p>
          <p><strong>Perda estimada:</strong> {asset["estimated_loss_kwh"]:,.0f} kWh ({asset["loss_percent"]}%)</p>
          <p><strong>GD/Solar estimada:</strong> {asset["solar_estimated_kwh"]:,.0f} kWh</p>
          <p><strong>Perda ajustada:</strong> {asset["adjusted_loss_kwh"]:,.0f} kWh ({asset["adjusted_loss_percent"]}%)</p>
          <p><strong>CRAS:</strong> {asset["cras_territory"]}</p>
          <p><strong>IBGE:</strong> {asset["ibge_sector_id"]}</p>
          <p><strong>Prioridade:</strong> {asset["priority"]}</p>
        </section>
        """
        for asset in assets
    )

    return f"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Mapa Operacional Demo - Area 51</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: #f3f6fb;
      color: #0f172a;
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0;
    }}
    .hero {{
      background: #0f172a;
      color: white;
      padding: 28px;
      border-radius: 18px;
      margin-bottom: 22px;
    }}
    .hero p {{
      color: #cbd5e1;
      max-width: 860px;
      line-height: 1.6;
    }}
    .heatmap {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }}
    .asset-card {{
      background: white;
      border: 1px solid #dbe3ef;
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    }}
    .asset-card h2 {{
      margin-top: 0;
    }}
    .priority-alta {{
      border-top: 8px solid #dc2626;
    }}
    .priority-média {{
      border-top: 8px solid #f59e0b;
    }}
    .priority-baixa {{
      border-top: 8px solid #16a34a;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    }}
    th,
    td {{
      padding: 12px 14px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
      font-size: 14px;
    }}
    th {{
      background: #1d4ed8;
      color: white;
    }}
    .note {{
      margin-top: 18px;
      padding: 16px;
      background: #e0f2fe;
      border-radius: 12px;
      color: #075985;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>Mapa Operacional Demo - Area 51</h1>
      <p>
        Visão demonstrativa de transformadores, perdas estimadas, geração solar estimada,
        perda ajustada, CRAS, IBGE e prioridade operacional para gravação do piloto.
      </p>
    </section>

    <section class="heatmap">
      {cards}
    </section>

    <table>
      <thead>
        <tr>
          <th>Transformador</th>
          <th>Alimentador</th>
          <th>Subestação</th>
          <th>Localidade</th>
          <th>Clientes</th>
          <th>Perda estimada</th>
          <th>Solar/GD</th>
          <th>Perda ajustada</th>
          <th>Prioridade</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>

    <div class="note">
      Este mapa é um artefato de demonstração local. Em piloto real, os pontos e indicadores
      devem ser gerados a partir das bases oficiais da concessionária.
    </div>
  </main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
