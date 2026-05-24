import argparse
import shutil
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove duplicated YOLO samples between train and val."
    )
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


def list_images(path: Path) -> dict[str, Path]:
    if not path.exists():
        return {}

    return {
        image_path.stem: image_path
        for image_path in path.rglob("*")
        if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS
    }


def find_label(labels_dir: Path, stem: str) -> Path | None:
    label_path = labels_dir / f"{stem}.txt"
    if label_path.exists():
        return label_path
    return None


def move_to_backup(path: Path, backup_root: Path, dataset_dir: Path) -> Path:
    relative_path = path.relative_to(dataset_dir)
    backup_path = backup_root / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(backup_path))
    return backup_path


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)

    if not dataset_dir.exists():
        print(f"error=Dataset directory not found: {dataset_dir}")
        raise SystemExit(1)

    train_images_dir = dataset_dir / "images" / "train"
    val_images_dir = dataset_dir / "images" / "val"
    val_labels_dir = dataset_dir / "labels" / "val"
    backup_root = dataset_dir / "_backup_removed_duplicates"

    train_images = list_images(train_images_dir)
    val_images = list_images(val_images_dir)

    duplicated = sorted(set(train_images).intersection(val_images))

    print("YOLO split duplicate fix")
    print(f"dataset_dir={dataset_dir}")
    print(f"mode={'apply' if args.apply else 'dry-run'}")
    print(f"duplicated_samples={len(duplicated)}")

    for stem in duplicated:
        image_path = val_images[stem]
        label_path = find_label(val_labels_dir, stem)

        print(f"- {stem}")
        print(f"  val_image={image_path}")
        if label_path:
            print(f"  val_label={label_path}")

        if args.apply:
            image_backup_path = move_to_backup(image_path, backup_root, dataset_dir)
            print(f"  image_backup={image_backup_path}")

            if label_path:
                label_backup_path = move_to_backup(label_path, backup_root, dataset_dir)
                print(f"  label_backup={label_backup_path}")

    if duplicated and not args.apply:
        print("Run again with --apply to move duplicated val samples to backup.")


if __name__ == "__main__":
    main()
