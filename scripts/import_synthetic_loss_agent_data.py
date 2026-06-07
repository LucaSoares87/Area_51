from src.aerial_housing_detection.ml.synthetic_loss_agent_dataset import (
    SyntheticLossAgentDatasetImporter,
)


def main() -> None:
    importer = SyntheticLossAgentDatasetImporter()
    result = importer.run()

    print("Importação do dataset sintético do agente de perdas executada com sucesso.")
    print(f"Banco local: {result.database_path}")
    print(f"Diretório de origem: {result.source_dir}")
    print("Tabelas importadas:")

    for table_name, row_count in result.imported_tables.items():
        print(f"- {table_name}: {row_count} linhas")

    print(f"Total de linhas importadas: {result.total_rows}")


if __name__ == "__main__":
    main()
