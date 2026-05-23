from html import escape
from pathlib import Path

from config.settings import get_settings
from src.aerial_housing_detection.domain.detection import DetectionResult


class MapRenderer:
    """Generates a simple HTML map-like report for roof detections."""

    def __init__(self) -> None:
        """Initialize map renderer settings."""
        self.settings = get_settings()

    def render_html(self, result: DetectionResult) -> Path:
        """Generate an HTML visualization from a detection result.

        Args:
            result: Detection result.

        Returns:
            Generated HTML file path.
        """
        html_path = self.settings.reports_dir / f"{result.analysis_id}{self.settings.html_map_filename_suffix}"

        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(self._build_html(result), encoding="utf-8")

        return html_path

    def _build_html(self, result: DetectionResult) -> str:
        """Build HTML content.

        Args:
            result: Detection result.

        Returns:
            HTML content.
        """
        image_width = result.image_metadata.image_size.width
        image_height = result.image_metadata.image_size.height

        boxes_html = "\n".join(
            self._render_detection_box(result=result, index=index) for index, _ in enumerate(result.detections, start=1)
        )

        file_name = escape(result.image_metadata.file_name)

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>Relatório de Detecção Aérea</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 32px;
            background: #f5f5f5;
            color: #222;
        }}

        .container {{
            max-width: 1180px;
            margin: 0 auto;
            background: #fff;
            padding: 24px;
            border: 1px solid #ddd;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}

        .card {{
            border: 1px solid #ddd;
            padding: 12px;
            background: #fafafa;
        }}

        .stage {{
            position: relative;
            width: 100%;
            aspect-ratio: {image_width} / {image_height};
            border: 1px solid #999;
            background:
                linear-gradient(45deg, #e8e8e8 25%, transparent 25%),
                linear-gradient(-45deg, #e8e8e8 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #e8e8e8 75%),
                linear-gradient(-45deg, transparent 75%, #e8e8e8 75%);
            background-size: 24px 24px;
            background-position: 0 0, 0 12px, 12px -12px, -12px 0px;
            overflow: hidden;
        }}

        .box {{
            position: absolute;
            border: 2px solid #222;
            background: rgba(0, 0, 0, 0.08);
            box-sizing: border-box;
            font-size: 11px;
            padding: 2px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 24px;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            font-size: 13px;
        }}

        th {{
            background: #eee;
        }}
    </style>
</head>
<body>
    <main class="container">
        <h1>Relatório de Detecção Aérea de Residências</h1>

        <section class="summary">
            <div class="card">
                <strong>Análise</strong>
                <p>{escape(result.analysis_id)}</p>
            </div>
            <div class="card">
                <strong>Imagem</strong>
                <p>{file_name}</p>
            </div>
            <div class="card">
                <strong>Telhados</strong>
                <p>{result.roof_count}</p>
            </div>
            <div class="card">
                <strong>Residências estimadas</strong>
                <p>{result.estimated_residences}</p>
            </div>
        </section>

        <h2>Mapa HTML de detecções</h2>
        <div class="stage">
            {boxes_html}
        </div>

        <h2>Detalhamento</h2>
        {self._render_table(result)}
    </main>
</body>
</html>
"""

    def _render_detection_box(self, result: DetectionResult, index: int) -> str:
        """Render one detection box.

        Args:
            result: Detection result.
            index: Detection index starting at 1.

        Returns:
            HTML div for one detection.
        """
        detection = result.detections[index - 1]
        image_width = result.image_metadata.image_size.width
        image_height = result.image_metadata.image_size.height

        left = detection.bbox.x / image_width * 100
        top = detection.bbox.y / image_height * 100
        width = detection.bbox.width / image_width * 100
        height = detection.bbox.height / image_height * 100

        return (
            f'<div class="box" style="left:{left:.4f}%; top:{top:.4f}%; '
            f'width:{width:.4f}%; height:{height:.4f}%;">'
            f"{index}</div>"
        )

    def _render_table(self, result: DetectionResult) -> str:
        """Render detection details table.

        Args:
            result: Detection result.

        Returns:
            HTML table.
        """
        rows = []

        for index, detection in enumerate(result.detections, start=1):
            rows.append(
                "<tr>"
                f"<td>{index}</td>"
                f"<td>{escape(detection.detection_id)}</td>"
                f"<td>{detection.confidence_score:.4f}</td>"
                f"<td>{detection.bbox.x:.2f}</td>"
                f"<td>{detection.bbox.y:.2f}</td>"
                f"<td>{detection.bbox.width:.2f}</td>"
                f"<td>{detection.bbox.height:.2f}</td>"
                f"<td>{detection.bbox.area:.2f}</td>"
                "</tr>"
            )

        if not rows:
            rows.append('<tr><td colspan="8">Nenhuma detecção encontrada.</td></tr>')

        rows_html = "\n".join(rows)

        return f"""
<table>
    <thead>
        <tr>
            <th>#</th>
            <th>ID da detecção</th>
            <th>Confiança</th>
            <th>X</th>
            <th>Y</th>
            <th>Largura</th>
            <th>Altura</th>
            <th>Área</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>
"""
