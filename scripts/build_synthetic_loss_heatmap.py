from src.aerial_housing_detection.ml.synthetic_loss_heatmap import (
    SyntheticLossHeatmapBuilder,
)


def main() -> None:
    builder = SyntheticLossHeatmapBuilder()
    result = builder.run()

    print("Heatmap sintético de perdas executado com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Heatmap por transformador: {result.transformer_heatmap_path}")
    print(f"Heatmap por alimentador: {result.feeder_heatmap_path}")
    print(f"Resumo: {result.summary_path}")
    print(f"Linhas por transformador: {result.transformer_rows}")
    print(f"Linhas por alimentador: {result.feeder_rows}")
    print(f"Transformadores em calor alto: {result.high_heat_transformers}")
    print(f"Alimentadores em calor alto: {result.high_heat_feeders}")


if __name__ == "__main__":
    main()
