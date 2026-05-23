from pathlib import Path
from uuid import uuid4

from config.logging_config import get_logger
from src.aerial_housing_detection.detection.image_preprocessor import ImagePreprocessor
from src.aerial_housing_detection.detection.post_processor import DetectionPostProcessor
from src.aerial_housing_detection.detection.roof_detector import RoofDetector
from src.aerial_housing_detection.domain.detection import DetectionResult
from src.aerial_housing_detection.domain.exceptions import PipelineExecutionError
from src.aerial_housing_detection.domain.report import PipelineResult
from src.aerial_housing_detection.pipeline.pipeline_state import PipelineState
from src.aerial_housing_detection.pipeline.step_registry import (
    PipelineStep,
    PipelineStepExecution,
    PipelineStepName,
    StepRegistry,
)
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
    ) -> None:
        """Initialize pipeline dependencies.

        Args:
            image_preprocessor: Optional image preprocessor.
            roof_detector: Optional roof detector.
            post_processor: Optional detection post processor.
            report_generator: Optional report generator.
            map_renderer: Optional map renderer.
        """
        self.image_preprocessor = image_preprocessor or ImagePreprocessor()
        self.roof_detector = roof_detector or RoofDetector()
        self.post_processor = post_processor or DetectionPostProcessor()
        self.report_generator = report_generator or ReportGenerator()
        self.map_renderer = map_renderer or MapRenderer()
        self._last_executions: list[PipelineStepExecution] = []

    @property
    def last_executions(self) -> list[PipelineStepExecution]:
        """Return metadata from the last pipeline execution."""
        return self._last_executions

    def run_detection(self, image_path: Path) -> DetectionResult:
        """Run only the detection stage.

        Args:
            image_path: Path to aerial image.

        Returns:
            Detection result.

        Raises:
            PipelineExecutionError: If the pipeline cannot complete.
        """
        state = PipelineState(
            analysis_id=uuid4().hex,
            image_path=image_path,
        )

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
        """Run detection and generate output files.

        Args:
            image_path: Path to aerial image.

        Returns:
            Pipeline result with generated report paths.

        Raises:
            PipelineExecutionError: If the pipeline cannot complete.
        """
        detection_result = self.run_detection(image_path)
        csv_report_path = self.report_generator.generate_csv(detection_result)
        html_map_path = self.map_renderer.render_html(detection_result)

        return PipelineResult(
            analysis_id=detection_result.analysis_id,
            estimated_residences=detection_result.estimated_residences,
            roof_count=detection_result.roof_count,
            confidence_score=detection_result.average_confidence,
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

    def _post_process(self, state: PipelineState) -> None:
        """Run detection post-processing step."""
        state.final_detections = self.post_processor.process(state.raw_detections)
