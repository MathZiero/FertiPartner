"""Testes unitários para as regras puras de cálculo do domínio."""

import pytest
from app.domain.calculators import (
    calculate_apparent_consumption,
    calculate_external_dependency_pct,
    calculate_seasonality_indices,
    calculate_mom_change_pct,
    calculate_moving_average,
)


def test_calculate_apparent_consumption():
    """Valida cálculo do consumo aparente: Produção + Importação - Exportação."""
    cons = calculate_apparent_consumption(
        national_production_mt=1_000_000.0,
        total_imports_mt=9_000_000.0,
        total_exports_mt=200_000.0,
    )
    assert cons == 9_800_000.0


def test_calculate_external_dependency_pct():
    """Valida cálculo da taxa de dependência externa."""
    rate = calculate_external_dependency_pct(
        total_imports_mt=8_500_000.0,
        apparent_consumption_mt=10_000_000.0,
    )
    assert rate == 85.0

    # Divisão por zero ou consumo zero
    assert calculate_external_dependency_pct(1_000.0, 0.0) == 0.0
    assert calculate_external_dependency_pct(0.0, 1_000.0) == 0.0


def test_calculate_seasonality_indices():
    """Valida decomposição de índice sazonal com base 100."""
    # 12 meses com volumes simulados
    monthly_data = {
        1: 50.0, 2: 60.0, 3: 70.0, 4: 80.0,
        5: 100.0, 6: 120.0, 7: 150.0, 8: 160.0,
        9: 140.0, 10: 110.0, 11: 90.0, 12: 70.0,
    }
    indices = calculate_seasonality_indices(monthly_data)
    assert len(indices) == 12
    # Mês 8 (160) deve ter o maior índice (> 150)
    assert indices[8] > 150.0
    # Mês 1 (50) deve ter o menor índice (< 60)
    assert indices[1] < 60.0


def test_calculate_mom_change_pct():
    """Valida variação percentual mês a mês."""
    assert calculate_mom_change_pct(110.0, 100.0) == 10.0
    assert calculate_mom_change_pct(90.0, 100.0) == -10.0
    assert calculate_mom_change_pct(100.0, 0.0) == 0.0


def test_calculate_moving_average():
    """Valida média móvel com janela definida."""
    values = [100.0, 110.0, 120.0, 130.0]
    ma = calculate_moving_average(values, window=3)
    assert len(ma) == 4
    # Primeiro e segundo valores na janela 3 recebem média parcial ou None
    assert ma[2] == pytest.approx(110.0)  # (100+110+120)/3
    assert ma[3] == pytest.approx(120.0)  # (110+120+130)/3
