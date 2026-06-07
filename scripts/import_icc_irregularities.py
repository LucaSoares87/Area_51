from src.aerial_housing_detection.ml.icc_irregularity_labels import (
    IccIrregularityLabelImporter,
)


def main() -> None:
    importer = IccIrregularityLabelImporter()
    result = importer.run()

    print("Importação de irregularidades ICC executada com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Arquivo de origem: {result.source_path}")
    print(f"Linhas ICC importadas: {result.imported_rows}")
    print(f"Rótulos por transformador/mês gerados: {result.label_rows}")


if __name__ == "__main__":
    main()
