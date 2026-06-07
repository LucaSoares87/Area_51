from src.aerial_housing_detection.ml.synthetic_loss_map import (
    SyntheticLossMapBuilder,
)


def main() -> None:
    builder = SyntheticLossMapBuilder()
    result = builder.run()

    print("Mapa HTML sintético de perdas executado com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Mapa HTML: {result.map_path}")
    print(f"Pontos de transformadores: {result.transformer_points}")
    print(f"Pontos de alimentadores: {result.feeder_points}")
    print(f"Transformadores em calor alto: {result.high_heat_transformers}")
    print(f"Alimentadores em calor alto: {result.high_heat_feeders}")


if __name__ == "__main__":
    main()
