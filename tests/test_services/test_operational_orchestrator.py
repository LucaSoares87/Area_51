from src.aerial_housing_detection.domain.territory_enrichment import (
    CrasContext,
    IbgeContext,
)
from src.aerial_housing_detection.integrations.concessionaria.contracts import (
    ConcessionariaAsset,
)
from src.aerial_housing_detection.integrations.concessionaria.memory_provider import (
    InMemoryConcessionariaProvider,
)
from src.aerial_housing_detection.integrations.cras.memory_provider import (
    InMemoryCrasProvider,
)
from src.aerial_housing_detection.integrations.ibge.memory_provider import (
    InMemoryIbgeProvider,
)
from src.aerial_housing_detection.services.operational_orchestrator import (
    OperationalOrchestrator,
)


def test_orchestrator_analyzes_transformer_with_real_data_contract() -> None:
    orchestrator = _build_orchestrator()

    result = orchestrator.analyze_transformer("TR-001")

    assert result.asset is not None
    assert result.asset.transformer_code == "TR-001"
    assert result.inference is not None
    assert result.inference.priority == "Alta"
    assert result.territory is not None
    assert result.territory.source_strategy == "coordinates"
    assert result.territory.ibge is not None
    assert result.territory.cras is not None


def test_orchestrator_returns_empty_result_when_transformer_not_found() -> None:
    orchestrator = _build_orchestrator()

    result = orchestrator.analyze_transformer("TR-999")

    assert result.asset is None
    assert result.inference is None
    assert result.territory is None


def test_orchestrator_finds_nearest_asset_by_coordinates() -> None:
    orchestrator = _build_orchestrator()

    result = orchestrator.analyze_coordinates(-7.9401, -34.8734)

    assert result.asset is not None
    assert result.asset.transformer_code == "TR-001"
    assert result.inference is not None
    assert result.territory is not None


def _build_orchestrator() -> OperationalOrchestrator:
    asset = ConcessionariaAsset(
        transformer_code="TR-001",
        feeder_code="AL-01",
        substation_code="SE-01",
        latitude=-7.9401,
        longitude=-34.8734,
        city="Recife",
        neighborhood="Boa Viagem",
        postal_code="51000-000",
        customer_count=74,
        transformer_input_kwh=176450,
        billed_consumption_kwh=138000,
        gd_injected_kwh=12600,
        technical_loss_kwh=0,
    )

    return OperationalOrchestrator(
        concessionaria_provider=InMemoryConcessionariaProvider([asset]),
        ibge_provider=InMemoryIbgeProvider(
            IbgeContext(
                sector_id="260790105000001",
                population=1200,
                households=380,
                average_income=1850.0,
                vulnerability_index=0.62,
            )
        ),
        cras_provider=InMemoryCrasProvider(
            CrasContext(
                territory_id="CRAS-REC-001",
                cras_name="CRAS Boa Viagem",
                vulnerability_level="Média/Alta",
                families_assisted=420,
                vulnerability_index=0.68,
            )
        ),
    )
