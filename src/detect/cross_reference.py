
import httpx

from src.detect.config import detect_settings
from src.detect.models import CrossRefResult, Detection


class CrossReferenceService:
    def __init__(self):
        self.enabled = detect_settings.cross_reference_enabled
        self.api_url = detect_settings.cross_reference_api_url
        self.timeout = detect_settings.cross_reference_timeout_seconds

    async def check_detections(
        self,
        detections: list[Detection],
    ) -> list[CrossRefResult]:
        if not self.enabled or not self.api_url:
            return [
                CrossRefResult(
                    detection_id=d.id,
                    matched=False,
                    source="disabled",
                )
                for d in detections
            ]

        results = []
        for detection in detections:
            result = await self._query(detection)
            results.append(result)
        return results

    async def _query(self, detection: Detection) -> CrossRefResult:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/lookup",
                    json={
                        "detection_id": detection.id,
                        "bbox": {
                            "x": detection.bbox.x,
                            "y": detection.bbox.y,
                            "width": detection.bbox.width,
                            "height": detection.bbox.height,
                        },
                        "confidence": detection.confidence,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    return CrossRefResult(
                        detection_id=detection.id,
                        matched=data.get("matched", False),
                        source="cadunico",
                        details=data.get("details"),
                    )

                return CrossRefResult(
                    detection_id=detection.id,
                    matched=False,
                    source="cadunico",
                    error=f"API retornou status {response.status_code}",
                )

        except httpx.TimeoutException:
            return CrossRefResult(
                detection_id=detection.id,
                matched=False,
                source="cadunico",
                error="Timeout na consulta",
            )
        except Exception as exc:
            return CrossRefResult(
                detection_id=detection.id,
                matched=False,
                source="cadunico",
                error=str(exc),
            )
