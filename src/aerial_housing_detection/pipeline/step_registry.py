from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from time import perf_counter

from src.aerial_housing_detection.pipeline.pipeline_state import PipelineState


class PipelineStepName(str, Enum):
    """Names of pipeline execution steps."""

    PREPROCESS_IMAGE = "preprocess_image"
    DETECT_ROOFS = "detect_roofs"
    POST_PROCESS = "post_process"


PipelineStepHandler = Callable[[PipelineState], None]


@dataclass(frozen=True)
class PipelineStep:
    """Represents one executable pipeline step."""

    name: PipelineStepName
    handler: PipelineStepHandler


@dataclass(frozen=True)
class PipelineStepExecution:
    """Represents execution metadata for one pipeline step."""

    name: PipelineStepName
    elapsed_seconds: float


class StepRegistry:
    """Executes registered pipeline steps in order."""

    def __init__(self, steps: list[PipelineStep]) -> None:
        """Initialize registry.

        Args:
            steps: Pipeline steps in execution order.
        """
        self.steps = steps

    def run(self, state: PipelineState) -> list[PipelineStepExecution]:
        """Run all registered steps.

        Args:
            state: Pipeline state.

        Returns:
            List of step execution metadata.
        """
        executions: list[PipelineStepExecution] = []

        for step in self.steps:
            started_at = perf_counter()
            step.handler(state)
            elapsed = perf_counter() - started_at
            executions.append(
                PipelineStepExecution(
                    name=step.name,
                    elapsed_seconds=round(elapsed, 6),
                )
            )

        return executions
