import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from ultralytics import YOLO

DEFAULT_DATASET = Path("data/yolo/dataset.yaml")
DEFAULT_MODEL = "yolov8n.pt"
DEFAULT_PROJECT_DIR = Path("runs")
DEFAULT_RUN_NAME = "roof_detector_yolo"
DEFAULT_EXPORT_DIR = Path("models/yolo")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLO roof detector.")

    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET),
        help="Path to YOLO dataset YAML.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Base YOLO model. Example: yolov8n.pt, yolov8s.pt or local .pt path.",
    )
    parser.add_argument(
        "--project",
        default=str(DEFAULT_PROJECT_DIR),
        help="Ultralytics project output directory.",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_RUN_NAME,
        help="Training run name.",
    )
    parser.add_argument(
        "--export-dir",
        default=str(DEFAULT_EXPORT_DIR),
        help="Directory where best model and metadata will be copied.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Training image size.",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=8,
        help="Training batch size.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Training device. Use cpu, 0, 1, etc.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=25,
        help="Early stopping patience.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a short training for validation.",
    )

    return parser.parse_args()


def validate_dataset_yaml(dataset_path: Path) -> None:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset YAML not found: {dataset_path}")

    content = dataset_path.read_text(encoding="utf-8")

    required_terms = ["train:", "val:", "names:"]
    missing_terms = [term for term in required_terms if term not in content]

    if missing_terms:
        terms = ", ".join(missing_terms)
        raise ValueError(f"Dataset YAML is missing required terms: {terms}")


def resolve_epochs(args: argparse.Namespace) -> int:
    if args.quick:
        return min(args.epochs, 3)

    return args.epochs


def build_run_name(base_name: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}"


def print_training_summary(args: argparse.Namespace, run_name: str, epochs: int) -> None:
    separator = "=" * 72

    print(f"\n{separator}")
    print("YOLO roof detector training")
    print(separator)
    print(f"dataset={args.dataset}")
    print(f"model={args.model}")
    print(f"project={args.project}")
    print(f"name={run_name}")
    print(f"export_dir={args.export_dir}")
    print(f"epochs={epochs}")
    print(f"imgsz={args.imgsz}")
    print(f"batch={args.batch}")
    print(f"device={args.device}")
    print(f"patience={args.patience}")
    print(f"quick={args.quick}")
    print(separator)


def train_model(args: argparse.Namespace, run_name: str, epochs: int) -> None:
    model = YOLO(args.model)

    model.train(
        data=args.dataset,
        epochs=epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        name=run_name,
        project=args.project,
        patience=args.patience,
        workers=0,
        cache=False,
        amp=False,
        augment=True,
        verbose=True,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.2,
        scale=0.5,
        translate=0.2,
        degrees=10.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        perspective=0.001,
        weight_decay=0.001,
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=3,
        cos_lr=True,
        val=True,
        plots=True,
    )


def copy_training_artifacts(
    project_dir: Path,
    run_name: str,
    export_dir: Path,
    args: argparse.Namespace,
    epochs: int,
) -> None:
    run_dir = project_dir / run_name
    weights_dir = run_dir / "weights"
    best_model = weights_dir / "best.pt"
    last_model = weights_dir / "last.pt"

    export_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": args.dataset,
        "base_model": args.model,
        "project": str(project_dir),
        "run_name": run_name,
        "epochs": epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "patience": args.patience,
        "quick": args.quick,
        "best_model_source": str(best_model),
        "last_model_source": str(last_model),
    }

    if best_model.exists():
        best_destination = export_dir / "roof_detector_best.pt"
        shutil.copy2(best_model, best_destination)
        metadata["best_model_exported"] = str(best_destination)
        print(f"best_model_exported={best_destination}")
    else:
        metadata["best_model_exported"] = None
        print(f"warning=best model not found: {best_model}")

    if last_model.exists():
        last_destination = export_dir / "roof_detector_last.pt"
        shutil.copy2(last_model, last_destination)
        metadata["last_model_exported"] = str(last_destination)
        print(f"last_model_exported={last_destination}")
    else:
        metadata["last_model_exported"] = None
        print(f"warning=last model not found: {last_model}")

    metadata_path = export_dir / "roof_detector_training_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"metadata_exported={metadata_path}")


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    project_dir = Path(args.project)
    export_dir = Path(args.export_dir)

    validate_dataset_yaml(dataset_path)

    epochs = resolve_epochs(args)
    run_name = build_run_name(args.name)

    print_training_summary(args, run_name, epochs)
    train_model(args, run_name, epochs)
    copy_training_artifacts(project_dir, run_name, export_dir, args, epochs)

    print("training_completed=true")


if __name__ == "__main__":
    main()
