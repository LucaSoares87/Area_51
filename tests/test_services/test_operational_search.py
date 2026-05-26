from pathlib import Path

from src.aerial_housing_detection.domain.operational_search import (
    CustomerOperationalLink,
    OperationalAsset,
    OperationalSearchType,
)
from src.aerial_housing_detection.services.operational_search import (
    OperationalSearchService,
)
from src.aerial_housing_detection.storage.operational_repository import (
    OperationalRepository,
)


def test_operational_search_finds_asset_by_customer(tmp_path: Path) -> None:
    repository = OperationalRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

    asset = OperationalAsset(
        area_id="area-001",
        transformer_code="TR-001",
        feeder_code="AL-01",
        substation_code="SE-01",
        latitude=-7.9401,
        longitude=-34.8734,
        city="Paulista",
        neighborhood="Maranguape I",
        installed_power_kva=75.0,
        operational_status="active",
    )
    link = CustomerOperationalLink(
        customer_id="UC-001",
        area_id="area-001",
        transformer_code="TR-001",
        feeder_code="AL-01",
        substation_code="SE-01",
        reference_month="2026-05",
        customer_status="active",
        consumer_class="residential",
    )

    repository.save_asset(asset)
    repository.save_customer_link(link)

    service = OperationalSearchService(repository=repository)
    result = service.search_by_customer(
        customer_id="UC-001",
        reference_month="2026-05",
    )

    assert result.search_type == OperationalSearchType.CUSTOMER
    assert result.asset is not None
    assert result.asset.transformer_code == "TR-001"
    assert result.customer_link is not None
    assert result.customer_link.customer_id == "UC-001"


def test_operational_search_finds_asset_by_transformer(tmp_path: Path) -> None:
    repository = OperationalRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

    repository.save_asset(
        OperationalAsset(
            area_id="area-001",
            transformer_code="TR-001",
            feeder_code="AL-01",
            substation_code="SE-01",
            latitude=-7.9401,
            longitude=-34.8734,
            city="Paulista",
            neighborhood="Maranguape I",
        )
    )

    service = OperationalSearchService(repository=repository)
    result = service.search_by_transformer("TR-001")

    assert result.search_type == OperationalSearchType.TRANSFORMER
    assert result.asset is not None
    assert result.asset.area_id == "area-001"


def test_operational_search_finds_assets_by_feeder(tmp_path: Path) -> None:
    repository = OperationalRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

    repository.save_asset(
        OperationalAsset(
            area_id="area-001",
            transformer_code="TR-001",
            feeder_code="AL-01",
            substation_code="SE-01",
            latitude=-7.9401,
            longitude=-34.8734,
            city="Paulista",
            neighborhood="Maranguape I",
        )
    )
    repository.save_asset(
        OperationalAsset(
            area_id="area-002",
            transformer_code="TR-002",
            feeder_code="AL-01",
            substation_code="SE-01",
            latitude=-7.9512,
            longitude=-34.8821,
            city="Paulista",
            neighborhood="Janga",
        )
    )

    service = OperationalSearchService(repository=repository)
    results = service.search_by_feeder("AL-01")

    assert len(results) == 2
    assert all(result.search_type == OperationalSearchType.FEEDER for result in results)


def test_operational_search_finds_nearest_asset_by_coordinates(
    tmp_path: Path,
) -> None:
    repository = OperationalRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

    repository.save_asset(
        OperationalAsset(
            area_id="area-001",
            transformer_code="TR-001",
            feeder_code="AL-01",
            substation_code="SE-01",
            latitude=-7.9401,
            longitude=-34.8734,
            city="Paulista",
            neighborhood="Maranguape I",
        )
    )

    service = OperationalSearchService(repository=repository)
    result = service.search_by_coordinates(
        latitude=-7.9402,
        longitude=-34.8735,
    )

    assert result.search_type == OperationalSearchType.COORDINATES
    assert result.asset is not None
    assert result.asset.transformer_code == "TR-001"
    assert result.distance_meters is not None
    assert result.distance_meters > 0
