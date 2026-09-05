"""Camada de domínio: entidades de negócio, regras puras, validadores e contratos."""

from app.domain.entities import (
    FertilizerEntity,
    PriceRecordEntity,
    TradeRecordEntity,
    ProductionRecordEntity,
    ExternalDependencyEntity,
    SeasonalPatternEntity,
    MarketInsightEntity,
    InsightSeverity,
)
from app.domain.calculators import (
    calculate_apparent_consumption,
    calculate_external_dependency_pct,
    calculate_seasonality_indices,
    calculate_mom_change_pct,
    calculate_moving_average,
)
from app.domain.insights import MarketInsightsEngine
from app.domain.validators import DomainValidationError, validate_non_negative_number, validate_date_range

__all__ = [
    "FertilizerEntity",
    "PriceRecordEntity",
    "TradeRecordEntity",
    "ProductionRecordEntity",
    "ExternalDependencyEntity",
    "SeasonalPatternEntity",
    "MarketInsightEntity",
    "InsightSeverity",
    "calculate_apparent_consumption",
    "calculate_external_dependency_pct",
    "calculate_seasonality_indices",
    "calculate_mom_change_pct",
    "calculate_moving_average",
    "MarketInsightsEngine",
    "DomainValidationError",
    "validate_non_negative_number",
    "validate_date_range",
]
