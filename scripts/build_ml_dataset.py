from src.aerial_housing_detection.ml.dataset_builder import (
    TransformerMlDatasetBuilder,
)


def main() -> None:
    builder = TransformerMlDatasetBuilder()
    result = builder.build()

    print("Dataset de Machine Learning criado com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Arquivo gerado: {result.output_path}")
    print(f"Linhas geradas: {result.rows_created}")
    print(f"Colunas: {len(result.columns)}")


if __name__ == "__main__":
    main()