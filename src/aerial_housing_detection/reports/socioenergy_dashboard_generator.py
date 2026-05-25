from pathlib import Path
from string import Template
from typing import Any

from config.settings import get_settings
from src.aerial_housing_detection.domain.socioenergy import SocioEnergyIndicator


class SocioEnergyDashboardGenerator:
    """Generates a socioenergy dashboard as a standalone HTML file."""

    def __init__(self, output_dir: Path | None = None) -> None:
        settings = get_settings()
        self.output_dir = output_dir or settings.reports_dir

    def generate_html(
        self,
        indicators: list[SocioEnergyIndicator],
        reference_month: str,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / "socioenergy_dashboard.html"

        html = self._render_html(
            indicators=indicators,
            reference_month=reference_month,
        )
        output_path.write_text(html, encoding="utf-8")

        return output_path

    def _render_html(
        self,
        indicators: list[SocioEnergyIndicator],
        reference_month: str,
    ) -> str:
        template = Template(self._template())
        summary = self._build_summary(indicators)

        return template.safe_substitute(
            reference_month=reference_month,
            total_areas=summary["total_areas"],
            total_population=self._format_number(summary["total_population"]),
            total_households=self._format_number(summary["total_households"]),
            total_estimated_roofs=self._format_number(
                summary["total_estimated_roofs"],
            ),
            total_customers=self._format_number(summary["total_customers"]),
            total_roof_customer_gap=self._format_number(
                summary["total_roof_customer_gap"],
            ),
            average_vulnerability=self._format_percent(
                summary["average_vulnerability"],
            ),
            top_priority_score=self._format_number(
                summary["top_priority_score"],
            ),
            ranking_rows=self._render_ranking_rows(indicators),
        )

    def _build_summary(
        self,
        indicators: list[SocioEnergyIndicator],
    ) -> dict[str, Any]:
        total_areas = len(indicators)
        total_population = sum(item.population for item in indicators)
        total_households = sum(item.households for item in indicators)
        total_estimated_roofs = sum(item.estimated_roofs for item in indicators)
        total_customers = sum(item.customer_count for item in indicators)
        total_roof_customer_gap = sum(item.roof_customer_gap for item in indicators)

        if indicators:
            average_vulnerability = sum(
                item.vulnerability_ratio for item in indicators
            ) / len(indicators)
            top_priority_score = max(
                item.socioenergy_priority_score for item in indicators
            )
        else:
            average_vulnerability = 0.0
            top_priority_score = 0.0

        return {
            "total_areas": total_areas,
            "total_population": total_population,
            "total_households": total_households,
            "total_estimated_roofs": total_estimated_roofs,
            "total_customers": total_customers,
            "total_roof_customer_gap": total_roof_customer_gap,
            "average_vulnerability": average_vulnerability,
            "top_priority_score": top_priority_score,
        }

    def _render_ranking_rows(
        self,
        indicators: list[SocioEnergyIndicator],
    ) -> str:
        if not indicators:
            return """
            <tr>
                <td colspan="10">Nenhum indicador encontrado.</td>
            </tr>
            """

        rows = []
        for position, indicator in enumerate(indicators, start=1):
            rows.append(
                f"""
                <tr>
                    <td>{position}</td>
                    <td>{indicator.area_id}</td>
                    <td>{indicator.sector_id}</td>
                    <td>{indicator.territory_id}</td>
                    <td>{self._format_number(indicator.estimated_roofs)}</td>
                    <td>{self._format_number(indicator.customer_count)}</td>
                    <td>{self._format_number(indicator.roof_customer_gap)}</td>
                    <td>{self._format_percent(indicator.vulnerability_ratio)}</td>
                    <td>{self._format_percent(indicator.estimated_loss_percent)}</td>
                    <td>
                        {self._format_number(indicator.socioenergy_priority_score)}
                    </td>
                </tr>
                """
            )

        return "\n".join(rows)

    def _format_number(self, value: Any) -> str:
        number = self._to_float(value)
        formatted = f"{number:,.2f}"

        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    def _format_percent(self, value: Any) -> str:
        number = self._to_float(value)
        return f"{number * 100:.2f}%".replace(".", ",")

    def _to_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _template(self) -> str:
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>Area 51 - Painel Socioenergético</title>
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

        .kpis {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
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
            font-size: 22px;
            font-weight: bold;
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

        .note {
            color: #6b7280;
            font-size: 13px;
            margin-top: 10px;
        }

        .priority {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="layout">
        <aside class="sidebar">
            <div class="sidebar-item">A51</div>
            <div class="sidebar-item">SOC</div>
            <div class="sidebar-item">IBGE</div>
            <div class="sidebar-item">CRAS</div>
        </aside>

        <main class="content">
            <section class="header">
                <div>
                    <h1>Visão Socioenergética</h1>
                    <p>
                        Cruzamento entre perdas, telhados estimados,
                        clientes, IBGE e indicadores sociais agregados.
                    </p>
                </div>
                <div class="filter">
                    Referência: <strong>$reference_month</strong>
                </div>
            </section>

            <section class="kpis">
                <div class="kpi">
                    <div class="kpi-title">Áreas analisadas</div>
                    <div class="kpi-value">$total_areas</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">População estimada IBGE</div>
                    <div class="kpi-value">$total_population</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Domicílios IBGE</div>
                    <div class="kpi-value">$total_households</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Telhados estimados</div>
                    <div class="kpi-value">$total_estimated_roofs</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Clientes cadastrados</div>
                    <div class="kpi-value">$total_customers</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Gap telhados x clientes</div>
                    <div class="kpi-value">$total_roof_customer_gap</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Vulnerabilidade média</div>
                    <div class="kpi-value">$average_vulnerability</div>
                </div>
                <div class="kpi">
                    <div class="kpi-title">Maior prioridade</div>
                    <div class="kpi-value">$top_priority_score</div>
                </div>
            </section>

            <section class="card">
                <h2>Ranking socioenergético</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Área</th>
                            <th>Setor IBGE</th>
                            <th>Território CRAS</th>
                            <th>Telhados</th>
                            <th>Clientes</th>
                            <th>Gap telhados</th>
                            <th>Vulnerabilidade</th>
                            <th>Perda %</th>
                            <th>Prioridade</th>
                        </tr>
                    </thead>
                    <tbody>
                        $ranking_rows
                    </tbody>
                </table>
                <div class="note">
                    Indicadores baseados em dados agregados. O painel deve ser usado
                    para priorização territorial, não para inferência individual.
                </div>
            </section>
        </main>
    </div>
</body>
</html>
"""
