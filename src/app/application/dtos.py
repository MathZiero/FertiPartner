"""Objetos de Transferência de Dados (DTOs) da camada de aplicação."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FertilizerDTO:
    """DTO com dados cadastrais e nutricionais de fertilizante."""
    id: int
    slug: str
    canonical_name: str
    category_name: str
    chemical_formula: str | None = None
    cas_rn: str | None = None
    description: str | None = None
    typical_nutrients: dict[str, float] = field(default_factory=dict)
    synonyms: list[str] = field(default_factory=list)
    hs_ncm_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExternalDependencyDTO:
    """DTO consolidado de dependência externa e consumo aparente."""
    fertilizer_name: str
    ref_year: int
    national_production_mt: float
    total_imports_mt: float
    total_exports_mt: float
    apparent_consumption_mt: float
    external_dependency_pct: float


@dataclass(frozen=True)
class SeasonalPatternDTO:
    """DTO do perfil de sazonalidade mensal (RF10)."""
    fertilizer_name: str
    month: int
    month_name: str
    average_volume_mt: float
    seasonality_index: float
    peak_status: str
    crop_calendar_phase: str


@dataclass(frozen=True)
class MarketInsightDTO:
    """DTO de alerta ou insight analítico de inteligência de mercado (RF23)."""
    id: str
    title: str
    category: str
    severity: str
    message: str
    metric_name: str
    metric_value: str
    baseline_value: str
    recommended_action: str
    is_critical: bool
