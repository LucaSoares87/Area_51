from src.aerial_housing_detection.ml.baseline_model import (
    TransformerMlBaselineModel,
)


def main() -> None:
    model = TransformerMlBaselineModel()
    result = model.run()

    print("Baseline de Machine Learning executado com sucesso.")
    print(f"Dataset: {result.dataset_path}")
    print(f"Métricas: {result.metrics_path}")
    print(f"Ranking: {result.ranking_path}")
    print(f"Total de linhas: {result.total_rows}")
    print(f"Linhas positivas: {result.positive_rows}")
    print(f"Precision@10: {result.precision_at_10}")
    print(f"Precision@50: {result.precision_at_50}")
    print(f"Recall@50: {result.recall_at_50}")


if __name__ == "__main__":
    main()
