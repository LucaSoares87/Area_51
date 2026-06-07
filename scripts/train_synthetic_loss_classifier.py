from src.aerial_housing_detection.ml.synthetic_loss_classifier import (
    SyntheticLossClassifier,
)


def main() -> None:
    classifier = SyntheticLossClassifier()
    result = classifier.run()

    print("Classificador sintético do agente de perdas executado com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Métricas: {result.metrics_path}")
    print(f"Ranking: {result.ranking_path}")
    print(f"Total de linhas: {result.total_rows}")
    print(f"Linhas positivas: {result.positive_rows}")
    print(f"Precision@10: {result.precision_at_10}")
    print(f"Precision@50: {result.precision_at_50}")
    print(f"Recall@50: {result.recall_at_50}")


if __name__ == "__main__":
    main()
