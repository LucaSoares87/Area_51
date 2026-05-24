import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect local YOLO model artifacts.")
    parser.add_argument(
        "--models-dir",
        default="models/yolo",
        help="Directory containing exported model artifacts.",
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory containing YOLO training runs.",
    )
    return parser.parse_args()


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def list_files(path: Path, pattern: str) -> list[Path]:
    if not path.exists():
        return []
    return sorted(path.rglob(pattern))


def print_model_files(models_dir: Path) -> None:
    print("Model artifacts")
    print(f"models_dir={models_dir}")

    model_files = []
    for pattern in ("*.pt", "*.onnx", "*.engine", "*.torchscript", "*.tflite", "*.pb"):
        model_files.extend(list_files(models_dir, pattern))

    if not model_files:
        print("model_files=0")
        return

    print(f"model_files={len(model_files)}")
    for path in model_files:
        print(f"- {path} size_mb={file_size_mb(path):.2f}")


def print_metadata(models_dir: Path) -> None:
    metadata_files = list_files(models_dir, "*.json")

    if not metadata_files:
        print("metadata_files=0")
        return

    print(f"metadata_files={len(metadata_files)}")

    for path in metadata_files:
        print(f"- {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("  invalid_json=true")
            continue

        for key in ("created_at", "dataset", "base_model", "run_name", "epochs", "imgsz"):
            if key in data:
                print(f"  {key}={data[key]}")


def print_runs(runs_dir: Path) -> None:
    print("Training runs")
    print(f"runs_dir={runs_dir}")

    if not runs_dir.exists():
        print("runs=0")
        return

    run_dirs = sorted([path for path in runs_dir.iterdir() if path.is_dir()])

    print(f"runs={len(run_dirs)}")
    for path in run_dirs[-10:]:
        print(f"- {path}")


def main() -> None:
    args = parse_args()

    models_dir = Path(args.models_dir)
    runs_dir = Path(args.runs_dir)

    print_model_files(models_dir)
    print_metadata(models_dir)
    print_runs(runs_dir)


if __name__ == "__main__":
    main()
