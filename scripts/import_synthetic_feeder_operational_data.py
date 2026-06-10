from src.aerial_housing_detection.ml.synthetic_feeder_operational import (
    SyntheticFeederOperationalBuilder,
)


def main() -> None:
    builder = SyntheticFeederOperationalBuilder()
    result = builder.run()

    print("Base sintética operacional do alimentador executada com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Resumo: {result.summary_path}")
    print(f"Percurso do alimentador: {result.route_path}")
    print(f"Seções do alimentador: {result.sections_path}")
    print(f"Subestações: {result.substations}")
    print(f"Alimentadores: {result.feeders}")
    print(f"Pontos do percurso: {result.route_points}")
    print(f"Religadores: {result.reclosers}")
    print(f"Clientes MT: {result.mv_customers}")
    print(f"Transformadores: {result.transformers}")
    print(f"Seções: {result.sections}")


if __name__ == "__main__":
    main()
