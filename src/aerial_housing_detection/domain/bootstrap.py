from dataclasses import dataclass
from enum import StrEnum


class BootstrapLabel(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class BootstrapClassification:
    label: BootstrapLabel
    confidence_score: float
    reason: str = ""

    @property
    def is_positive(self) -> bool:
        return self.label == BootstrapLabel.POSITIVE

    @property
    def is_negative(self) -> bool:
        return self.label == BootstrapLabel.NEGATIVE

    @property
    def is_uncertain(self) -> bool:
        return self.label == BootstrapLabel.UNCERTAIN
