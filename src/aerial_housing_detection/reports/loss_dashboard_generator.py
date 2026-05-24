from pathlib import Path
from string import Template
from typing import Any

from config.settings import get_settings


class LossDashboardGenerator:
    """Generates an operational losses dashboard as a standalone HTML file."""

    def __init__(self, output_dir: Path | None = None) -> None:
        settings = get_settings()
        self.output_dir = output_dir or settings.reports_dir

    def generate_html(
        self,
        records: list[dict[str, Any]],
        summary: dict[str, Any],
        reference_month: str | None = None,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "losses_dashboard.html"

        html = self._render_html(
            records=records,
            summary=summary,
            reference_month=reference_month,
        )
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _render_html(
        self,
        records: list[dict[str, Any]],
        summary: dict[str, Any],
        reference_month: str | None,
    ) -> str:
        template = Template(self._template())

        return template.safe_substitute(
            reference_month=reference_month or "Todos os meses",
            total_areas=summary.get("total_areas", 0),
            critical_areas=summary.get("critical_areas", 0),
            high_risk_areas=summary.get("high_risk_areas", 0),
            estimated_loss_kwh=self._format_number(
                summary.get("estimated_loss_kwh", 0),
            ),
            average_loss_percent=self._format_percent(
                summary.get("average_loss_percent", 0),
            ),
            top_priority_score=self._format_number(
                summary.get("top_priority_score", 0),
            ),
            ranking_rows=self._render_ranking_rows(records),
            map_points=self._render_map_points(records),
        )

    def _render_ranking_rows(self, records: list[dict[str, Any]]) -> str:
        if not records:
            return """
            <tr>
                <td colspan="7">Nenhum registro encontrado.</td>
            </tr>
            """

        rows = []
        for position, record in enumerate(records, start=1):
            transformer_code = self._get_text(record, "transformer_code")
            neighborhood = self._get_text(record, "neighborhood")
            city = self._get_text(record, "city")
            risk_level = self._get_risk_level(record)

            estimated_loss_kwh = self._format_number(
                record.get("estimated_loss_kwh", 0),
            )
            estimated_loss_percent = self._format_percent(
                record.get("estimated_loss_percent", 0),
            )

            rows.append(
                f"""
                <tr>
                    <td>{position}</td>
                    <td>{transformer_code}</td>
                    <td>{neighborhood}</td>
                    <td>{city}</td>
                    <td>{estimated_loss_kwh}</td>
                    <td>{estimated_loss_percent}</td>
                    <td>
                        <span class="risk risk-{risk_level}">
                            {risk_level}
                        </span>
                    </td>
                </tr>
                """
            )

        return "\n".join(rows)

    def _render_map_points(self, records: list[dict[str, Any]]) -> str:
        if not records:
            return '<div class="empty-map">Sem pontos para exibir.</div>'

        points = []
        for record in records:
            latitude = self._to_float(record.get("latitude", 0))
            longitude = self._to_float(record.get("longitude", 0))

            left = self._normalize_coordinate(
                value=longitude,
                min_value=-35.0,
                max_value=-34.7,
            )
            top = 100 - self._normalize_coordinate(
                value=latitude,
                min_value=-8.1,
                max_value=-7.8,
            )

            risk_level = self._get_risk_level(record)
            title = self._build_point_title(record)

            points.append(
                f"""
                <div
                    class="map-point risk-{risk_level}"
                    style="left: {left:.2f}%; top: {top:.2f}%;"
                    title="{title}">
                </div>
                """
            )

        return "\n".join(points)

    def _build_point_title(self, record: dict[str, Any]) -> str:
        transformer_code = self._get_text(record, "transformer_code")
        neighborhood = self._get_text(record, "neighborhood")
        loss_percent = self._format_percent(
            record.get("estimated_loss_percent", 0),
        )

        return f"{transformer_code} - {neighborhood} - {loss_percent}"

    def _normalize_coordinate(
        self,
        value: float,
        min_value: float,
        max_value: float,
    ) -> float:
        if max_value == min_value:
            return 50.0

        normalized = ((value - min_value) / (max_value - min_value)) * 100
        return min(95.0, max(5.0, normalized))

    def _get_text(self, record: dict[str, Any], key: str) -> str:
        value = record.get(key, "")
        if value is None:
            return ""

        return str(value)

    def _get_risk_level(self, record: dict[str, Any]) -> str:
        risk_level = self._get_text(record, "risk_level").lower().strip()
        allowed_levels = {"critical", "high", "medium", "low"}

        if risk_level in allowed_levels:
            return risk_level

        return "low"

    def _to_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _format_number(self, value: Any) -> str:
        number = self._to_float(value)
        formatted = f"{number:,.2f}"

        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    def _format_percent(self, value: Any) -> str:
        number = self._to_float(value)
        return f"{number * 100:.2f}%".replace(".", ",")

    def _template(self) -> str:
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>Area 51 - Painel de Perdas Operacionais</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f5f8;
            color: #1f2933;
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
            margin-bottom: 18px;
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

        .grid {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
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

        .kpis {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }

        .kpi {
            background: #f8fafc;
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
            font-size: 22px;
            font-weight: bold;
        }

        .map {
            position: relative;
            height: 420px;
            border-radius: 12px;
            overflow: hidden;
            background:
                linear-gradient(
                    135deg,
                    rgba(15, 23, 42, 0.92),
                    rgba(30, 41, 59, 0.96)
                ),
                radial-gradient(
                    circle at 70% 40%,
                    rgba(34, 197, 94, 0.2),
                    transparent 28%
                );
            border: 1px solid #111827;
        }

        .map-label {
            position: absolute;
            left: 16px;
            bottom: 16px;
            color: #cbd5e1;
            font-size: 13px;
        }

        .map-point {
            position: absolute;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            border: 2px solid #ffffff;
            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.18);
        }

        .risk-critical {
            background: #dc2626;
        }

        .risk-high {
            background: #f97316;
        }

        .risk-medium {
            background: #eab308;
        }

        .risk-low {
            background: #16a34a;
        }

        .empty-map {
            color: #ffffff;
            padding: 24px;
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

        .risk {
            color: #ffffff;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 12px;
            text-transform: uppercase;
            font-weight: bold;
        }

        .full {
            grid-column: 1 / -1;
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
            <div class="sidebar-item">KPI</div>
            <div class="sidebar-item">RANK</div>
        </aside>

        <main class="content">
            <section class="header">
                <div>
                    <h1>Visão Operacional de Perdas</h1>
                    <p>
                        Monitoramento de áreas críticas por transformador
                        e ciclo mensal.
                    </p>
                </div>
                <div class="filter">
                    Referência: <strong>$reference_month</strong>
                </div>
            </section>

            <section class="kpis">
                <div class="kpi">
                    <div class="kpi-title">Áreas monitoradas</div>
                    <div class="kpi-value">$total_areas</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Áreas críticas</div>
                    <div class="kpi-value">$critical_areas</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Alto risco</div>
                    <div class="kpi-value">$high_risk_areas</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Perda estimada kWh</div>
                    <div class="kpi-value">$estimated_loss_kwh</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Perda média</div>
                    <div class="kpi-value">$average_loss_percent</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Maior prioridade</div>
                    <div class="kpi-value">$top_priority_score</div>
                </div>
            </section>

            <section class="grid">
                <div class="card">
                    <h2>Mapa operacional</h2>
                    <div class="map">
                        $map_points
                        <div class="map-label">
                            Pontos aproximados por latitude/longitude
                        </div>
                    </div>
                    <div class="note">
                        Mapa demonstrativo para priorização. Integração com
                        mapa real será adicionada em fase posterior.
                    </div>
                </div>

                <div class="card">
                    <h2>Ranking de áreas críticas</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Transformador</th>
                                <th>Bairro</th>
                                <th>Cidade</th>
                                <th>Perda kWh</th>
                                <th>Perda %</th>
                                <th>Risco</th>
                            </tr>
                        </thead>
                        <tbody>
                            $ranking_rows
                        </tbody>
                    </table>
                </div>
            </section>
        </main>
    </div>
</body>
</html>
"""
