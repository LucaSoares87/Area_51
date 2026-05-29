import json
import sqlite3
from pathlib import Path
from typing import Any

SEED_PATH = Path("data/demo/concessionaria_seed.json")
DB_PATH = Path("data/area51.db")


def main() -> None:
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        create_tables(connection)
        clear_tables(connection)
        insert_substations(connection, seed["substations"])
        insert_transformers(connection, seed["transformers"])
        insert_customers(connection, seed["customers"])
        insert_customer_aggregates(connection, seed["customer_aggregates"])
        insert_roof_estimates(connection, seed["roof_estimates"])

    print("Banco realista de demonstração criado com sucesso.")
    print(f"Banco local: {DB_PATH}")
    print("Dados disponíveis:")
    print("Transformador: TR-001")
    print("Alimentador: AL-01")
    print("Subestação: SE-01")
    print("Coordenadas: -7.9401, -34.8734")


def create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_substations (
            substation_code TEXT PRIMARY KEY,
            substation_name TEXT NOT NULL,
            city TEXT NOT NULL,
            main_feeders TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_transformers (
            transformer_code TEXT PRIMARY KEY,
            power_kva REAL NOT NULL,
            feeder_code TEXT NOT NULL,
            substation_code TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            measured_energy_kwh REAL NOT NULL,
            injected_energy_kwh REAL NOT NULL,
            received_gd_energy_kwh REAL NOT NULL,
            technical_loss_kwh REAL NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_customers (
            installation_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            cpf TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            transformer_code TEXT NOT NULL,
            monthly_consumption_kwh REAL NOT NULL,
            has_gd INTEGER NOT NULL,
            gd_received_kwh REAL NOT NULL,
            gd_injected_kwh REAL NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_customer_aggregates (
            transformer_code TEXT PRIMARY KEY,
            customer_count INTEGER NOT NULL,
            total_consumption_kwh REAL NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_roof_estimates (
            transformer_code TEXT PRIMARY KEY,
            estimated_roofs INTEGER NOT NULL,
            confidence_score REAL NOT NULL,
            source TEXT NOT NULL
        )
        """
    )


def clear_tables(connection: sqlite3.Connection) -> None:
    tables = [
        "demo_substations",
        "demo_transformers",
        "demo_customers",
        "demo_customer_aggregates",
        "demo_roof_estimates",
    ]

    for table in tables:
        connection.execute(f"DELETE FROM {table}")


def insert_substations(
    connection: sqlite3.Connection,
    substations: list[dict[str, Any]],
) -> None:
    for substation in substations:
        connection.execute(
            """
            INSERT INTO demo_substations (
                substation_code,
                substation_name,
                city,
                main_feeders
            ) VALUES (?, ?, ?, ?)
            """,
            (
                substation["substation_code"],
                substation["substation_name"],
                substation["city"],
                json.dumps(substation["main_feeders"], ensure_ascii=False),
            ),
        )


def insert_transformers(
    connection: sqlite3.Connection,
    transformers: list[dict[str, Any]],
) -> None:
    for transformer in transformers:
        connection.execute(
            """
            INSERT INTO demo_transformers (
                transformer_code,
                power_kva,
                feeder_code,
                substation_code,
                latitude,
                longitude,
                measured_energy_kwh,
                injected_energy_kwh,
                received_gd_energy_kwh,
                technical_loss_kwh
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transformer["transformer_code"],
                transformer["power_kva"],
                transformer["feeder_code"],
                transformer["substation_code"],
                transformer["latitude"],
                transformer["longitude"],
                transformer["measured_energy_kwh"],
                transformer["injected_energy_kwh"],
                transformer["received_gd_energy_kwh"],
                transformer["technical_loss_kwh"],
            ),
        )


def insert_customers(
    connection: sqlite3.Connection,
    customers: list[dict[str, Any]],
) -> None:
    for customer in customers:
        connection.execute(
            """
            INSERT INTO demo_customers (
                installation_id,
                customer_name,
                cpf,
                postal_code,
                transformer_code,
                monthly_consumption_kwh,
                has_gd,
                gd_received_kwh,
                gd_injected_kwh
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer["installation_id"],
                customer["customer_name"],
                customer["cpf"],
                customer["postal_code"],
                customer["transformer_code"],
                customer["monthly_consumption_kwh"],
                int(customer["has_gd"]),
                customer["gd_received_kwh"],
                customer["gd_injected_kwh"],
            ),
        )


def insert_customer_aggregates(
    connection: sqlite3.Connection,
    aggregates: list[dict[str, Any]],
) -> None:
    for aggregate in aggregates:
        connection.execute(
            """
            INSERT INTO demo_customer_aggregates (
                transformer_code,
                customer_count,
                total_consumption_kwh
            ) VALUES (?, ?, ?)
            """,
            (
                aggregate["transformer_code"],
                aggregate["customer_count"],
                aggregate["total_consumption_kwh"],
            ),
        )


def insert_roof_estimates(
    connection: sqlite3.Connection,
    roof_estimates: list[dict[str, Any]],
) -> None:
    for roof in roof_estimates:
        connection.execute(
            """
            INSERT INTO demo_roof_estimates (
                transformer_code,
                estimated_roofs,
                confidence_score,
                source
            ) VALUES (?, ?, ?, ?)
            """,
            (
                roof["transformer_code"],
                roof["estimated_roofs"],
                roof["confidence_score"],
                roof["source"],
            ),
        )


if __name__ == "__main__":
    main()