from src.aerial_housing_detection.services.operational_feature_store import (
    OperationalFeatureStore,
)


def main() -> None:
    store = OperationalFeatureStore()
    result = store.build()

    print("Feature store operacional criada com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Tabela: {result.table_name}")
    print(f"Linhas geradas: {result.rows_created}")


if __name__ == "__main__":
    main()