import math

from src.monitoring.config import monitoring_settings
from src.monitoring.models import DriftReport


class DriftDetector:
    def __init__(self):
        self.psi_threshold = monitoring_settings.drift_psi_threshold
        self.min_samples = monitoring_settings.drift_min_samples

    def compute_psi(
        self,
        reference: list[float],
        current: list[float],
        bins: int = 10,
    ) -> float | None:
        if len(reference) < self.min_samples or len(current) < self.min_samples:
            return None

        breakpoints = self._quantile_breakpoints(reference, bins)
        ref_counts = self._bin_counts(reference, breakpoints, bins)
        cur_counts = self._bin_counts(current, breakpoints, bins)

        ref_total = len(reference)
        cur_total = len(current)

        eps = 1e-6
        psi = 0.0

        for i in range(bins):
            ref_pct = (ref_counts[i] / ref_total) + eps
            cur_pct = (cur_counts[i] / cur_total) + eps
            psi += (cur_pct - ref_pct) * math.log(cur_pct / ref_pct)

        return round(psi, 6)

    def detect(
        self,
        reference: list[float],
        current: list[float],
    ) -> DriftReport:
        psi = self.compute_psi(reference, current)

        if psi is None:
            return DriftReport(
                psi=None,
                threshold=self.psi_threshold,
                drifted=False,
                message=f"Amostras insuficientes (minimo: {self.min_samples})",
            )

        drifted = psi > self.psi_threshold

        if drifted:
            message = f"Drift detectado (PSI={psi:.4f} > {self.psi_threshold})"
        else:
            message = f"Sem drift (PSI={psi:.4f} <= {self.psi_threshold})"

        return DriftReport(
            psi=psi,
            threshold=self.psi_threshold,
            drifted=drifted,
            message=message,
        )

    @staticmethod
    def _quantile_breakpoints(data: list[float], bins: int) -> list[float]:
        sorted_data = sorted(data)
        n = len(sorted_data)
        return [
            sorted_data[int(n * i / bins)]
            for i in range(1, bins)
        ]

    @staticmethod
    def _bin_counts(
        data: list[float],
        breakpoints: list[float],
        bins: int,
    ) -> list[int]:
        counts = [0] * bins
        for val in data:
            placed = False
            for i, bp in enumerate(breakpoints):
                if val <= bp:
                    counts[i] += 1
                    placed = True
                    break
            if not placed:
                counts[-1] += 1
        return counts
