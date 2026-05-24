import argparse
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
EXPECTED_CLASSES = ("positives", "negatives", "uncertain")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit bootstrap image dataset.")
    parser.add_argument(
        "--dataset-dir",
        default="data/bootstrap",
        help="Path to bootstrap dataset directory.",
    )
    return parser.parse_args()


def list_images(path: Path) -> list[Path]:
    if not path.exists():
        return []

    return sorted(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS
    )


def audit_class(dataset_dir: Path, class_name: str) -> dict[str, object]:
    class_dir = dataset_dir / class_name
    images = list_images(class_dir)

    duplicated_names = sorted(
        name
        for name in {image.name for image in images}
        if sum(1 for image in images if image.name == name) > 1
    )

    return {
        "class_name": class_name,
        "path": str(class_dir),
        "exists": class_dir.exists(),
        "images": len(images),
        "duplicated_names": duplicated_names,
    }


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)

    print("Bootstrap dataset audit")
    print(f"dataset_dir={dataset_dir}")

    if not dataset_dir.exists():
        print(f"error=Dataset directory not found: {dataset_dir}")
        raise SystemExit(1)

    total_images = 0
    has_error = False

    for class_name in EXPECTED_CLASSES:
        report = audit_class(dataset_dir, class_name)
        total_images += int(report["images"])

        print(f"\nClass: {report['class_name']}")
        print(f"path={report['path']}")
        print(f"exists={report['exists']}")
        print(f"images={report['images']}")
        print(f"duplicated_names={len(report['duplicated_names'])}")

        if not report["exists"]:
            has_error = True

        if report["duplicated_names"]:
            has_error = True
            print("sample_duplicated_names:")
            for name in report["duplicated_names"][:10]:
                print(f"- {name}")

    print(f"\ntotal_images={total_images}")

    if has_error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
