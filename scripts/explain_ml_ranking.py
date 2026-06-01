from src.aerial_housing_detection.ml.explainability import (
    TransformerRankingExplainer,
)


def main() -> None:
    explainer = TransformerRankingExplainer()
    result = explainer.run()

    print("Explicabilidade do ranking de Machine Learning executada com sucesso.")
    print(f"Dataset: {result.dataset_path}")
    print(f"Resumo: {result.summary_path}")
    print(f"Ranking auditável: {result.ranking_path}")
    print(f"Total de linhas: {result.total_rows}")
    print(f"Linhas explicadas: {result.explained_rows}")


if __name__ == "__main__":
    main()
