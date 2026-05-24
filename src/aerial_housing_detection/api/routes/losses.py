from fastapi import APIRouter, Query

from src.aerial_housing_detection.api.schemas.losses import (
    LossRankingResponse,
    LossRecordResponse,
    LossSummaryResponse,
    SeedLossesRequest,
)
from src.aerial_housing_detection.domain.losses import LossCalculator, OperationalArea
from src.aerial_housing_detection.storage.loss_repository import LossRepository

router = APIRouter(prefix="/losses", tags=["losses"])


def get_repository() -> LossRepository:
    repository = LossRepository()
    repository.initialize()
    return repository


@router.get("/ranking", response_model=LossRankingResponse)
def get_loss_ranking(
    reference_month: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> LossRankingResponse:
    repository = get_repository()
    records = repository.list_monthly_loss_records(reference_month=reference_month)
    limited_records = records[:limit]

    return LossRankingResponse(
        reference_month=reference_month,
        total_records=len(records),
        records=[LossRecordResponse(**record) for record in limited_records],
    )


@router.get("/summary", response_model=LossSummaryResponse)
def get_loss_summary(
    reference_month: str | None = Query(default=None),
) -> LossSummaryResponse:
    repository = get_repository()
    records = repository.list_monthly_loss_records(reference_month=reference_month)

    total_areas = len(records)
    critical_areas = sum(1 for record in records if record["risk_level"] == "critical")
    high_risk_areas = sum(1 for record in records if record["risk_level"] == "high")
    estimated_loss_kwh = sum(float(record["estimated_loss_kwh"]) for record in records)

    if records:
        average_loss_percent = sum(
            float(record["estimated_loss_percent"]) for record in records
        ) / len(records)
        top_priority_score = max(float(record["priority_score"]) for record in records)
    else:
        average_loss_percent = 0.0
        top_priority_score = 0.0

    return LossSummaryResponse(
        reference_month=reference_month,
        total_areas=total_areas,
        critical_areas=critical_areas,
        high_risk_areas=high_risk_areas,
        estimated_loss_kwh=round(estimated_loss_kwh, 4),
        average_loss_percent=round(average_loss_percent, 6),
        top_priority_score=round(top_priority_score, 4),
    )


@router.post("/seed", response_model=LossRankingResponse, status_code=201)
def seed_loss_records(request: SeedLossesRequest) -> LossRankingResponse:
    repository = get_repository()
    calculator = LossCalculator()

    areas = [
        OperationalArea(
            area_id="area-001",
            transformer_code="TR-001",
            latitude=-7.9401,
            longitude=-34.8734,
            neighborhood="Maranguape I",
            city="Paulista",
            feeder="AL-01",
            customer_count=120,
        ),
        OperationalArea(
            area_id="area-002",
            transformer_code="TR-002",
            latitude=-7.9512,
            longitude=-34.8821,
            neighborhood="Janga",
            city="Paulista",
            feeder="AL-02",
            customer_count=98,
        ),
        OperationalArea(
            area_id="area-003",
            transformer_code="TR-003",
            latitude=-7.9315,
            longitude=-34.8652,
            neighborhood="Centro",
            city="Paulista",
            feeder="AL-03",
            customer_count=150,
        ),
    ]

    energy_pairs = {
        "area-001": (12000.0, 8300.0),
        "area-002": (9400.0, 7800.0),
        "area-003": (15000.0, 8800.0),
    }

    for area in areas:
        repository.save_area(area)
        injected_energy_kwh, billed_consumption_kwh = energy_pairs[area.area_id]
        record = calculator.calculate_record(
            area_id=area.area_id,
            reference_month=request.reference_month,
            injected_energy_kwh=injected_energy_kwh,
            billed_consumption_kwh=billed_consumption_kwh,
        )
        repository.save_monthly_loss_record(record)

    records = repository.list_monthly_loss_records(
        reference_month=request.reference_month,
    )

    return LossRankingResponse(
        reference_month=request.reference_month,
        total_records=len(records),
        records=[LossRecordResponse(**record) for record in records],
    )
