"""Entidades puras e imutáveis da camada de domínio do FertiPartner."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class InsightSeverity(str, Enum):
    """Níveis de severidade para alertas de inteligência de mercado."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True)
class FertilizerEntity:
    """Entidade central de fertilizante com especificações físico-químicas."""
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
    is_active: bool = True


@dataclass(frozen=True)
class PriceRecordEntity:
    """Cotação histórica de preço e benchmark de mercado."""
    fertilizer_name: str
    benchmark_name: str
    price_date: date | str
    standard_price_usd_per_mt: float
    hub_port_name: str | None = None
    incoterm: str | None = None
    month_over_month_pct_change: float | None = None
    moving_avg_3m_usd: float | None = None


@dataclass(frozen=True)
class TradeRecordEntity:
    """Fluxo comercial bilateral consolidado."""
    fertilizer_name: str
    flow_type: str  # IMPORT ou EXPORT
    exporter_country: str
    importer_country: str
    trade_year: int
    trade_month: int | None = None
    total_quantity_mt: float = 0.0
    total_value_usd: float = 0.0
    avg_usd_per_mt: float = 0.0


@dataclass(frozen=True)
class ProductionRecordEntity:
    """Registro de volume de produção e ranking mundial."""
    fertilizer_name: str
    country_name: str
    country_iso3: str
    production_year: int
    standard_quantity_mt: float
    global_market_share_pct: float
    rank_position: int


@dataclass(frozen=True)
class ExternalDependencyEntity:
    """Indicadores consolidados de dependência externa e balanço nacional."""
    fertilizer_name: str
    ref_year: int
    national_production_mt: float
    total_imports_mt: float
    total_exports_mt: float
    apparent_consumption_mt: float
    external_dependency_pct: float


@dataclass(frozen=True)
class SeasonalPatternEntity:
    """Índice e padrão sazonal mensal de compras e suprimento (RF10)."""
    fertilizer_name: str
    month: int
    month_name: str
    average_volume_mt: float
    seasonality_index: float  # Base 100
    peak_status: str  # Pico, Vale, Regular
    crop_calendar_phase: str  # Safra de Verão, Safrinha, Entressafra


@dataclass(frozen=True)
class MarketInsightEntity:
    """Alerta ou insight de anomalia gerado pelo sistema (RF23)."""
    id: str
    title: str
    category: str
    severity: InsightSeverity
    message: str
    metric_name: str
    metric_value: str
    baseline_value: str
    recommended_action: str

    @property
    def is_critical(self) -> bool:
        return self.severity == InsightSeverity.CRITICAL
