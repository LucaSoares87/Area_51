import random

from src.monitoring.drift_detector import DriftDetector


class TestDriftDetector:
    def setup_method(self):
        self.detector = DriftDetector()

    def test_no_drift_same_distribution(self):
        random.seed(42)
        reference = [random.uniform(0.5, 0.9) for _ in range(200)]
        current = [random.uniform(0.5, 0.9) for _ in range(200)]
        report = self.detector.detect(reference, current)
        assert report.drifted is False
        assert report.psi is not None

    def test_drift_different_distribution(self):
        random.seed(42)
        reference = [random.uniform(0.7, 0.95) for _ in range(200)]
        current = [random.uniform(0.1, 0.4) for _ in range(200)]
        report = self.detector.detect(reference, current)
        assert report.drifted is True
        assert report.psi > self.detector.psi_threshold

    def test_insufficient_samples(self):
        report = self.detector.detect([0.5] * 10, [0.5] * 10)
        assert report.drifted is False
        assert report.psi is None
        assert "insuficientes" in report.message

    def test_psi_returns_none_small_sample(self):
        result = self.detector.compute_psi([0.5] * 5, [0.5] * 5)
        assert result is None

    def test_psi_returns_float(self):
        random.seed(42)
        ref = [random.uniform(0.5, 0.9) for _ in range(200)]
        cur = [random.uniform(0.5, 0.9) for _ in range(200)]
        result = self.detector.compute_psi(ref, cur)
        assert isinstance(result, float)
        assert result >= 0
