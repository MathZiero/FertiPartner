"""Testes unitários para a camada de casos de uso (Application layer)."""

import pandas as pd
from app.application.use_cases.calculate_seasonality import CalculateSeasonalityUseCase
from app.application.use_cases.generate_insights import GenerateMarketInsightsUseCase
from app.application.dtos import SeasonalPatternDTO, MarketInsightDTO


def test_calculate_seasonality_use_case():
    """Garante que o caso de uso calcula as curvas sazonais de importação por mês."""
    use_case = CalculateSeasonalityUseCase()
    patterns = use_case.execute(fertilizer_name="Todos")
    assert isinstance(patterns, list)
    assert len(patterns) == 12
    assert all(isinstance(p, SeasonalPatternDTO) for p in patterns)

    # Meses de pico (julho/agosto/setembro) devem ter índice superior a 100
    picos = [p for p in patterns if p.month in (7, 8, 9)]
    for p in picos:
        assert p.seasonality_index > 100.0


def test_generate_market_insights_use_case():
    """Garante que o caso de uso de insights orquestra as análises e retorna DTOs."""
    use_case = GenerateMarketInsightsUseCase()
    insights = use_case.execute()
    assert isinstance(insights, list)
    assert len(insights) > 0
    assert all(isinstance(i, MarketInsightDTO) for i in insights)
