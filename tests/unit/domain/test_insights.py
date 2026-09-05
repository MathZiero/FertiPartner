"""Testes unitários para o motor determinístico de insights de mercado (RF23)."""

from app.domain.entities import ExternalDependencyEntity, InsightSeverity
from app.domain.insights import MarketInsightsEngine


def test_detect_dependency_alerts():
    """Garante geração de alertas quando dependência externa ultrapassa patamares críticos."""
    deps = [
        ExternalDependencyEntity(
            fertilizer_name="Cloreto de Potássio (KCl / MOP)",
            ref_year=2024,
            national_production_mt=350_000.0,
            total_imports_mt=7_000_000.0,
            total_exports_mt=0.0,
            apparent_consumption_mt=7_350_000.0,
            external_dependency_pct=95.2,
        ),
        ExternalDependencyEntity(
            fertilizer_name="Ureia",
            ref_year=2024,
            national_production_mt=800_000.0,
            total_imports_mt=7_200_000.0,
            total_exports_mt=0.0,
            apparent_consumption_mt=8_000_000.0,
            external_dependency_pct=90.0,
        ),
        ExternalDependencyEntity(
            fertilizer_name="Fosfato Monoamônico (MAP)",
            ref_year=2024,
            national_production_mt=1_500_000.0,
            total_imports_mt=3_500_000.0,
            total_exports_mt=0.0,
            apparent_consumption_mt=5_000_000.0,
            external_dependency_pct=70.0,
        ),
    ]

    engine = MarketInsightsEngine()
    alerts = engine.evaluate_dependency_risks(deps)
    assert len(alerts) >= 2
    critical_alerts = [a for a in alerts if a.severity == InsightSeverity.CRITICAL]
    assert len(critical_alerts) >= 2  # KCl e Ureia (> 85%)


def test_detect_price_spikes():
    """Garante geração de alertas para variações atípicas de preço."""
    price_records = [
        {"fertilizer": "Ureia", "date": "2024-07-01", "price": 380.0, "mom_pct": 2.1},
        {"fertilizer": "Ureia", "date": "2024-08-01", "price": 435.0, "mom_pct": 14.5},  # Spike!
        {"fertilizer": "MAP", "date": "2024-08-01", "price": 540.0, "mom_pct": -6.8},  # Queda acentuada!
    ]

    engine = MarketInsightsEngine()
    price_alerts = engine.evaluate_price_volatility(price_records)
    assert len(price_alerts) >= 2
    assert any("alta" in a.title.lower() or "spike" in a.title.lower() for a in price_alerts)
    assert any("queda" in a.title.lower() for a in price_alerts)


def test_detect_crop_calendar_window():
    """Garante identificação da janela sazonal atual (Safra ou Safrinha)."""
    engine = MarketInsightsEngine()
    # Mês 8 (Agosto) -> Janela de pico da Safra de Verão
    safra_insights = engine.evaluate_crop_calendar_window(current_month=8)
    assert len(safra_insights) > 0
    assert any("Safra" in s.title for s in safra_insights)
