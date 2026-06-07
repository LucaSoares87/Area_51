import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
ICC_PATH = Path("data/imports/concessionaria/Relatorio_ICC_IRREGULARIDADES_Ativas_20260601.csv")


@dataclass(frozen=True)
class IccIrregularityImportResult:
    database_path: str
    source_path: str
    imported_rows: int
    label_rows: int


class IccIrregularityLabelImporter:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        source_path: Path = ICC_PATH,
    ) -> None:
        self.db_path = db_path
        self.source_path = source_path

    def run(self) -> IccIrregularityImportResult:
        rows = self._read_source_rows()

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            self._create_tables(connection)
            self._clear_tables(connection)
            self._insert_irregularities(connection, rows)
            label_rows = self._build_transformer_labels(connection)

        return IccIrregularityImportResult(
            database_path=str(self.db_path),
            source_path=str(self.source_path),
            imported_rows=len(rows),
            label_rows=label_rows,
        )

    def _read_source_rows(self) -> list[dict[str, Any]]:
        if not self.source_path.exists():
            return []

        with self.source_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter=";")
            return [normalize_icc_row(row) for row in reader]

    def _create_tables(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_icc_active_irregularities (
                numero_nota TEXT,
                instalacao TEXT,
                conta_contrato TEXT,
                codigo_irregularidade TEXT,
                periodo_inicio_irregularidade TEXT,
                periodo_fim_irregularidade TEXT,
                data_criacao TEXT,
                data_atualizacao TEXT,
                codigo_situacao TEXT,
                numero_ordem TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_transformer_irregularity_labels (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_irregularidades_ativas INTEGER,
                qtd_instalacoes_com_irregularidade INTEGER,
                codigos_irregularidade TEXT,
                target_irregularidade_ativa INTEGER
            )
            """
        )

    def _clear_tables(self, connection: sqlite3.Connection) -> None:
        connection.execute("DELETE FROM real_icc_active_irregularities")
        connection.execute("DELETE FROM real_transformer_irregularity_labels")

    def _insert_irregularities(
        self,
        connection: sqlite3.Connection,
        rows: list[dict[str, Any]],
    ) -> None:
        if not rows:
            return

        connection.executemany(
            """
            INSERT INTO real_icc_active_irregularities (
                numero_nota,
                instalacao,
                conta_contrato,
                codigo_irregularidade,
                periodo_inicio_irregularidade,
                periodo_fim_irregularidade,
                data_criacao,
                data_atualizacao,
                codigo_situacao,
                numero_ordem
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["numero_nota"],
                    row["instalacao"],
                    row["conta_contrato"],
                    row["codigo_irregularidade"],
                    row["periodo_inicio_irregularidade"],
                    row["periodo_fim_irregularidade"],
                    row["data_criacao"],
                    row["data_atualizacao"],
                    row["codigo_situacao"],
                    row["numero_ordem"],
                )
                for row in rows
            ],
        )

    def _build_transformer_labels(self, connection: sqlite3.Connection) -> int:
        if not self._table_exists(connection, "real_transformer_customers"):
            return 0

        connection.execute(
            """
            INSERT INTO real_transformer_irregularity_labels (
                codigo_transformador,
                codigo_subestacao,
                codigo_alimentador,
                mes_referencia,
                qtd_irregularidades_ativas,
                qtd_instalacoes_com_irregularidade,
                codigos_irregularidade,
                target_irregularidade_ativa
            )
            SELECT
                customers.codigo_transformador AS codigo_transformador,
                customers.codigo_subestacao AS codigo_subestacao,
                customers.codigo_alimentador AS codigo_alimentador,
                COALESCE(
                    NULLIF(SUBSTR(irregularities.periodo_inicio_irregularidade, 1, 7), ''),
                    NULLIF(SUBSTR(irregularities.data_criacao, 1, 7), ''),
                    'sem_referencia'
                ) AS mes_referencia,
                COUNT(*) AS qtd_irregularidades_ativas,
                COUNT(DISTINCT irregularities.instalacao)
                    AS qtd_instalacoes_com_irregularidade,
                GROUP_CONCAT(DISTINCT irregularities.codigo_irregularidade)
                    AS codigos_irregularidade,
                1 AS target_irregularidade_ativa
            FROM real_icc_active_irregularities irregularities
            INNER JOIN real_transformer_customers customers
                ON TRIM(irregularities.instalacao) = TRIM(customers.instalacao)
                OR printf('%012s', TRIM(irregularities.conta_contrato)) =
                    printf('%012s', TRIM(customers.conta_contrato))
            WHERE customers.codigo_transformador IS NOT NULL
              AND customers.codigo_transformador <> ''
            GROUP BY
                customers.codigo_transformador,
                customers.codigo_subestacao,
                customers.codigo_alimentador,
                COALESCE(
                    NULLIF(SUBSTR(irregularities.periodo_inicio_irregularidade, 1, 7), ''),
                    NULLIF(SUBSTR(irregularities.data_criacao, 1, 7), ''),
                    'sem_referencia'
                )
            """
        )

        row = connection.execute(
            "SELECT COUNT(*) FROM real_transformer_irregularity_labels"
        ).fetchone()

        return int(row[0]) if row else 0

    def _table_exists(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> bool:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        return row is not None


def normalize_icc_row(row: dict[str, Any]) -> dict[str, str]:
    normalized = {str(key).strip().upper(): value for key, value in row.items()}

    return {
        "numero_nota": _clean(normalized.get("QMNUM")),
        "instalacao": _clean(normalized.get("ANLAGE")),
        "conta_contrato": _clean(normalized.get("ZCGACCOUN")),
        "codigo_irregularidade": _clean(normalized.get("COD_IRREG")),
        "periodo_inicio_irregularidade": _normalize_period(
            normalized.get("P_INIIRREG")
        ),
        "periodo_fim_irregularidade": _normalize_period(
            normalized.get("P_FINIRREG")
        ),
        "data_criacao": _normalize_date(normalized.get("ERDAT")),
        "data_atualizacao": _normalize_date(normalized.get("AEDAT")),
        "codigo_situacao": _clean(normalized.get("CODSIT")),
        "numero_ordem": _clean(normalized.get("ONEORDERNUMBER")),
    }


def _clean(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _normalize_period(value: Any) -> str:
    text = _clean(value)

    if not text:
        return ""

    if len(text) >= 7 and text[4] == "-":
        return text[:7]

    digits = "".join(character for character in text if character.isdigit())

    if len(digits) >= 6:
        return f"{digits[:4]}-{digits[4:6]}"

    return text


def _normalize_date(value: Any) -> str:
    text = _clean(value)

    if not text:
        return ""

    if len(text) >= 10 and text[4] == "-":
        return text[:10]

    digits = "".join(character for character in text if character.isdigit())

    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"

    return text
