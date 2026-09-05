"""Módulo de Casos de Uso (Use Cases) da camada de aplicação."""

from app.application.use_cases.calculate_seasonality import CalculateSeasonalityUseCase
from app.application.use_cases.generate_insights import GenerateMarketInsightsUseCase

__all__ = [
    "CalculateSeasonalityUseCase",
    "GenerateMarketInsightsUseCase",
]
