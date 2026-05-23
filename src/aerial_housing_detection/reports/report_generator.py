import csv
from pathlib import Path

from config.settings import get_settings
from src.aerial_housing_detection.domain.detection import DetectionResult


class ReportGenerator:
    """Generates CSV reports for aerial housing detection results."""

    def __init__(self) -> None:
        """Initialize report generator settings."""
        self.settings = get_settings()

    def generate_csv(self, result: DetectionResult) -> Path:
        """Generate a CSV report from a detection result.

        Args:
            result: Detection result.

        Returns:
            Generated CSV report path.
        """
        report_path = self.settings.reports_dir / f"{result.analysis_id}{self.settings.csv_report_filename_suffix}"

        report_path.parent.mkdir(parents=True, exist_ok=True)

        with report_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "analysis_id",
                    "file_name",
                    "image_width",
                    "image_height",
                    "roof_count",
                    "estimated_residences",
                    "average_confidence",
                    "detection_id",
                    "bbox_x",
                    "bbox_y",
                    "bbox_width",
                    "bbox_height",
                    "bbox_area",
                    "confidence_score",
                    "source",
                    "status",
                    "created_at",
                ],
                delimiter=self.settings.csv_delimiter,
            )

            writer.writeheader()

            if not result.detections:
                writer.writerow(
                    {
                        "analysis_id": result.analysis_id,
                        "file_name": result.image_metadata.file_name,
                        "image_width": result.image_metadata.image_size.width,
                        "image_height": result.image_metadata.image_size.height,
                        "roof_count": result.roof_count,
                        "estimated_residences": result.estimated_residences,
                        "average_confidence": result.average_confidence,
                        "detection_id": "",
                        "bbox_x": "",
                        "bbox_y": "",
                        "bbox_width": "",
                        "bbox_height": "",
                        "bbox_area": "",
                        "confidence_score": "",
                        "source": "",
                        "status": result.status.value,
                        "created_at": result.created_at.isoformat(),
                    }
                )
                return report_path

            for detection in result.detections:
                writer.writerow(
                    {
                        "analysis_id": result.analysis_id,
                        "file_name": result.image_metadata.file_name,
                        "image_width": result.image_metadata.image_size.width,
                        "image_height": result.image_metadata.image_size.height,
                        "roof_count": result.roof_count,
                        "estimated_residences": result.estimated_residences,
                        "average_confidence": result.average_confidence,
                        "detection_id": detection.detection_id,
                        "bbox_x": detection.bbox.x,
                        "bbox_y": detection.bbox.y,
                        "bbox_width": detection.bbox.width,
                        "bbox_height": detection.bbox.height,
                        "bbox_area": detection.bbox.area,
                        "confidence_score": detection.confidence_score,
                        "source": detection.source.value,
                        "status": result.status.value,
                        "created_at": result.created_at.isoformat(),
                    }
                )

        return report_path
