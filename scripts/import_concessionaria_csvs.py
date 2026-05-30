from src.aerial_housing_detection.services.concessionaria_csv_importer import (
    ConcessionariaCsvImporter,
)


def main() -> None:
    importer = ConcessionariaCsvImporter()
    summary = importer.import_all()

    print("Importação real controlada concluída.")
    print(f"Banco local: {summary.database_path}")

    for item in summary.imported_files:
        print(
            f"{item.file_name} -> {item.table_name}: "
            f"{item.rows_imported} linhas"
        )


if __name__ == "__main__":
    main()
