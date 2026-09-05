"""Testes unitários para as entidades puras da camada de domínio."""

from datetime import date
import pytest
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


def test_fertilizer_entity_creation():
    """Valida instanciação e atributos da entidade Fertilizer."""
    fert = FertilizerEntity(
        id=1,
        slug="ureia",
        canonical_name="Ureia",
        category_name="Fertilizantes Nitrogenados",
        chemical_formula="CO(NH2)2",
        cas_rn="57-13-6",
        description="Fertilizante nitrogenado concentrado",
        typical_nutrients={"N": 46.0},
        synonyms=["Urea", "Carbamide"],
        hs_ncm_codes=["310210"],
    )
    assert fert.slug == "ureia"
    assert fert.canonical_name == "Ureia"
    assert fert.typical_nutrients["N"] == 46.0
    assert "Urea" in fert.synonyms


def test_external_dependency_entity():
    """Valida entidade de dependência externa do Brasil."""
    dep = ExternalDependencyEntity(
        fertilizer_name="Cloreto de Potássio (KCl / MOP)",
        ref_year=2024,
        national_production_mt=350_000.0,
        total_imports_mt=7_000_000.0,
        total_exports_mt=0.0,
        apparent_consumption_mt=7_350_000.0,
        external_dependency_pct=95.24,
    )
    assert dep.external_dependency_pct > 90.0
    assert dep.apparent_consumption_mt == 7_350_000.0


def test_seasonal_pattern_entity():
    """Valida entidade de padrão de sazonalidade."""
    pattern = SeasonalPatternEntity(
        fertilizer_name="Ureia",
        month=8,
        month_name="Agosto",
        average_volume_mt=450_000.0,
        seasonality_index=135.5,
        peak_status="Pico (Safra de Verão)",
        crop_calendar_phase="Janela de Compras e Adubação de Base",
    )
    assert pattern.month == 8
    assert pattern.seasonality_index > 100.0
    assert "Safra" in pattern.peak_status


def test_market_insight_entity():
    """Valida entidade de insight automático de inteligência de mercado."""
    insight = MarketInsightEntity(
        id="INS-001",
        title="Alerta de Dependência Crítica de Potássio",
        category="Dependência Externa",
        severity=InsightSeverity.CRITICAL,
        message="A dependência externa de KCl atingiu 95.2%, superando o limiar de alerta estratégico.",
        metric_name="Taxa de Dependência",
        metric_value="95.2%",
        baseline_value="Meta Plano Nacional: < 50%",
        recommended_action="Diversificar parceiros de suprimento e acelerar projetos de exploração na Bacia do Amazonas.",
    )
    assert insight.severity == InsightSeverity.CRITICAL
    assert insight.is_critical is True
