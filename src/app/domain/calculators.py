"""Funções puras de cálculo de indicadores de negócio da cadeia de fertilizantes."""

from typing import Sequence


def calculate_apparent_consumption(
    national_production_mt: float,
    total_imports_mt: float,
    total_exports_mt: float,
) -> float:
    """Calcula o consumo aparente nacional (Produção + Importações - Exportações)."""
    return max(0.0, float(national_production_mt) + float(total_imports_mt) - float(total_exports_mt))


def calculate_external_dependency_pct(
    total_imports_mt: float,
    apparent_consumption_mt: float,
) -> float:
    """Calcula a taxa percentual de dependência externa (Importações / Consumo Aparente * 100)."""
    if apparent_consumption_mt <= 0.0:
        return 0.0
    return round((float(total_imports_mt) / float(apparent_consumption_mt)) * 100.0, 2)


def calculate_seasonality_indices(monthly_volumes: dict[int, float]) -> dict[int, float]:
    """Calcula índices sazonais mensais com base 100 (média anual = 100.0).

    Args:
        monthly_volumes: Mapeamento de mês (1 a 12) para volume médio movimentado.

    Returns:
        Mapeamento de mês para índice sazonal percentual em base 100.
    """
    if not monthly_volumes:
        return {m: 100.0 for m in range(1, 13)}

    total = sum(monthly_volumes.values())
    count = len(monthly_volumes)
    mean_volume = total / count if count > 0 else 1.0

    if mean_volume <= 0.0:
        return {m: 100.0 for m in monthly_volumes}

    return {
        month: round((vol / mean_volume) * 100.0, 2)
        for month, vol in monthly_volumes.items()
    }


def calculate_mom_change_pct(current_val: float, previous_val: float) -> float:
    """Calcula a variação percentual mês a mês (MoM)."""
    if previous_val == 0.0:
        return 0.0
    return round(((float(current_val) - float(previous_val)) / float(previous_val)) * 100.0, 2)


def calculate_moving_average(
    series: Sequence[float],
    window: int = 3,
) -> list[float | None]:
    """Calcula média móvel simples de uma série temporal."""
    if not series:
        return []
    if window <= 0:
        raise ValueError("O tamanho da janela deve ser maior que zero.")

    result: list[float | None] = []
    for i in range(len(series)):
        if i + 1 < window:
            # Janela incompleta: média parcial do período disponível
            sub = series[: i + 1]
            result.append(round(sum(sub) / len(sub), 2))
        else:
            sub = series[i + 1 - window : i + 1]
            result.append(round(sum(sub) / window, 2))
    return result
