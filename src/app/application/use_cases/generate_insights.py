"""Caso de uso para geração automática de alertas e insights de mercado (RF23)."""

from datetime import datetime
from typing import Any
from app.application.dtos import MarketInsightDTO
from app.domain.entities import ExternalDependencyEntity
from app.domain.insights import MarketInsightsEngine


class GenerateMarketInsightsUseCase:
    """Orquestra a análise multivariada de séries e gera os alertas de inteligência."""

    def __init__(self, engine: MarketInsightsEngine | None = None) -> None:
        self.engine = engine or MarketInsightsEngine()

    def execute(
        self,
        dependencies: list[ExternalDependencyEntity] | None = None,
        price_records: list[dict[str, Any]] | None = None,
        current_month: int | None = None,
    ) -> list[MarketInsightDTO]:
        """Executa a varredura analítica e retorna a lista consolidada de insights.

        Args:
            dependencies: Lista opcional de registros de dependência.
            price_records: Lista opcional de cotações recentes para análise de volatilidade.
            current_month: Mês de referência (padrão: mês atual do sistema).

        Returns:
            Lista ordenada de MarketInsightDTO por gravidade (Críticos primeiro).
        """
        # Dados padrão caso não fornecidos externamente
        if dependencies is None:
            dependencies = [
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

        if price_records is None:
            price_records = [
                {"fertilizer": "Ureia", "date": "2024-08-01", "price": 415.0, "mom_pct": 9.2},
                {"fertilizer": "KCl", "date": "2024-08-01", "price": 310.0, "mom_pct": -5.5},
            ]

        if current_month is None:
            current_month = datetime.now().month

        # Execução das regras no motor de domínio
        all_domain_insights = []
        all_domain_insights.extend(self.engine.evaluate_dependency_risks(dependencies))
        all_domain_insights.extend(self.engine.evaluate_price_volatility(price_records))
        all_domain_insights.extend(self.engine.evaluate_crop_calendar_window(current_month))

        # Conversão para DTOs
        dto_list = [
            MarketInsightDTO(
                id=i.id,
                title=i.title,
                category=i.category,
                severity=i.severity.value,
                message=i.message,
                metric_name=i.metric_name,
                metric_value=i.metric_value,
                baseline_value=i.baseline_value,
                recommended_action=i.recommended_action,
                is_critical=i.is_critical,
            )
            for i in all_domain_insights
        ]

        # Ordenação: Críticos primeiro, seguidos de Atenção e Informativos
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        dto_list.sort(key=lambda x: severity_order.get(x.severity, 9))

        return dto_list
