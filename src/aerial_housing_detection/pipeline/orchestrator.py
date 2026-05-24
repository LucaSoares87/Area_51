from pathlib import Path
from uuid import uuid4

from config.logging_config import get_logger
from src.aerial_housing_detection.bootstrap.bootstrap_filter import BootstrapFilter
from src.aerial_housing_detection.detection.image_preprocessor import ImagePreprocessor
from src.aerial_housing_detection.detection.post_processor import DetectionPostProcessor
from src.aerial_housing_detection.detection.roof_detector import RoofDetector
from src.aerial_housing_detection.domain.detection import DetectionResult
from src.aerial_housing_detection.domain.evidence import OperationalEvidence
from src.aerial_housing_detection.domain.exceptions import PipelineExecutionError
from src.aerial_housing_detection.domain.report import PipelineResult
from src.aerial_housing_detection.pipeline.pipeline_state import PipelineState
from src.aerial_housing_detection.pipeline.step_registry import (
    PipelineStep,
    PipelineStepExecution,
    PipelineStepName,
    StepRegistry,
)
from src.aerial_housing_detection.reports.evidence_generator import EvidenceGenerator
from src.aerial_housing_detection.reports.map_renderer import MapRenderer
from src.aerial_housing_detection.reports.report_generator import ReportGenerator

logger = get_logger(__name__)


class DetectionPipeline:
    """Coordinates the aerial housing detection pipeline."""

    def __init__(
        self,
        image_preprocessor: ImagePreprocessor | None = None,
        roof_detector: RoofDetector | None = None,
        post_processor: DetectionPostProcessor | None = None,
        report_generator: ReportGenerator | None = None,
        map_renderer: MapRenderer | None = None,
        bootstrap_filter: BootstrapFilter | None = None,
        evidence_generator: EvidenceGenerator | None = None,
    ) -> None:
        """Initialize pipeline dependencies."""
        self.image_preprocessor = image_preprocessor or ImagePreprocessor()
        self.roof_detector = roof_detector or RoofDetector()
        self.post_processor = post_processor or DetectionPostProcessor()
        self.report_generator = report_generator or ReportGenerator()
        self.map_renderer = map_renderer or MapRenderer()
        self.bootstrap_filter = bootstrap_filter or BootstrapFilter()
        self.evidence_generator = evidence_generator or EvidenceGenerator()

        self._last_executions: list[PipelineStepExecution] = []
        self._last_raw_detection_count = 0
        self._last_filtered_detection_count = 0
        self.last_evidence_path: Path | None = None

    @property
    def last_executions(self) -> list[PipelineStepExecution]:
        """Return metadata from the last pipeline execution."""
        return self._last_executions

    def run_detection(self, image_path: Path) -> DetectionResult:
        """Run only the detection stage."""
        state = PipelineState(
            analysis_id=uuid4().hex,
            image_path=image_path,
        )

        self._reset_execution_counters()

        registry = StepRegistry(
            steps=[
                PipelineStep(
                    name=PipelineStepName.PREPROCESS_IMAGE,
                    handler=self._preprocess_image,
                ),
                PipelineStep(
                    name=PipelineStepName.DETECT_ROOFS,
                    handler=self._detect_roofs,
                ),
                PipelineStep(
                    name=PipelineStepName.POST_PROCESS,
                    handler=self._post_process,
                ),
            ]
        )

        try:
            state.mark_processing()
            self._last_executions = registry.run(state)
            state.mark_completed()

            logger.info(
                "pipeline_detection_completed",
                analysis_id=state.analysis_id,
                roof_count=len(state.final_detections),
                raw_detection_count=self._last_raw_detection_count,
                filtered_detection_count=self._last_filtered_detection_count,
            )

            return state.to_detection_result()

        except Exception as exc:
            state.mark_failed(str(exc))
            logger.error(
                "pipeline_detection_failed",
                analysis_id=state.analysis_id,
                error=str(exc),
            )
            raise PipelineExecutionError(str(exc)) from exc

    def run(self, image_path: Path) -> PipelineResult:
        """Run detection and generate output files."""
        detection_result = self.run_detection(image_path)
        csv_report_path = self.report_generator.generate_csv(detection_result)
        html_map_path = self.map_renderer.render_html(detection_result)

        evidence = self._build_operational_evidence(
            image_path=image_path,
            detection_result=detection_result,
            csv_report_path=csv_report_path,
            html_map_path=html_map_path,
        )
        self.last_evidence_path = self.evidence_generator.generate_json(evidence)

        return PipelineResult(
            analysis_id=detection_result.analysis_id,
            estimated_residences=detection_result.estimated_residences,
            roof_count=detection_result.roof_count,
            confidence_score=detection_result.average_confidence,
            csv_report_path=csv_report_path,
            html_map_path=html_map_path,
        )

    def _reset_execution_counters(self) -> None:
        """Reset counters used to create operational evidence."""
        self._last_raw_detection_count = 0
        self._last_filtered_detection_count = 0
        self.last_evidence_path = None

    def _build_operational_evidence(
        self,
        image_path: Path,
        detection_result: DetectionResult,
        csv_report_path: Path,
        html_map_path: Path,
    ) -> OperationalEvidence:
        """Build operational evidence from the latest pipeline execution."""
        return OperationalEvidence(
            analysis_id=detection_result.analysis_id,
            image_path=image_path,
            raw_detection_count=self._last_raw_detection_count,
            filtered_detection_count=self._last_filtered_detection_count,
            final_detection_count=detection_result.roof_count,
            estimated_residences=detection_result.estimated_residences,
            average_confidence=detection_result.average_confidence,
            status=detection_result.status.value,
            csv_report_path=csv_report_path,
            html_map_path=html_map_path,
        )

    def _preprocess_image(self, state: PipelineState) -> None:
        """Run image preprocessing step."""
        state.image_metadata = self.image_preprocessor.preprocess(state.image_path)

    def _detect_roofs(self, state: PipelineState) -> None:
        """Run roof detection step."""
        metadata = state.require_metadata()
        state.raw_detections = self.roof_detector.detect(state.image_path, metadata)
        self._last_raw_detection_count = len(state.raw_detections)

    def _post_process(self, state: PipelineState) -> None:
        """Run bootstrap filtering and detection post-processing."""
        filtered_detections = self.bootstrap_filter.filter(state.raw_detections)
        self._last_filtered_detection_count = len(filtered_detections)
        state.final_detections = self.post_processor.process(filtered_detections)
