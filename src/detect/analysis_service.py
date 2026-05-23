import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.detect.config import detect_settings
from src.detect.cross_reference import CrossReferenceService
from src.detect.image_processor import ImageProcessor
from src.detect.inference import InferenceEngine
from src.detect.models import AnalysisResult, AnalysisStatus


class AnalysisService:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.engine = InferenceEngine()
        self.cross_ref = CrossReferenceService()
        self.results_dir = detect_settings.results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._analyses: dict[str, AnalysisResult] = {}

    async def analyze(
        self,
        file_path: Path,
        requester: str,
        cross_reference: bool = False,
    ) -> AnalysisResult:
        analysis_id = uuid.uuid4().hex[:16]

        errors = self.image_processor.validate(file_path)
        if errors:
            result = AnalysisResult(
                id=analysis_id,
                status=AnalysisStatus.FAILED,
                requester=requester,
                source_file=file_path.name,
                errors=errors,
                created_at=datetime.now(UTC),
            )
            self._analyses[analysis_id] = result
            return result

        metadata = self.image_processor.extract_metadata(file_path)
        detections = self.engine.predict(file_path)

        cross_refs = None
        if cross_reference and detect_settings.cross_reference_enabled:
            cross_refs = await self.cross_ref.check_detections(detections)

        result = AnalysisResult(
            id=analysis_id,
            status=AnalysisStatus.COMPLETED,
            requester=requester,
            source_file=file_path.name,
            metadata=metadata,
            detections=detections,
            cross_references=cross_refs,
            total_detections=len(detections),
            created_at=datetime.now(UTC),
        )
        self._analyses[analysis_id] = result
        return result

    async def analyze_batch(
        self,
        file_paths: list[Path],
        requester: str,
    ) -> list[AnalysisResult]:
        max_batch = detect_settings.batch_max_images
        if len(file_paths) > max_batch:
            raise ValueError(
                f"Batch excede o limite de {max_batch} imagens"
            )

        results = []
        for path in file_paths:
            result = await self.analyze(path, requester)
            results.append(result)
        return results

    def get_result(self, analysis_id: str) -> AnalysisResult | None:
        return self._analyses.get(analysis_id)

    def list_results(
        self,
        requester: str | None = None,
        limit: int = 50,
    ) -> list[AnalysisResult]:
        results = list(self._analyses.values())
        if requester:
            results = [r for r in results if r.requester == requester]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]
