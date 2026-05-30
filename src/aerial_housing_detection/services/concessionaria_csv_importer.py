import csv
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

IMPORTS_DIR = Path("data/imports/concessionaria")
DB_PATH = Path("data/area51.db")


@dataclass(frozen=True)
class CsvImportResult:
    file_name: str
    table_name: str
    rows_imported: int
    columns: list[str]


@dataclass(frozen=True)
class ConcessionariaImportSummary:
    database_path: str
    imported_files: list[CsvImportResult]


class ConcessionariaCsvImporter:
    def __init__(
        self,
        imports_dir: Path = IMPORTS_DIR,
        db_path: Path = DB_PATH,
    ) -> None:
        self.imports_dir = imports_dir
        self.db_path = db_path

    def import_all(self) -> ConcessionariaImportSummary:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        imported_files: list[CsvImportResult] = []

        with sqlite3.connect(self.db_path) as connection:
            self._create_tables(connection)

            for spec in _CSV_SPECS:
                path = self.imports_dir / spec.file_name
                if not path.exists():
                    continue

                rows = self._read_csv(path)
                normalized_rows = [
                    self._normalize_row(row, spec.column_map)
                    for row in rows
                ]

                normalized_rows = [
                    row for row in normalized_rows if self._has_any_value(row)
                ]

                self._replace_rows(
                    connection=connection,
                    table_name=spec.table_name,
                    columns=spec.columns,
                    rows=normalized_rows,
                )

                imported_files.append(
                    CsvImportResult(
                        file_name=spec.file_name,
                        table_name=spec.table_name,
                        rows_imported=len(normalized_rows),
                        columns=spec.columns,
                    )
                )

        return ConcessionariaImportSummary(
            database_path=str(self.db_path),
            imported_files=imported_files,
        )

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        lines = raw.splitlines()
        first_line = lines[0] if lines else ""
        delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, delimiter=delimiter)
            return [dict(row) for row in reader]

    def _normalize_row(
        self,
        row: dict[str, str],
        column_map: dict[str, str],
    ) -> dict[str, Any]:
        normalized_source = {
            _normalize_column_name(key): _clean_value(value)
            for key, value in row.items()
        }

        result: dict[str, Any] = {}

        for target_column, source_column in column_map.items():
            value = normalized_source.get(source_column)
            result[target_column] = self._coerce_value(target_column, value)

        return result

    def _coerce_value(self, column: str, value: str | None) -> Any:
        if value is None or value == "":
            return None

        if column in _INTEGER_COLUMNS:
            return _parse_integer(value)

        if column in _FLOAT_COLUMNS:
            return _parse_float(value)

        if column == "mes_referencia":
            return _parse_month(value)

        return value.strip()

    def _replace_rows(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        columns: list[str],
        rows: list[dict[str, Any]],
    ) -> None:
        connection.execute(f"DELETE FROM {table_name}")

        if not rows:
            return

        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)
        insert_sql = f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})"

        for row in rows:
            connection.execute(
                insert_sql,
                tuple(row.get(column) for column in columns),
            )

    def _create_tables(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_electrical_assets (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                pg_id REAL,
                pg TEXT,
                codigo_ponto_medido TEXT,
                conta_contrato TEXT,
                data_cadastro_gse TEXT,
                data_exclusao TEXT,
                latitude REAL,
                longitude REAL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_transformer_customers (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                instalacao TEXT,
                conta_contrato TEXT,
                regional TEXT,
                setor TEXT,
                subestacao_cliente TEXT,
                alimentador_cliente TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_transformer_consumption_monthly (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_clientes_com_consumo INTEGER,
                consumo_faturado_kwh REAL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_transformer_gd_monthly (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_instalacoes_gd INTEGER,
                energia_injetada_total REAL,
                energia_injetada_fora_ponta REAL,
                energia_injetada_ponta REAL,
                disponibilidade_total REAL,
                demanda_geracao_total REAL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_customer_status_by_transformer (
                utd TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                codigo_transformador TEXT,
                municipio TEXT,
                qtd_uc INTEGER,
                qtd_ligado INTEGER,
                qtd_cortado INTEGER,
                qtd_baixado INTEGER
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_transformer_notes (
                utd TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                codigo_transformador TEXT,
                municipio TEXT,
                tipo_nota TEXT,
                ano_referencia TEXT,
                quantidade_notas INTEGER
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_customer_classification (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                classe TEXT,
                quantidade_clientes INTEGER
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_low_income_classification (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                classificacao_baixa_renda TEXT,
                quantidade_clientes INTEGER
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_recovered_energy (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                energia_recuperada_media_kwh REAL
            )
            """
        )

    def _has_any_value(self, row: dict[str, Any]) -> bool:
        return any(value not in (None, "") for value in row.values())


@dataclass(frozen=True)
class CsvSpec:
    file_name: str
    table_name: str
    columns: list[str]
    column_map: dict[str, str]


_CSV_SPECS = [
    CsvSpec(
        file_name="ativos_eletricos.csv",
        table_name="real_electrical_assets",
        columns=[
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "pg_id",
            "pg",
            "codigo_ponto_medido",
            "conta_contrato",
            "data_cadastro_gse",
            "data_exclusao",
            "latitude",
            "longitude",
        ],
        column_map={
            "codigo_transformador": "codigo_transformador",
            "codigo_subestacao": "codigo_subestacao",
            "codigo_alimentador": "codigo_alimentador",
            "pg_id": "pg_id",
            "pg": "pg",
            "codigo_ponto_medido": "codigo_ponto_medido",
            "conta_contrato": "conta_contrato",
            "data_cadastro_gse": "data_cadastro_gse",
            "data_exclusao": "data_exclusao",
            "latitude": "latitude",
            "longitude": "longitude",
        },
    ),
    CsvSpec(
        file_name="clientes_transformador.csv",
        table_name="real_transformer_customers",
        columns=[
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "instalacao",
            "conta_contrato",
            "regional",
            "setor",
            "subestacao_cliente",
            "alimentador_cliente",
        ],
        column_map={
            "codigo_transformador": "codigo_transformador",
            "codigo_subestacao": "codigo_subestacao",
            "codigo_alimentador": "codigo_alimentador",
            "instalacao": "instalacao",
            "conta_contrato": "conta_contrato",
            "regional": "regional",
            "setor": "setor",
            "subestacao_cliente": "subestacao_cliente",
            "alimentador_cliente": "alimentador_cliente",
        },
    ),
    CsvSpec(
        file_name="consumo_transformador_mensal.csv",
        table_name="real_transformer_consumption_monthly",
        columns=[
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "mes_referencia",
            "qtd_clientes_com_consumo",
            "consumo_faturado_kwh",
        ],
        column_map={
            "codigo_transformador": "codigo_transformador",
            "codigo_subestacao": "codigo_subestacao",
            "codigo_alimentador": "codigo_alimentador",
            "mes_referencia": "mes_referencia",
            "qtd_clientes_com_consumo": "qtd_clientes_com_consumo",
            "consumo_faturado_kwh": "consumo_faturado_kwh",
        },
    ),
    CsvSpec(
        file_name="gd_transformador_mensal.csv",
        table_name="real_transformer_gd_monthly",
        columns=[
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "mes_referencia",
            "qtd_instalacoes_gd",
            "energia_injetada_total",
            "energia_injetada_fora_ponta",
            "energia_injetada_ponta",
            "disponibilidade_total",
            "demanda_geracao_total",
        ],
        column_map={
            "codigo_transformador": "codigo_transformador",
            "codigo_subestacao": "codigo_subestacao",
            "codigo_alimentador": "codigo_alimentador",
            "mes_referencia": "mes_referencia",
            "qtd_instalacoes_gd": "qtd_instalacoes_gd",
            "energia_injetada_total": "energia_injetada_total",
            "energia_injetada_fora_ponta": "energia_injetada_fora_ponta",
            "energia_injetada_ponta": "energia_injetada_ponta",
            "disponibilidade_total": "disponibilidade_total",
            "demanda_geracao_total": "demanda_geracao_total",
        },
    ),
    CsvSpec(
        file_name="qtde_de_cliente_ativos_e_cortados.csv",
        table_name="real_customer_status_by_transformer",
        columns=[
            "utd",
            "codigo_subestacao",
            "codigo_alimentador",
            "codigo_transformador",
            "municipio",
            "qtd_uc",
            "qtd_ligado",
            "qtd_cortado",
            "qtd_baixado",
        ],
        column_map={
            "utd": "utd",
            "codigo_subestacao": "subestacao",
            "codigo_alimentador": "alimentador",
            "codigo_transformador": "trafo",
            "municipio": "municipio",
            "qtd_uc": "qtd_uc",
            "qtd_ligado": "qtd_ligado",
            "qtd_cortado": "qtd_cortado",
            "qtd_baixado": "qtd_baixado",
        },
    ),
    CsvSpec(
        file_name="subestacao_alm_trafo_tpnota.csv",
        table_name="real_transformer_notes",
        columns=[
            "utd",
            "codigo_subestacao",
            "codigo_alimentador",
            "codigo_transformador",
            "municipio",
            "tipo_nota",
            "ano_referencia",
            "quantidade_notas",
        ],
        column_map={
            "utd": "utd",
            "codigo_subestacao": "subestacao",
            "codigo_alimentador": "alimentador",
            "codigo_transformador": "trafo",
            "municipio": "municipio",
            "tipo_nota": "tp_nota",
            "ano_referencia": "ref",
            "quantidade_notas": "count",
        },
    ),
    CsvSpec(
        file_name="classificacao_de_clientes.csv",
        table_name="real_customer_classification",
        columns=[
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "classe",
            "quantidade_clientes",
        ],
        column_map={
            "codigo_transformador": "codigo_transformador",
            "codigo_subestacao": "codigo_subestacao",
            "codigo_alimentador": "codigo_alimentador",
            "classe": "classe",
            "quantidade_clientes": "quantidade_clientes",
        },
    ),
    CsvSpec(
        file_name="classificacao_baixa_renda.csv",
        table_name="real_low_income_classification",
        columns=[
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "classificacao_baixa_renda",
            "quantidade_clientes",
        ],
        column_map={
            "codigo_transformador": "codigo_transformador",
            "codigo_subestacao": "codigo_subestacao",
            "codigo_alimentador": "codigo_alimentador",
            "classificacao_baixa_renda": "classificacao_baixa_renda",
            "quantidade_clientes": "quantidade_clientes",
        },
    ),
    CsvSpec(
        file_name="energia_recuperada_media.csv",
        table_name="real_recovered_energy",
        columns=[
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "energia_recuperada_media_kwh",
        ],
        column_map={
            "codigo_transformador": "codigo_transformador",
            "codigo_subestacao": "codigo_subestacao",
            "codigo_alimentador": "codigo_alimentador",
            "energia_recuperada_media_kwh": "energia_recuperada_media",
        },
    ),
]


_INTEGER_COLUMNS = {
    "qtd_clientes_com_consumo",
    "qtd_instalacoes_gd",
    "qtd_uc",
    "qtd_ligado",
    "qtd_cortado",
    "qtd_baixado",
    "quantidade_notas",
    "quantidade_clientes",
}

_FLOAT_COLUMNS = {
    "pg_id",
    "latitude",
    "longitude",
    "consumo_faturado_kwh",
    "energia_injetada_total",
    "energia_injetada_fora_ponta",
    "energia_injetada_ponta",
    "disponibilidade_total",
    "demanda_geracao_total",
    "energia_recuperada_media_kwh",
}


def _normalize_column_name(value: str | None) -> str:
    if value is None:
        return ""

    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")

    if normalized == "count":
        return "count"

    return normalized


def _clean_value(value: Any) -> str:
    if value is None:
        return ""

    cleaned = str(value).strip()

    if cleaned in {"?", "-", "NULL", "null", "None", "none"}:
        return ""

    return cleaned


def _parse_float(value: str) -> float | None:
    cleaned = _clean_value(value)

    if cleaned == "":
        return None

    cleaned = cleaned.replace(" ", "")

    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_integer(value: str) -> int | None:
    parsed = _parse_float(value)

    if parsed is None:
        return None

    return int(round(parsed))


def _parse_month(value: str) -> str | None:
    cleaned = _clean_value(value)

    if cleaned == "":
        return None

    cleaned = cleaned.strip()

    if re.fullmatch(r"\d{6}", cleaned):
        return f"{cleaned[:4]}-{cleaned[4:6]}"

    if re.fullmatch(r"\d{4}-\d{2}", cleaned):
        return cleaned

    if re.fullmatch(r"\d{4}", cleaned):
        return cleaned

    return cleaned
