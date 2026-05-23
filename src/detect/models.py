"""
Modelos de dados do modulo de deteccao aerea.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


class ObjectClass(str, Enum):
    AIRCRAFT = "aircraft"
    HELICOPTER = "helicopter"
    DRONE = "drone"
    BIRD = "bird"
    BALLOON = "balloon"
    SATELLITE = "satellite"
    MISSILE = "missile"
    UNKNOWN = "unknown"


class DetectionStatus(str, Enum):
    RAW = "raw"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    TRACKING = "tracking"
    LOST = "lost"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SourceType(str, Enum):
    RADAR = "radar"
    CAMERA = "camera"
    INFRARED = "infrared"
    LIDAR = "lidar"
    ADS_B = "ads_b"
    ACOUSTIC = "acoustic"
    FUSED = "fused"


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def area(self) -> float:
        return self.width * self.height

    def iou(self, other: "BoundingBox") -> float:
        inter_x1 = max(self.x, other.x)
        inter_y1 = max(self.y, other.y)
        inter_x2 = min(self.x2, other.x2)
        inter_y2 = min(self.y2, other.y2)

        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        union_area = self.area + other.area - inter_area

        if union_area == 0:
            return 0.0

        return inter_area / union_area

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "BoundingBox":
        return cls(x=data["x"], y=data["y"], width=data["width"], height=data["height"])


@dataclass
class GeoPosition:
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    heading_deg: float | None = None
    speed_knots: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "heading_deg": self.heading_deg,
            "speed_knots": self.speed_knots,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeoPosition":
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"],
            altitude_m=data.get("altitude_m", 0.0),
            heading_deg=data.get("heading_deg"),
            speed_knots=data.get("speed_knots"),
        )


@dataclass
class Detection:
    detection_id: str = field(default_factory=lambda: uuid4().hex)
    object_class: ObjectClass = ObjectClass.UNKNOWN
    confidence: float = 0.0
    bbox: BoundingBox | None = None
    position: GeoPosition | None = None
    source: SourceType = SourceType.CAMERA
    status: DetectionStatus = DetectionStatus.RAW
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    frame_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_confirmed(self) -> bool:
        return self.status == DetectionStatus.CONFIRMED

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.85

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "object_class": self.object_class.value,
            "confidence": self.confidence,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "position": self.position.to_dict() if self.position else None,
            "source": self.source.value,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "frame_index": self.frame_index,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Detection":
        return cls(
            detection_id=data.get("detection_id", uuid4().hex),
            object_class=ObjectClass(data.get("object_class", "unknown")),
            confidence=data.get("confidence", 0.0),
            bbox=BoundingBox.from_dict(data["bbox"]) if data.get("bbox") else None,
            position=GeoPosition.from_dict(data["position"]) if data.get("position") else None,
            source=SourceType(data.get("source", "camera")),
            status=DetectionStatus(data.get("status", "raw")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc),
            frame_index=data.get("frame_index"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TrackedObject:
    track_id: str = field(default_factory=lambda: uuid4().hex)
    object_class: ObjectClass = ObjectClass.UNKNOWN
    detections: list[Detection] = field(default_factory=list)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: DetectionStatus = DetectionStatus.TRACKING
    severity: Severity = Severity.LOW
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    @property
    def avg_confidence(self) -> float:
        if not self.detections:
            return 0.0
        return sum(d.confidence for d in self.detections) / len(self.detections)

    @property
    def last_detection(self) -> Detection | None:
        return self.detections[-1] if self.detections else None

    @property
    def last_position(self) -> GeoPosition | None:
        if not self.detections:
            return None
        for det in reversed(self.detections):
            if det.position is not None:
                return det.position
        return None

    @property
    def duration_seconds(self) -> float:
        return (self.last_seen - self.first_seen).total_seconds()

    def add_detection(self, detection: Detection) -> None:
        self.detections.append(detection)
        self.last_seen = detection.timestamp
        if detection.confidence > 0.5 and detection.object_class != ObjectClass.UNKNOWN:
            self.object_class = detection.object_class

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "object_class": self.object_class.value,
            "detections": [d.to_dict() for d in self.detections],
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "status": self.status.value,
            "severity": self.severity.value,
            "avg_confidence": self.avg_confidence,
            "detection_count": self.detection_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrackedObject":
        obj = cls(
            track_id=data.get("track_id", uuid4().hex),
            object_class=ObjectClass(data.get("object_class", "unknown")),
            first_seen=datetime.fromisoformat(data["first_seen"]) if data.get("first_seen") else datetime.now(timezone.utc),
            last_seen=datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else datetime.now(timezone.utc),
            status=DetectionStatus(data.get("status", "tracking")),
            severity=Severity(data.get("severity", "low")),
            metadata=data.get("metadata", {}),
        )
        for d in data.get("detections", []):
            obj.detections.append(Detection.from_dict(d))
        return obj


@dataclass
class InferenceResult:
    request_id: str = field(default_factory=lambda: uuid4().hex)
    model_name: str = ""
    model_version: str = ""
    detections: list[Detection] = field(default_factory=list)
    inference_time_ms: float = 0.0
    frame_width: int = 0
    frame_height: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_detections(self) -> int:
        return len(self.detections)

    @property
    def confirmed_detections(self) -> list[Detection]:
        return [d for d in self.detections if d.is_confirmed]

    @property
    def high_confidence_detections(self) -> list[Detection]:
        return [d for d in self.detections if d.is_high_confidence]

    def filter_by_class(self, obj_class: ObjectClass) -> list[Detection]:
        return [d for d in self.detections if d.object_class == obj_class]

    def filter_by_min_confidence(self, threshold: float) -> list[Detection]:
        return [d for d in self.detections if d.confidence >= threshold]

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "detections": [d.to_dict() for d in self.detections],
            "inference_time_ms": self.inference_time_ms,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "timestamp": self.timestamp.isoformat(),
            "total_detections": self.total_detections,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InferenceResult":
        result = cls(
            request_id=data.get("request_id", uuid4().hex),
            model_name=data.get("model_name", ""),
            model_version=data.get("model_version", ""),
            inference_time_ms=data.get("inference_time_ms", 0.0),
            frame_width=data.get("frame_width", 0),
            frame_height=data.get("frame_height", 0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(timezone.utc),
            metadata=data.get("metadata", {}),
        )
        for d in data.get("detections", []):
            result.detections.append(Detection.from_dict(d))
        return result


@dataclass
class BBox:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "BBox":
        return cls(x=data["x"], y=data["y"], width=data["width"], height=data["height"])


@dataclass
class ImageMetadata:
    filename: str = ""
    width: int = 0
    height: int = 0
    channels: int = 3
    format: str = ""
    size_bytes: int = 0
    hash_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "channels": self.channels,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "hash_sha256": self.hash_sha256,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageMetadata":
        return cls(
            filename=data.get("filename", ""),
            width=data.get("width", 0),
            height=data.get("height", 0),
            channels=data.get("channels", 3),
            format=data.get("format", ""),
            size_bytes=data.get("size_bytes", 0),
            hash_sha256=data.get("hash_sha256", ""),
        )


@dataclass
class Tile:
    index: int = 0
    bbox: BBox = field(default_factory=BBox)
    file_path: Path = field(default_factory=Path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "bbox": self.bbox.to_dict(),
            "file_path": str(self.file_path),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tile":
        return cls(
            index=data.get("index", 0),
            bbox=BBox.from_dict(data["bbox"]) if data.get("bbox") else BBox(),
            file_path=Path(data.get("file_path", "")),
        )
@dataclass
class CrossRefResult:
    detection_id: str = ""
    matched: bool = False
    source: str = ""
    details: Any = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "matched": self.matched,
            "source": self.source,
            "details": self.details,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CrossRefResult":
        return cls(
            detection_id=data.get("detection_id", ""),
            matched=data.get("matched", False),
            source=data.get("source", ""),
            details=data.get("details"),
            error=data.get("error", ""),
        )

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AnalysisResult:
    id: str = ""
    status: AnalysisStatus = AnalysisStatus.PENDING
    requester: str = ""
    source_file: str = ""
    errors: list[str] = field(default_factory=list)
    metadata: Any = None
    detections: list[Detection] = field(default_factory=list)
    cross_references: list[CrossRefResult] | None = None
    total_detections: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "requester": self.requester,
            "source_file": self.source_file,
            "errors": self.errors,
            "metadata": self.metadata,
            "detections": [d.to_dict() for d in self.detections],
            "cross_references": [c.to_dict() for c in self.cross_references] if self.cross_references else None,
            "total_detections": self.total_detections,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        return cls(
            id=data.get("id", ""),
            status=AnalysisStatus(data.get("status", "pending")),
            requester=data.get("requester", ""),
            source_file=data.get("source_file", ""),
            errors=data.get("errors", []),
            metadata=data.get("metadata"),
            detections=[Detection.from_dict(d) for d in data.get("detections", [])],
            cross_references=[CrossRefResult.from_dict(c) for c in data["cross_references"]] if data.get("cross_references") else None,
            total_detections=data.get("total_detections", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
        )
