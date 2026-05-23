import random
import uuid
from pathlib import Path

from src.detect.config import detect_settings
from src.detect.models import (
    BoundingBox,
    Detection,
    DetectionStatus,
    ObjectClass,
    SourceType,
)


class InferenceEngine:
    def __init__(self):
        self.mock = detect_settings.mock_inference
        self.confidence_threshold = detect_settings.confidence_threshold
        self.nms_iou_threshold = detect_settings.nms_iou_threshold
        self.spacenet_path = Path(detect_settings.spacenet_model_path)
        self.bootstrap_path = Path(detect_settings.bootstrap_model_path)
        self._spacenet_model = None
        self._bootstrap_model = None

    def load_models(self):
        if self.mock:
            return
        self._spacenet_model = self._load_torch_model(self.spacenet_path)
        self._bootstrap_model = self._load_torch_model(self.bootstrap_path)

    def _load_torch_model(self, path):
        import torch
        if not path.exists():
            raise FileNotFoundError(f"Modelo nao encontrado: {path}")
        model = torch.load(path, map_location="cpu")
        model.eval()
        return model

    def predict(self, image_path):
        if self.mock:
            return self._mock_predict(image_path)
        return self._real_predict(image_path)

    def _real_predict(self, image_path):
        raise NotImplementedError("Inferencia real sera implementada com modelo treinado")

    def _mock_predict(self, image_path):
        num_detections = random.randint(0, 5)
        detections = []
        mock_classes = list(ObjectClass)

        for _ in range(num_detections):
            confidence = random.uniform(0.3, 0.98)
            if confidence < self.confidence_threshold:
                continue

            detections.append(
                Detection(
                    detection_id=uuid.uuid4().hex[:12],
                    object_class=random.choice(mock_classes),
                    confidence=round(confidence, 4),
                    bbox=BoundingBox(
                        x=float(random.randint(0, 800)),
                        y=float(random.randint(0, 800)),
                        width=float(random.randint(30, 200)),
                        height=float(random.randint(30, 200)),
                    ),
                    source=SourceType.CAMERA,
                    status=DetectionStatus.RAW,
                    metadata={"source_file": image_path.name},
                )
            )

        return self._apply_nms(detections)

    def _apply_nms(self, detections):
        if len(detections) <= 1:
            return detections

        detections.sort(key=lambda d: d.confidence, reverse=True)
        kept = []

        for det in detections:
            overlaps = False
            for k in kept:
                if det.bbox is not None and k.bbox is not None:
                    if det.bbox.iou(k.bbox) > self.nms_iou_threshold:
                        overlaps = True
                        break
            if not overlaps:
                kept.append(det)

        return kept
