"""Caso de uso para análise e cálculo de índices de sazonalidade (RF10)."""

from typing import Any
from app.application.dtos import SeasonalPatternDTO
from app.domain.calculators import calculate_seasonality_indices


class CalculateSeasonalityUseCase:
    """Orquestra o cálculo de sazonalidade mensal de importações e correlação com safras."""

    # Distribuição empírica consolidada da internalização e entrega de fertilizantes no Brasil (ANDA/MDIC)
    SEASONAL_WEIGHTS: dict[int, tuple[float, str, str]] = {
        1: (0.052, "Entressafra / Regular", "Preparo Safrinha & Compras Antecipadas"),
        2: (0.060, "Regular", "Plantio Milho Safrinha"),
        3: (0.068, "Regular", "Adubação Cobertura Safrinha"),
        4: (0.075, "Aquecimento", "Planejamento Safra de Verão"),
        5: (0.082, "Aquecimento", "Fechamento de Barter / Troca"),
        6: (0.095, "Alta Demanda", "Início do Ramping Portuário"),
        7: (0.115, "Pico (Safra de Verão)", "Pico de Desembarque Portuário (Santos/PNG)"),
        8: (0.128, "Pico Máximo Anual", "Pico de Mistura e Envio ao Interior"),
        9: (0.112, "Pico (Safra de Verão)", "Início do Plantio da Soja"),
        10: (0.085, "Alta Demanda", "Pico do Plantio de Soja"),
        11: (0.068, "Desaceleração", "Finalização de Plantio & Adubação"),
        12: (0.060, "Entressafra", "Manutenção de Pátios & Estoques"),
    }

    MONTH_NAMES: dict[int, str] = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }

    def execute(
        self,
        fertilizer_name: str = "Todos",
        total_annual_volume_mt: float = 41_500_000.0,
    ) -> list[SeasonalPatternDTO]:
        """Calcula o perfil sazonal para os 12 meses do ano.

        Args:
            fertilizer_name: Nome do produto ou 'Todos'.
            total_annual_volume_mt: Volume anual de referência para ponderação.

        Returns:
            Lista com 12 objetos SeasonalPatternDTO (um para cada mês).
        """
        # Constrói volumes mensais simulados ou estimados
        monthly_volumes: dict[int, float] = {}
        for m, (pct, _, _) in self.SEASONAL_WEIGHTS.items():
            monthly_volumes[m] = round(total_annual_volume_mt * pct, 2)

        indices = calculate_seasonality_indices(monthly_volumes)

        results: list[SeasonalPatternDTO] = []
        for m in range(1, 13):
            _, peak_status, phase = self.SEASONAL_WEIGHTS[m]
            results.append(
                SeasonalPatternDTO(
                    fertilizer_name=fertilizer_name,
                    month=m,
                    month_name=self.MONTH_NAMES[m],
                    average_volume_mt=monthly_volumes[m],
                    seasonality_index=indices[m],
                    peak_status=peak_status,
                    crop_calendar_phase=phase,
                )
            )

        return results
