from src.aerial_housing_detection.integrations.gd.contracts import (
    GDMonthlyBalance,
    GDQuery,
    GDSourceType,
)
from src.aerial_housing_detection.integrations.gd.memory_provider import (
    InMemoryGDProvider,
)
from src.aerial_housing_detection.integrations.gd.normalizer import (
    GDToSolarEstimateNormalizer,
)


def test_in_memory_gd_provider_filters_by_transformer() -> None:
    provider = InMemoryGDProvider(
        balances=[
            GDMonthlyBalance(
                reference_month="2026-05",
                area_id="area-001",
                transformer_code="TR-001",
                feeder_code="AL-01",
                substation_code="SE-01",
                gd_customer_count=8,
                installed_capacity_kwp=42.5,
                generated_energy_kwh=3200.0,
                consumed_energy_kwh=2100.0,
                injected_to_grid_kwh=1100.0,
                received_from_grid_kwh=900.0,
                compensated_energy_kwh=700.0,
                source_type=GDSourceType.API,
                confidence_score=0.95,
            ),
            GDMonthlyBalance(
                reference_month="2026-05",
                area_id="area-002",
                transformer_code="TR-002",
                feeder_code="AL-01",
                substation_code="SE-01",
                gd_customer_count=2,
                installed_capacity_kwp=12.0,
                generated_energy_kwh=850.0,
                consumed_energy_kwh=600.0,
                injected_to_grid_kwh=250.0,
                received_from_grid_kwh=450.0,
                compensated_energy_kwh=150.0,
                source_type=GDSourceType.API,
                confidence_score=0.9,
            ),
        ]
    )

    balances = provider.get_monthly_balance(
        GDQuery(
            reference_month="2026-05",
            transformer_code="TR-001",
        )
    )

    assert len(balances) == 1
    assert balances[0].area_id == "area-001"
    assert balances[0].injected_to_grid_kwh == 1100.0


def test_gd_monthly_balance_computes_derived_values() -> None:
    balance = GDMonthlyBalance(
        reference_month="2026-05",
        area_id="area-001",
        transformer_code="TR-001",
        feeder_code="AL-01",
        substation_code="SE-01",
        gd_customer_count=8,
        installed_capacity_kwp=42.5,
        generated_energy_kwh=3200.0,
        consumed_energy_kwh=2100.0,
        injected_to_grid_kwh=1100.0,
        received_from_grid_kwh=900.0,
        compensated_energy_kwh=700.0,
        source_type=GDSourceType.API,
        confidence_score=0.95,
    )

    assert balance.net_injected_energy_kwh == 200.0
    assert balance.self_consumption_kwh == 2100.0
    assert balance.has_relevant_grid_injection


def test_gd_normalizer_converts_balance_to_solar_estimate() -> None:
    normalizer = GDToSolarEstimateNormalizer()
    balances = [
        GDMonthlyBalance(
            reference_month="2026-05",
            area_id="area-001",
            transformer_code="TR-001",
            feeder_code="AL-01",
            substation_code="SE-01",
            gd_customer_count=8,
            installed_capacity_kwp=42.5,
            generated_energy_kwh=3200.0,
            consumed_energy_kwh=2100.0,
            injected_to_grid_kwh=1100.0,
            received_from_grid_kwh=900.0,
            compensated_energy_kwh=700.0,
            source_type=GDSourceType.API,
            confidence_score=0.95,
        )
    ]

    estimates = normalizer.normalize(balances)

    assert len(estimates) == 1
    assert estimates[0].area_id == "area-001"
    assert estimates[0].solar_panel_count == 8
    assert estimates[0].estimated_solar_area_m2 == 255.0
    assert estimates[0].estimated_generation_kwh == 1100.0
    assert estimates[0].confidence_score == 0.95
