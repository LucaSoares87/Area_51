import argparse
from collections import Counter
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit YOLO dataset structure.")
    parser.add_argument(
        "--dataset-dir",
        default="data/yolo",
        help="Path to YOLO dataset directory.",
    )
    return parser.parse_args()


def list_images(path: Path) -> dict[str, Path]:
    if not path.exists():
        return {}

    return {
        image_path.stem: image_path
        for image_path in path.rglob("*")
        if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS
    }


def list_labels(path: Path) -> dict[str, Path]:
    if not path.exists():
        return {}

    return {label_path.stem: label_path for label_path in path.rglob("*.txt") if label_path.is_file()}


def validate_label_file(path: Path) -> list[str]:
    errors: list[str] = []

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        errors.append("empty_label")
        return errors

    for line_number, line in enumerate(content.splitlines(), start=1):
        parts = line.split()

        if len(parts) != 5:
            errors.append(f"line_{line_number}:invalid_yolo_column_count")
            continue

        class_id_raw, *coords_raw = parts

        if not class_id_raw.isdigit():
            errors.append(f"line_{line_number}:invalid_class_id")
            continue

        try:
            coords = [float(value) for value in coords_raw]
        except ValueError:
            errors.append(f"line_{line_number}:invalid_coordinate")
            continue

        for coord in coords:
            if coord < 0 or coord > 1:
                errors.append(f"line_{line_number}:coordinate_out_of_range")
                break

        width = coords[2]
        height = coords[3]

        if width <= 0 or height <= 0:
            errors.append(f"line_{line_number}:invalid_box_size")

    return errors


def audit_split(dataset_dir: Path, split: str) -> dict[str, object]:
    images_dir = dataset_dir / "images" / split
    labels_dir = dataset_dir / "labels" / split

    images = list_images(images_dir)
    labels = list_labels(labels_dir)

    image_names = set(images)
    label_names = set(labels)

    images_without_labels = sorted(image_names - label_names)
    labels_without_images = sorted(label_names - image_names)

    label_errors: dict[str, list[str]] = {}
    class_counter: Counter[str] = Counter()
    object_count = 0

    for _label_name, label_path in labels.items():
        errors = validate_label_file(label_path)
        if errors:
            label_errors[str(label_path)] = errors
            continue

        for line in label_path.read_text(encoding="utf-8").strip().splitlines():
            class_id = line.split()[0]
            class_counter[class_id] += 1
            object_count += 1

    return {
        "split": split,
        "images": len(images),
        "labels": len(labels),
        "objects": object_count,
        "images_without_labels": images_without_labels,
        "labels_without_images": labels_without_images,
        "invalid_labels": label_errors,
        "class_distribution": dict(class_counter),
    }


def print_split_report(report: dict[str, object]) -> None:
    print(f"\nSplit: {report['split']}")
    print(f"images={report['images']}")
    print(f"labels={report['labels']}")
    print(f"objects={report['objects']}")
    print(f"class_distribution={report['class_distribution']}")

    images_without_labels = report["images_without_labels"]
    labels_without_images = report["labels_without_images"]
    invalid_labels = report["invalid_labels"]

    print(f"images_without_labels={len(images_without_labels)}")
    print(f"labels_without_images={len(labels_without_images)}")
    print(f"invalid_labels={len(invalid_labels)}")

    if images_without_labels:
        print("sample_images_without_labels:")
        for item in images_without_labels[:10]:
            print(f"- {item}")

    if labels_without_images:
        print("sample_labels_without_images:")
        for item in labels_without_images[:10]:
            print(f"- {item}")

    if invalid_labels:
        print("sample_invalid_labels:")
        for path, errors in list(invalid_labels.items())[:10]:
            print(f"- {path}: {errors}")


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)

    if not dataset_dir.exists():
        print(f"error=Dataset directory not found: {dataset_dir}")
        raise SystemExit(1)

    train_report = audit_split(dataset_dir, "train")
    val_report = audit_split(dataset_dir, "val")

    print("YOLO dataset audit")
    print(f"dataset_dir={dataset_dir}")

    print_split_report(train_report)
    print_split_report(val_report)

    train_images = set(list_images(dataset_dir / "images" / "train"))
    val_images = set(list_images(dataset_dir / "images" / "val"))
    duplicated = sorted(train_images.intersection(val_images))

    print("\nCross split")
    print(f"duplicated_image_names_between_train_and_val={len(duplicated)}")

    if duplicated:
        for item in duplicated[:10]:
            print(f"- {item}")

    total_invalid = len(train_report["invalid_labels"]) + len(val_report["invalid_labels"])
    total_missing = (
        len(train_report["images_without_labels"])
        + len(train_report["labels_without_images"])
        + len(val_report["images_without_labels"])
        + len(val_report["labels_without_images"])
    )

    if total_invalid or total_missing or duplicated:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
