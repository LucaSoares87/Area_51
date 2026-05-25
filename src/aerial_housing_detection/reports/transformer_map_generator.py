from pathlib import Path
from string import Template
from typing import Any

from config.settings import get_settings
from src.aerial_housing_detection.domain.grid_aggregation import (
    TransformerLossSummary,
)


class TransformerOperationalMapGenerator:
    """Generates an HTML operational map for transformer loss summaries."""

    def __init__(self, output_dir: Path | None = None) -> None:
        settings = get_settings()
        self.output_dir = output_dir or settings.reports_dir

    def generate_html(
        self,
        summaries: list[TransformerLossSummary],
        coordinates_by_area: dict[str, tuple[float, float]],
        reference_month: str,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "transformer_operational_map.html"

        html = self._render_html(
            summaries=summaries,
            coordinates_by_area=coordinates_by_area,
            reference_month=reference_month,
        )
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _render_html(
        self,
        summaries: list[TransformerLossSummary],
        coordinates_by_area: dict[str, tuple[float, float]],
        reference_month: str,
    ) -> str:
        template = Template(self._template())
        map_points = self._render_map_points(
            summaries=summaries,
            coordinates_by_area=coordinates_by_area,
        )
        ranking_rows = self._render_ranking_rows(summaries)
        summary = self._build_summary(summaries)

        return template.safe_substitute(
            reference_month=reference_month,
            total_transformers=summary["total_transformers"],
            total_estimated_loss=self._format_number(
                summary["total_estimated_loss"],
            ),
            total_solar_generation=self._format_number(
                summary["total_solar_generation"],
            ),
            total_adjusted_loss=self._format_number(
                summary["total_adjusted_loss"],
            ),
            top_adjusted_loss=self._format_number(summary["top_adjusted_loss"]),
            average_solar_offset=self._format_percent(
                summary["average_solar_offset"],
            ),
            map_points=map_points,
            ranking_rows=ranking_rows,
        )

    def _build_summary(
        self,
        summaries: list[TransformerLossSummary],
    ) -> dict[str, Any]:
        total_transformers = len(summaries)
        total_estimated_loss = sum(item.estimated_loss_kwh for item in summaries)
        total_solar_generation = sum(
            item.estimated_generation_kwh for item in summaries
        )
        total_adjusted_loss = sum(item.adjusted_loss_kwh for item in summaries)

        if summaries:
            top_adjusted_loss = max(item.adjusted_loss_kwh for item in summaries)
            average_solar_offset = sum(
                item.solar_offset_ratio for item in summaries
            ) / len(summaries)
        else:
            top_adjusted_loss = 0.0
            average_solar_offset = 0.0

        return {
            "total_transformers": total_transformers,
            "total_estimated_loss": total_estimated_loss,
            "total_solar_generation": total_solar_generation,
            "total_adjusted_loss": total_adjusted_loss,
            "top_adjusted_loss": top_adjusted_loss,
            "average_solar_offset": average_solar_offset,
        }

    def _render_map_points(
        self,
        summaries: list[TransformerLossSummary],
        coordinates_by_area: dict[str, tuple[float, float]],
    ) -> str:
        if not summaries:
            return ""

        points = []
        for summary in summaries:
            coordinates = coordinates_by_area.get(summary.area_id)
            if coordinates is None:
                continue

            latitude, longitude = coordinates
            color = self._risk_color(summary.risk_level)
            size = self._marker_size(summary.adjusted_loss_kwh)
            tooltip = self._tooltip(summary)

            points.append(
                f"""
                {{
                    areaId: "{summary.area_id}",
                    transformerCode: "{summary.transformer_code}",
                    feeder: "{summary.feeder}",
                    latitude: {latitude},
                    longitude: {longitude},
                    color: "{color}",
                    size: {size},
                    tooltip: `{tooltip}`
                }}
                """
            )

        return ",\n".join(points)

    def _render_ranking_rows(
        self,
        summaries: list[TransformerLossSummary],
    ) -> str:
        if not summaries:
            return """
            <tr>
                <td colspan="9">Nenhum transformador encontrado.</td>
            </tr>
            """

        rows = []
        for position, summary in enumerate(summaries, start=1):
            rows.append(
                f"""
                <tr>
                    <td>{position}</td>
                    <td>{summary.transformer_code}</td>
                    <td>{summary.feeder}</td>
                    <td>{summary.area_id}</td>
                    <td>{self._format_number(summary.estimated_loss_kwh)}</td>
                    <td>{self._format_number(summary.estimated_generation_kwh)}</td>
                    <td>{self._format_number(summary.adjusted_loss_kwh)}</td>
                    <td>{self._format_percent(summary.solar_offset_ratio)}</td>
                    <td>{summary.risk_level.upper()}</td>
                </tr>
                """
            )

        return "\n".join(rows)

    def _tooltip(self, summary: TransformerLossSummary) -> str:
        return (
            f"<strong>{summary.transformer_code}</strong><br>"
            f"Área: {summary.area_id}<br>"
            f"Alimentador: {summary.feeder}<br>"
            f"Perda estimada: {self._format_number(summary.estimated_loss_kwh)} kWh<br>"
            f"Geração solar: {self._format_number(summary.estimated_generation_kwh)} kWh<br>"
            f"Perda ajustada: {self._format_number(summary.adjusted_loss_kwh)} kWh<br>"
            f"Offset solar: {self._format_percent(summary.solar_offset_ratio)}<br>"
            f"Risco: {summary.risk_level.upper()}<br>"
            f"Prioridade: {self._format_number(summary.priority_score)}"
        )

    def _risk_color(self, risk_level: str) -> str:
        risk_colors = {
            "critical": "#dc2626",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#22c55e",
        }

        return risk_colors.get(risk_level.lower(), "#64748b")

    def _marker_size(self, adjusted_loss_kwh: float) -> int:
        if adjusted_loss_kwh >= 5000:
            return 18
        if adjusted_loss_kwh >= 2500:
            return 15
        if adjusted_loss_kwh >= 1000:
            return 12
        return 10

    def _format_number(self, value: Any) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0

        formatted = f"{number:,.2f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    def _format_percent(self, value: Any) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 0.0

        return f"{number * 100:.2f}%".replace(".", ",")

    def _template(self) -> str:
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>Area 51 - Mapa Operacional de Transformadores</title>

    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    />

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f5f8;
            color: #111827;
        }

        .layout {
            display: grid;
            grid-template-columns: 72px 1fr;
            min-height: 100vh;
        }

        .sidebar {
            background: #ffffff;
            border-right: 1px solid #d9dee7;
            padding-top: 24px;
            text-align: center;
            color: #637083;
            font-weight: bold;
        }

        .sidebar-item {
            margin: 22px 0;
            font-size: 13px;
        }

        .content {
            padding: 24px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .header h1 {
            margin: 0;
            font-size: 28px;
        }

        .header p {
            margin: 4px 0 0;
            color: #6b7280;
        }

        .filter {
            background: #ffffff;
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid #d9dee7;
            font-size: 14px;
        }

        .kpis {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }

        .kpi {
            background: #ffffff;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
            padding: 14px;
        }

        .kpi-title {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 8px;
        }

        .kpi-value {
            font-size: 20px;
            font-weight: bold;
        }

        .grid {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 16px;
        }

        .card {
            background: #ffffff;
            border: 1px solid #d9dee7;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        }

        .card h2 {
            margin: 0 0 14px;
            font-size: 18px;
        }

        #map {
            height: 560px;
            border-radius: 12px;
            border: 1px solid #d9dee7;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        th {
            text-align: left;
            color: #64748b;
            border-bottom: 1px solid #e5e7eb;
            padding: 10px 8px;
        }

        td {
            border-bottom: 1px solid #eef2f7;
            padding: 10px 8px;
        }

        .legend {
            display: flex;
            gap: 14px;
            margin-top: 12px;
            font-size: 13px;
            color: #4b5563;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .dot {
            width: 12px;
            height: 12px;
            border-radius: 999px;
            display: inline-block;
        }

        .note {
            color: #6b7280;
            font-size: 13px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="layout">
        <aside class="sidebar">
            <div class="sidebar-item">A51</div>
            <div class="sidebar-item">MAP</div>
            <div class="sidebar-item">TR</div>
            <div class="sidebar-item">ALIM</div>
        </aside>

        <main class="content">
            <section class="header">
                <div>
                    <h1>Mapa Operacional de Transformadores</h1>
                    <p>
                        Perdas por transformador, geração solar estimada
                        e perda ajustada no território de Pernambuco.
                    </p>
                </div>
                <div class="filter">
                    Referência: <strong>$reference_month</strong>
                </div>
            </section>

            <section class="kpis">
                <div class="kpi">
                    <div class="kpi-title">Transformadores</div>
                    <div class="kpi-value">$total_transformers</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Perda estimada kWh</div>
                    <div class="kpi-value">$total_estimated_loss</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Geração solar kWh</div>
                    <div class="kpi-value">$total_solar_generation</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Perda ajustada kWh</div>
                    <div class="kpi-value">$total_adjusted_loss</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Maior perda ajustada</div>
                    <div class="kpi-value">$top_adjusted_loss</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Offset solar médio</div>
                    <div class="kpi-value">$average_solar_offset</div>
                </div>
            </section>

            <section class="grid">
                <div class="card">
                    <h2>Mapa de transformadores</h2>
                    <div id="map"></div>
                    <div class="legend">
                        <div class="legend-item">
                            <span class="dot" style="background:#dc2626"></span>
                            Crítico
                        </div>
                        <div class="legend-item">
                            <span class="dot" style="background:#f97316"></span>
                            Alto
                        </div>
                        <div class="legend-item">
                            <span class="dot" style="background:#eab308"></span>
                            Médio
                        </div>
                        <div class="legend-item">
                            <span class="dot" style="background:#22c55e"></span>
                            Baixo
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>Ranking por perda ajustada</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Trafo</th>
                                <th>Alim.</th>
                                <th>Área</th>
                                <th>Perda</th>
                                <th>Solar</th>
                                <th>Ajustada</th>
                                <th>Offset</th>
                                <th>Risco</th>
                            </tr>
                        </thead>
                        <tbody>
                            $ranking_rows
                        </tbody>
                    </table>
                    <div class="note">
                        O mapa usa coordenadas aproximadas por área/transformador.
                    </div>
                </div>
            </section>
        </main>
    </div>

    <script>
        const map = L.map("map").setView([-8.0476, -34.8770], 9);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }).addTo(map);

        const points = [
            $map_points
        ];

        const bounds = [];

        points.forEach((point) => {
            const marker = L.circleMarker([point.latitude, point.longitude], {
                radius: point.size,
                color: "#ffffff",
                weight: 2,
                fillColor: point.color,
                fillOpacity: 0.9
            }).addTo(map);

            marker.bindPopup(point.tooltip);
            bounds.push([point.latitude, point.longitude]);
        });

        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [32, 32] });
        }
    </script>
</body>
</html>
"""
