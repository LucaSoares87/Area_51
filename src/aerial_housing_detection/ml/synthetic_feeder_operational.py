import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
SUMMARY_PATH = Path("reports/synthetic_feeder_operational_summary.json")
ROUTE_PATH = Path("reports/synthetic_feeder_operational_route.csv")
SECTIONS_PATH = Path("reports/synthetic_feeder_operational_sections.csv")


@dataclass(frozen=True)
class SyntheticFeederOperationalResult:
    database_path: str
    summary_path: str
    route_path: str
    sections_path: str
    substations: int
    feeders: int
    route_points: int
    reclosers: int
    mv_customers: int
    transformers: int
    sections: int


class SyntheticFeederOperationalBuilder:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        summary_path: Path = SUMMARY_PATH,
        route_path: Path = ROUTE_PATH,
        sections_path: Path = SECTIONS_PATH,
    ) -> None:
        self.db_path = db_path
        self.summary_path = summary_path
        self.route_path = route_path
        self.sections_path = sections_path

    def run(self) -> SyntheticFeederOperationalResult:
        dataset = build_synthetic_feeder_dataset()

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.route_path.parent.mkdir(parents=True, exist_ok=True)
        self.sections_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            self._create_tables(connection)
            self._clear_tables(connection)
            self._insert_dataset(connection, dataset)

        summary = build_operational_summary(dataset)
        route_rows = dataset["route_points"]
        section_rows = build_section_rows(dataset)

        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.route_path.write_text(
            _to_csv(route_rows, ROUTE_FIELDS),
            encoding="utf-8",
        )
        self.sections_path.write_text(
            _to_csv(section_rows, SECTION_FIELDS),
            encoding="utf-8",
        )

        return SyntheticFeederOperationalResult(
            database_path=str(self.db_path),
            summary_path=str(self.summary_path),
            route_path=str(self.route_path),
            sections_path=str(self.sections_path),
            substations=len(dataset["substations"]),
            feeders=len(dataset["feeders"]),
            route_points=len(dataset["route_points"]),
            reclosers=len(dataset["reclosers"]),
            mv_customers=len(dataset["mv_customers"]),
            transformers=len(dataset["transformers"]),
            sections=len(section_rows),
        )

    def _create_tables(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_substations (
                codigo_subestacao TEXT PRIMARY KEY,
                nome_subestacao TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                tensao_kv REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_feeders (
                codigo_alimentador TEXT PRIMARY KEY,
                codigo_subestacao TEXT NOT NULL,
                nome_alimentador TEXT NOT NULL,
                extensao_rede_km REAL NOT NULL,
                total_uc_bt INTEGER NOT NULL,
                total_uc_mt INTEGER NOT NULL,
                total_gd INTEGER NOT NULL,
                total_transformadores INTEGER NOT NULL,
                total_religadores INTEGER NOT NULL,
                consumo_gwh REAL NOT NULL,
                energia_injetada_gwh REAL NOT NULL,
                perda_estimada_gwh REAL NOT NULL,
                perda_percentual REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_route_points (
                codigo_alimentador TEXT NOT NULL,
                sequencia INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                tipo_ponto TEXT NOT NULL,
                descricao TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_reclosers (
                codigo_religador TEXT PRIMARY KEY,
                codigo_alimentador TEXT NOT NULL,
                codigo_subestacao TEXT NOT NULL,
                trecho TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                ordem_fluxo INTEGER NOT NULL,
                transformadores_jusante INTEGER NOT NULL,
                uc_bt_jusante INTEGER NOT NULL,
                uc_mt_jusante INTEGER NOT NULL,
                gd_jusante INTEGER NOT NULL,
                consumo_jusante_gwh REAL NOT NULL,
                energia_injetada_jusante_gwh REAL NOT NULL,
                perda_jusante_gwh REAL NOT NULL,
                perda_percentual_jusante REAL NOT NULL,
                nivel_calor TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_mv_customers (
                codigo_cliente_mt TEXT PRIMARY KEY,
                codigo_alimentador TEXT NOT NULL,
                codigo_subestacao TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                demanda_kw REAL NOT NULL,
                consumo_mensal_mwh REAL NOT NULL,
                setor TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_transformers (
                codigo_transformador TEXT PRIMARY KEY,
                codigo_alimentador TEXT NOT NULL,
                codigo_subestacao TEXT NOT NULL,
                trecho TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                uc_bt INTEGER NOT NULL,
                uc_mt INTEGER NOT NULL,
                gd INTEGER NOT NULL,
                consumo_mensal_mwh REAL NOT NULL,
                energia_injetada_mwh REAL NOT NULL,
                perda_estimada_mwh REAL NOT NULL,
                perda_percentual REAL NOT NULL,
                nivel_calor TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_feeder_sections (
                codigo_secao TEXT PRIMARY KEY,
                codigo_alimentador TEXT NOT NULL,
                codigo_subestacao TEXT NOT NULL,
                religador_origem TEXT NOT NULL,
                religador_destino TEXT NOT NULL,
                distancia_km REAL NOT NULL,
                transformadores INTEGER NOT NULL,
                uc_bt INTEGER NOT NULL,
                uc_mt INTEGER NOT NULL,
                gd INTEGER NOT NULL,
                consumo_gwh REAL NOT NULL,
                energia_injetada_gwh REAL NOT NULL,
                perda_estimada_gwh REAL NOT NULL,
                perda_percentual REAL NOT NULL,
                nivel_calor TEXT NOT NULL
            )
            """
        )

    def _clear_tables(self, connection: sqlite3.Connection) -> None:
        for table_name in TABLES:
            connection.execute(f"DELETE FROM {table_name}")

    def _insert_dataset(
        self,
        connection: sqlite3.Connection,
        dataset: dict[str, list[dict[str, Any]]],
    ) -> None:
        _insert_rows(connection, "synthetic_feeder_substations", dataset["substations"])
        _insert_rows(connection, "synthetic_feeder_feeders", dataset["feeders"])
        _insert_rows(connection, "synthetic_feeder_route_points", dataset["route_points"])
        _insert_rows(connection, "synthetic_feeder_reclosers", dataset["reclosers"])
        _insert_rows(connection, "synthetic_feeder_mv_customers", dataset["mv_customers"])
        _insert_rows(connection, "synthetic_feeder_transformers", dataset["transformers"])
        _insert_rows(connection, "synthetic_feeder_sections", build_section_rows(dataset))


def build_synthetic_feeder_dataset() -> dict[str, list[dict[str, Any]]]:
    codigo_subestacao = "HPO"
    codigo_alimentador = "HPO-0IL4"

    substations = [
        {
            "codigo_subestacao": codigo_subestacao,
            "nome_subestacao": "Subestação HPO",
            "latitude": -8.0194,
            "longitude": -34.9466,
            "tensao_kv": 69.0,
        }
    ]

    route_points = build_route_points(codigo_alimentador)
    transformers = build_transformers(codigo_subestacao, codigo_alimentador)
    reclosers = build_reclosers(codigo_subestacao, codigo_alimentador, transformers)
    mv_customers = build_mv_customers(codigo_subestacao, codigo_alimentador)

    feeder = {
        "codigo_alimentador": codigo_alimentador,
        "codigo_subestacao": codigo_subestacao,
        "nome_alimentador": "Modelo Alimentador HPO-0IL4",
        "extensao_rede_km": 6.0,
        "total_uc_bt": sum(_to_int(row["uc_bt"]) for row in transformers),
        "total_uc_mt": len(mv_customers),
        "total_gd": sum(_to_int(row["gd"]) for row in transformers),
        "total_transformadores": len(transformers),
        "total_religadores": len(reclosers),
        "consumo_gwh": round(
            sum(_to_float(row["consumo_mensal_mwh"]) for row in transformers) / 1000,
            6,
        ),
        "energia_injetada_gwh": round(
            sum(_to_float(row["energia_injetada_mwh"]) for row in transformers) / 1000,
            6,
        ),
        "perda_estimada_gwh": round(
            sum(_to_float(row["perda_estimada_mwh"]) for row in transformers) / 1000,
            6,
        ),
        "perda_percentual": 0.0,
    }
    feeder["perda_percentual"] = calculate_loss_percentual(
        feeder["perda_estimada_gwh"],
        feeder["consumo_gwh"],
    )

    return {
        "substations": substations,
        "feeders": [feeder],
        "route_points": route_points,
        "reclosers": reclosers,
        "mv_customers": mv_customers,
        "transformers": transformers,
        "sections": [],
    }


def build_route_points(codigo_alimentador: str) -> list[dict[str, Any]]:
    coordinates = [
        (-8.0194, -34.9466, "subestacao", "Saída da Subestação HPO"),
        (-8.0178, -34.9448, "rede", "Trecho inicial do alimentador"),
        (-8.0162, -34.9429, "religador", "Religador RLG-01"),
        (-8.0145, -34.9404, "rede", "Ramal urbano principal"),
        (-8.0128, -34.9381, "cliente_mt", "Cliente MT sintético 01"),
        (-8.0111, -34.9360, "religador", "Religador RLG-02"),
        (-8.0092, -34.9338, "rede", "Trecho com alta densidade BT"),
        (-8.0077, -34.9317, "cliente_mt", "Cliente MT sintético 02"),
        (-8.0060, -34.9295, "religador", "Religador RLG-03"),
        (-8.0042, -34.9273, "rede", "Trecho final com GD distribuída"),
        (-8.0024, -34.9251, "rede", "Fim do circuito principal"),
    ]

    return [
        {
            "codigo_alimentador": codigo_alimentador,
            "sequencia": index + 1,
            "latitude": latitude,
            "longitude": longitude,
            "tipo_ponto": tipo_ponto,
            "descricao": descricao,
        }
        for index, (latitude, longitude, tipo_ponto, descricao) in enumerate(coordinates)
    ]


def build_transformers(
    codigo_subestacao: str,
    codigo_alimentador: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    section_configs = [
        ("S01", 12, -8.0172, -34.9442, 135, 18, 0.06),
        ("S02", 18, -8.0144, -34.9405, 310, 34, 0.09),
        ("S03", 14, -8.0104, -34.9356, 360, 49, 0.13),
        ("S04", 16, -8.0062, -34.9298, 383, 36, 0.16),
    ]

    counter = 1

    for section, quantity, start_lat, start_lng, uc_base, gd_base, loss_base in section_configs:
        for index in range(quantity):
            progress = index / max(quantity - 1, 1)
            uc_bt = max(8, round(uc_base / quantity + (index % 5) - 2))
            gd = max(0, round(gd_base / quantity + (index % 3) - 1))
            uc_mt = 1 if counter in {7, 16, 23, 29, 37, 41, 48, 52, 58} else 0
            consumo_mwh = round(28 + uc_bt * 1.25 + uc_mt * 16 + (index % 4) * 2.5, 3)
            energia_injetada_mwh = round(gd * 3.2 + (index % 2) * 1.5, 3)
            perda_percentual = round(loss_base + (index % 6) * 0.008, 6)
            perda_mwh = round(consumo_mwh * perda_percentual, 3)

            rows.append(
                {
                    "codigo_transformador": f"TRF-HPO-0IL4-{counter:03d}",
                    "codigo_alimentador": codigo_alimentador,
                    "codigo_subestacao": codigo_subestacao,
                    "trecho": section,
                    "latitude": round(start_lat + progress * 0.0015, 6),
                    "longitude": round(start_lng + progress * 0.0016, 6),
                    "uc_bt": uc_bt,
                    "uc_mt": uc_mt,
                    "gd": gd,
                    "consumo_mensal_mwh": consumo_mwh,
                    "energia_injetada_mwh": energia_injetada_mwh,
                    "perda_estimada_mwh": perda_mwh,
                    "perda_percentual": perda_percentual,
                    "nivel_calor": classify_heat_level(perda_percentual, perda_mwh),
                }
            )
            counter += 1

    return rows


def build_reclosers(
    codigo_subestacao: str,
    codigo_alimentador: str,
    transformers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    configs = [
        ("RLG-01", "S01", -8.0162, -34.9429, 1),
        ("RLG-02", "S02", -8.0111, -34.9360, 2),
        ("RLG-03", "S03", -8.0060, -34.9295, 3),
    ]

    rows: list[dict[str, Any]] = []

    for codigo_religador, section, latitude, longitude, ordem_fluxo in configs:
        downstream = [
            row
            for row in transformers
            if _section_order(row["trecho"]) >= _section_order(section)
        ]

        consumo = sum(_to_float(row["consumo_mensal_mwh"]) for row in downstream) / 1000
        injetada = sum(_to_float(row["energia_injetada_mwh"]) for row in downstream) / 1000
        perda = sum(_to_float(row["perda_estimada_mwh"]) for row in downstream) / 1000
        perda_percentual = calculate_loss_percentual(perda, consumo)

        rows.append(
            {
                "codigo_religador": codigo_religador,
                "codigo_alimentador": codigo_alimentador,
                "codigo_subestacao": codigo_subestacao,
                "trecho": section,
                "latitude": latitude,
                "longitude": longitude,
                "ordem_fluxo": ordem_fluxo,
                "transformadores_jusante": len(downstream),
                "uc_bt_jusante": sum(_to_int(row["uc_bt"]) for row in downstream),
                "uc_mt_jusante": sum(_to_int(row["uc_mt"]) for row in downstream),
                "gd_jusante": sum(_to_int(row["gd"]) for row in downstream),
                "consumo_jusante_gwh": round(consumo, 6),
                "energia_injetada_jusante_gwh": round(injetada, 6),
                "perda_jusante_gwh": round(perda, 6),
                "perda_percentual_jusante": perda_percentual,
                "nivel_calor": classify_heat_level(perda_percentual, perda * 1000),
            }
        )

    return rows


def build_mv_customers(
    codigo_subestacao: str,
    codigo_alimentador: str,
) -> list[dict[str, Any]]:
    base_points = [
        (-8.0128, -34.9381, "comercial"),
        (-8.0077, -34.9317, "industrial"),
        (-8.0153, -34.9412, "servico"),
        (-8.0106, -34.9349, "comercial"),
        (-8.0069, -34.9307, "industrial"),
        (-8.0048, -34.9279, "rural"),
        (-8.0137, -34.9392, "servico"),
        (-8.0090, -34.9331, "comercial"),
        (-8.0056, -34.9288, "industrial"),
    ]

    return [
        {
            "codigo_cliente_mt": f"MT-HPO-0IL4-{index:03d}",
            "codigo_alimentador": codigo_alimentador,
            "codigo_subestacao": codigo_subestacao,
            "latitude": latitude,
            "longitude": longitude,
            "demanda_kw": 75 + index * 18,
            "consumo_mensal_mwh": round(18 + index * 3.7, 3),
            "setor": setor,
        }
        for index, (latitude, longitude, setor) in enumerate(base_points, start=1)
    ]


def build_section_rows(dataset: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    transformers = dataset["transformers"]
    configs = [
        ("SEC-01", "RLG-00", "RLG-01", "S01", 1.35),
        ("SEC-02", "RLG-01", "RLG-02", "S02", 1.65),
        ("SEC-03", "RLG-02", "RLG-03", "S03", 1.45),
        ("SEC-04", "RLG-03", "FIM", "S04", 1.55),
    ]

    rows: list[dict[str, Any]] = []

    for codigo_secao, origem, destino, trecho, distancia in configs:
        section_transformers = [row for row in transformers if row["trecho"] == trecho]
        consumo = (
            sum(_to_float(row["consumo_mensal_mwh"]) for row in section_transformers)
            / 1000
        )
        injetada = (
            sum(_to_float(row["energia_injetada_mwh"]) for row in section_transformers)
            / 1000
        )
        perda = (
            sum(_to_float(row["perda_estimada_mwh"]) for row in section_transformers)
            / 1000
        )
        perda_percentual = calculate_loss_percentual(perda, consumo)

        rows.append(
            {
                "codigo_secao": codigo_secao,
                "codigo_alimentador": "HPO-0IL4",
                "codigo_subestacao": "HPO",
                "religador_origem": origem,
                "religador_destino": destino,
                "distancia_km": distancia,
                "transformadores": len(section_transformers),
                "uc_bt": sum(_to_int(row["uc_bt"]) for row in section_transformers),
                "uc_mt": sum(_to_int(row["uc_mt"]) for row in section_transformers),
                "gd": sum(_to_int(row["gd"]) for row in section_transformers),
                "consumo_gwh": round(consumo, 6),
                "energia_injetada_gwh": round(injetada, 6),
                "perda_estimada_gwh": round(perda, 6),
                "perda_percentual": perda_percentual,
                "nivel_calor": classify_heat_level(perda_percentual, perda * 1000),
            }
        )

    return rows


def build_operational_summary(
    dataset: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    feeder = dataset["feeders"][0]
    transformers = dataset["transformers"]
    reclosers = dataset["reclosers"]
    sections = build_section_rows(dataset)

    return {
        "codigo_subestacao": feeder["codigo_subestacao"],
        "codigo_alimentador": feeder["codigo_alimentador"],
        "nome_alimentador": feeder["nome_alimentador"],
        "extensao_rede_km": feeder["extensao_rede_km"],
        "total_uc_bt": feeder["total_uc_bt"],
        "total_uc_mt": feeder["total_uc_mt"],
        "total_gd": feeder["total_gd"],
        "total_transformadores": feeder["total_transformadores"],
        "total_religadores": feeder["total_religadores"],
        "consumo_gwh": feeder["consumo_gwh"],
        "energia_injetada_gwh": feeder["energia_injetada_gwh"],
        "perda_estimada_gwh": feeder["perda_estimada_gwh"],
        "perda_percentual": feeder["perda_percentual"],
        "transformadores_calor_alto": sum(
            1 for row in transformers if row["nivel_calor"] == "ALTO"
        ),
        "religadores_calor_alto": sum(
            1 for row in reclosers if row["nivel_calor"] == "ALTO"
        ),
        "secoes_calor_alto": sum(1 for row in sections if row["nivel_calor"] == "ALTO"),
        "sections": sections,
        "reclosers": reclosers,
    }


def calculate_loss_percentual(loss: float, consumption: float) -> float:
    if consumption <= 0:
        return 0.0

    return round(loss / consumption, 6)


def classify_heat_level(loss_percentual: float, loss_mwh: float) -> str:
    if loss_percentual >= 0.16 or loss_mwh >= 90:
        return "ALTO"

    if loss_percentual >= 0.09 or loss_mwh >= 45:
        return "MEDIO"

    return "BAIXO"


TABLES = [
    "synthetic_feeder_sections",
    "synthetic_feeder_transformers",
    "synthetic_feeder_mv_customers",
    "synthetic_feeder_reclosers",
    "synthetic_feeder_route_points",
    "synthetic_feeder_feeders",
    "synthetic_feeder_substations",
]

ROUTE_FIELDS = [
    "codigo_alimentador",
    "sequencia",
    "latitude",
    "longitude",
    "tipo_ponto",
    "descricao",
]

SECTION_FIELDS = [
    "codigo_secao",
    "codigo_alimentador",
    "codigo_subestacao",
    "religador_origem",
    "religador_destino",
    "distancia_km",
    "transformadores",
    "uc_bt",
    "uc_mt",
    "gd",
    "consumo_gwh",
    "energia_injetada_gwh",
    "perda_estimada_gwh",
    "perda_percentual",
    "nivel_calor",
]


def _insert_rows(
    connection: sqlite3.Connection,
    table_name: str,
    rows: list[dict[str, Any]],
) -> None:
    if not rows:
        return

    columns = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)

    connection.executemany(
        f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
        [[row[column] for column in columns] for row in rows],
    )


def _to_csv(rows: list[dict[str, Any]], fieldnames: list[str]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fieldnames})

    return buffer.getvalue()


def _section_order(section: str) -> int:
    return int(section.replace("S", ""))


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0

    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0

    return int(float(value))
