from src.aerial_housing_detection.ml.temporal_validation import (
    TransformerTemporalValidator,
)


def main() -> None:
    validator = TransformerTemporalValidator()
    result = validator.run()

    print("Validação temporal de Machine Learning executada com sucesso.")
    print(f"Dataset: {result.dataset_path}")
    print(f"Métricas: {result.output_path}")
    print(f"Total de linhas: {result.total_rows}")
    print(f"Total de meses: {result.total_months}")
    print(f"Meses avaliados: {', '.join(result.months)}")


if __name__ == "__main__":
    main()
