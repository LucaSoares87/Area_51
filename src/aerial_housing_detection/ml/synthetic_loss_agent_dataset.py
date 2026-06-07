import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
SOURCE_DIR = Path("data/imports/synthetic_ml")


@dataclass(frozen=True)
class SyntheticLossAgentImportResult:
    database_path: str
    source_dir: str
    imported_tables: dict[str, int]
    total_rows: int


class SyntheticLossAgentDatasetImporter:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        source_dir: Path = SOURCE_DIR,
    ) -> None:
        self.db_path = db_path
        self.source_dir = source_dir

    def run(self) -> SyntheticLossAgentImportResult:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        imported_tables: dict[str, int] = {}

        with sqlite3.connect(self.db_path) as connection:
            self._create_tables(connection)
            self._clear_tables(connection)

            imported_tables["synthetic_loss_agent_dataset"] = self._import_csv(
                connection=connection,
                csv_path=self.source_dir / "fake_dataset_agente_perdas_transformador_mes.csv",
                table_name="synthetic_loss_agent_dataset",
                columns=[
                    "codigo_transformador",
                    "codigo_subestacao",
                    "codigo_alimentador",
                    "mes_referencia",
                    "latitude",
                    "longitude",
                    "qtd_clientes_vinculados",
                    "qtd_clientes_com_consumo",
                    "consumo_faturado_kwh",
                    "qtd_instalacoes_gd",
                    "energia_injetada_total",
                    "qtd_inspecoes",
                    "qtd_irregularidades_confirmadas",
                    "qtd_defeitos_concessionaria",
                    "qtd_sem_perdas",
                    "qtd_normais",
                    "qtd_casas_cras",
                    "qtd_casas_ibge",
                    "qtd_casas_telhado",
                    "media_estimativa_casas",
                    "divergencia_casas_clientes",
                    "nivel_divergencia_habitacional",
                    "perda_estimada_kwh",
                    "perda_estimada_percentual",
                    "nivel_calor",
                    "target_irregularidade_confirmada",
                    "prioridade_ml_operacional",
                ],
            )

            imported_tables["synthetic_transformer_heatmap"] = self._import_csv(
                connection=connection,
                csv_path=self.source_dir / "fake_heatmap_transformador_mes.csv",
                table_name="synthetic_transformer_heatmap",
                columns=[
                    "codigo_transformador",
                    "codigo_subestacao",
                    "codigo_alimentador",
                    "mes_referencia",
                    "latitude",
                    "longitude",
                    "consumo_faturado_kwh",
                    "energia_injetada_total",
                    "perda_estimada_kwh",
                    "perda_estimada_percentual",
                    "qtd_irregularidades_confirmadas",
                    "target_irregularidade_confirmada",
                    "nivel_calor",
                ],
            )

            imported_tables["synthetic_feeder_heatmap"] = self._import_csv(
                connection=connection,
                csv_path=self.source_dir / "fake_heatmap_alimentador_mes.csv",
                table_name="synthetic_feeder_heatmap",
                columns=[
                    "codigo_subestacao",
                    "codigo_alimentador",
                    "mes_referencia",
                    "qtd_transformadores",
                    "latitude_centroide",
                    "longitude_centroide",
                    "consumo_faturado_kwh",
                    "perda_estimada_kwh",
                    "perda_estimada_percentual_media",
                    "qtd_irregularidades_confirmadas",
                    "nivel_calor_alimentador",
                ],
            )

            imported_tables["synthetic_housing_estimates"] = self._import_csv(
                connection=connection,
                csv_path=self.source_dir / "fake_estimativa_casas_transformador.csv",
                table_name="synthetic_housing_estimates",
                columns=[
                    "codigo_transformador",
                    "codigo_subestacao",
                    "codigo_alimentador",
                    "latitude",
                    "longitude",
                    "qtd_clientes_cadastrados",
                    "qtd_casas_cras",
                    "qtd_casas_ibge",
                    "qtd_casas_telhado",
                    "media_estimativa_casas",
                    "divergencia_casas_clientes",
                    "nivel_divergencia_habitacional",
                ],
            )

            imported_tables["synthetic_irregularity_labels"] = self._import_csv(
                connection=connection,
                csv_path=self.source_dir / "fake_labels_irregularidade_transformador_mes.csv",
                table_name="synthetic_irregularity_labels",
                columns=[
                    "codigo_transformador",
                    "codigo_subestacao",
                    "codigo_alimentador",
                    "mes_referencia",
                    "qtd_inspecoes",
                    "qtd_instalacoes_inspecionadas",
                    "qtd_irregularidades_confirmadas",
                    "qtd_defeitos_concessionaria",
                    "qtd_sem_perdas",
                    "qtd_normais",
                    "target_irregularidade_confirmada",
                ],
            )

        total_rows = sum(imported_tables.values())

        return SyntheticLossAgentImportResult(
            database_path=str(self.db_path),
            source_dir=str(self.source_dir),
            imported_tables=imported_tables,
            total_rows=total_rows,
        )

    def _create_tables(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_loss_agent_dataset (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                latitude REAL,
                longitude REAL,
                qtd_clientes_vinculados INTEGER,
                qtd_clientes_com_consumo INTEGER,
                consumo_faturado_kwh REAL,
                qtd_instalacoes_gd INTEGER,
                energia_injetada_total REAL,
                qtd_inspecoes INTEGER,
                qtd_irregularidades_confirmadas INTEGER,
                qtd_defeitos_concessionaria INTEGER,
                qtd_sem_perdas INTEGER,
                qtd_normais INTEGER,
                qtd_casas_cras INTEGER,
                qtd_casas_ibge INTEGER,
                qtd_casas_telhado INTEGER,
                media_estimativa_casas REAL,
                divergencia_casas_clientes REAL,
                nivel_divergencia_habitacional TEXT,
                perda_estimada_kwh REAL,
                perda_estimada_percentual REAL,
                nivel_calor TEXT,
                target_irregularidade_confirmada INTEGER,
                prioridade_ml_operacional TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_transformer_heatmap (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                latitude REAL,
                longitude REAL,
                consumo_faturado_kwh REAL,
                energia_injetada_total REAL,
                perda_estimada_kwh REAL,
                perda_estimada_percentual REAL,
                qtd_irregularidades_confirmadas INTEGER,
                target_irregularidade_confirmada INTEGER,
                nivel_calor TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_heatmap (
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_transformadores INTEGER,
                latitude_centroide REAL,
                longitude_centroide REAL,
                consumo_faturado_kwh REAL,
                perda_estimada_kwh REAL,
                perda_estimada_percentual_media REAL,
                qtd_irregularidades_confirmadas INTEGER,
                nivel_calor_alimentador TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_housing_estimates (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                latitude REAL,
                longitude REAL,
                qtd_clientes_cadastrados INTEGER,
                qtd_casas_cras INTEGER,
                qtd_casas_ibge INTEGER,
                qtd_casas_telhado INTEGER,
                media_estimativa_casas REAL,
                divergencia_casas_clientes REAL,
                nivel_divergencia_habitacional TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_irregularity_labels (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_inspecoes INTEGER,
                qtd_instalacoes_inspecionadas INTEGER,
                qtd_irregularidades_confirmadas INTEGER,
                qtd_defeitos_concessionaria INTEGER,
                qtd_sem_perdas INTEGER,
                qtd_normais INTEGER,
                target_irregularidade_confirmada INTEGER
            )
            """
        )

    def _clear_tables(self, connection: sqlite3.Connection) -> None:
        for table_name in [
            "synthetic_loss_agent_dataset",
            "synthetic_transformer_heatmap",
            "synthetic_feeder_heatmap",
            "synthetic_housing_estimates",
            "synthetic_irregularity_labels",
        ]:
            connection.execute(f"DELETE FROM {table_name}")

    def _import_csv(
        self,
        connection: sqlite3.Connection,
        csv_path: Path,
        table_name: str,
        columns: list[str],
    ) -> int:
        if not csv_path.exists():
            return 0

        rows = _read_csv(csv_path)

        if not rows:
            return 0

        placeholders = ", ".join(["?"] * len(columns))
        column_names = ", ".join(columns)

        values = [
            tuple(_coerce_value(row.get(column, "")) for column in columns)
            for row in rows
        ]

        connection.executemany(
            f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
            values,
        )

        return len(values)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(2048)
        file.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(file, delimiter=delimiter)
        return [dict(row) for row in reader]


def _coerce_value(value: Any) -> Any:
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    normalized = text.replace(",", ".")

    try:
        number = float(normalized)
    except ValueError:
        return text

    if number.is_integer():
        return int(number)

    return number
