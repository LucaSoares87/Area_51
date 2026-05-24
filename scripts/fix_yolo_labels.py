import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fix YOLO label coordinates.")
    parser.add_argument(
        "--dataset-dir",
        default="data/yolo",
        help="Path to YOLO dataset directory.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Without this flag, runs in dry-run mode.",
    )
    return parser.parse_args()


def clamp(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def fix_line(line: str) -> tuple[str, bool]:
    parts = line.split()

    if len(parts) != 5:
        return line, False

    class_id = parts[0]

    try:
        coords = [float(value) for value in parts[1:]]
    except ValueError:
        return line, False

    fixed_coords = [clamp(value) for value in coords]
    changed = fixed_coords != coords

    fixed_line = (
        f"{class_id} "
        f"{fixed_coords[0]:.6f} "
        f"{fixed_coords[1]:.6f} "
        f"{fixed_coords[2]:.6f} "
        f"{fixed_coords[3]:.6f}"
    )

    return fixed_line, changed


def fix_label_file(label_path: Path, apply: bool) -> bool:
    original_lines = label_path.read_text(encoding="utf-8").splitlines()

    fixed_lines: list[str] = []
    changed = False

    for line in original_lines:
        fixed_line, line_changed = fix_line(line)
        fixed_lines.append(fixed_line)
        changed = changed or line_changed

    if changed and apply:
        backup_path = label_path.with_suffix(label_path.suffix + ".bak")
        if not backup_path.exists():
            shutil.copy2(label_path, backup_path)

        label_path.write_text("\n".join(fixed_lines) + "\n", encoding="utf-8")

    return changed


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)

    if not dataset_dir.exists():
        print(f"error=Dataset directory not found: {dataset_dir}")
        raise SystemExit(1)

    label_files = sorted((dataset_dir / "labels").rglob("*.txt"))

    changed_files: list[Path] = []

    for label_path in label_files:
        if fix_label_file(label_path, apply=args.apply):
            changed_files.append(label_path)

    mode = "apply" if args.apply else "dry-run"

    print("YOLO label fix")
    print(f"dataset_dir={dataset_dir}")
    print(f"mode={mode}")
    print(f"changed_files={len(changed_files)}")

    for path in changed_files:
        print(f"- {path}")

    if changed_files and not args.apply:
        print("Run again with --apply to write changes.")


if __name__ == "__main__":
    main()
