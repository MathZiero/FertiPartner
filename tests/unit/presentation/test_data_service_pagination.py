import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app.presentation.streamlit.services.data_service import FertiDataService


def test_fetch_all_paginated_multiple_batches():
    """Verifica se _fetch_all_paginated realiza paginação em múltiplos lotes."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()

    batch_1 = [{"id": i, "val": f"v_{i}"} for i in range(1000)]
    batch_2 = [{"id": i, "val": f"v_{i}"} for i in range(1000, 1450)]

    res_1 = MagicMock(data=batch_1)
    res_2 = MagicMock(data=batch_2)

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.range.side_effect = [
        MagicMock(execute=MagicMock(return_value=res_1)),
        MagicMock(execute=MagicMock(return_value=res_2)),
    ]

    with patch.object(FertiDataService, "_get_client", return_value=mock_client):
        result = FertiDataService._fetch_all_paginated("test_view", batch_size=1000)

    assert len(result) == 1450
    assert result[0]["id"] == 0
    assert result[-1]["id"] == 1449


def test_brazil_external_dependency_includes_zero_production():
    """Verifica que produtos com produção nacional legítima igual a 0.0 (como DAP, SOP e Enxofre)
    são consolidados e preservam a taxa de dependência calculada (100%)."""
    mock_data = [
        {
            "fertilizer_id": 3,
            "fertilizer_name": "Fosfato Diamônico (DAP)",
            "ref_year": 2024,
            "national_production_mt": 0.0,
            "total_imports_mt": 387389.0,
            "total_exports_mt": 0.0,
            "apparent_consumption_mt": 387389.0,
            "external_dependency_pct": 100.0,
        },
        {
            "fertilizer_id": 1,
            "fertilizer_name": "Ureia",
            "ref_year": 2023,
            "national_production_mt": 437680.0,
            "total_imports_mt": 14078513.0,
            "total_exports_mt": 21018.0,
            "apparent_consumption_mt": 14495175.0,
            "external_dependency_pct": 97.13,
        },
    ]

    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value.execute.return_value = MagicMock(data=mock_data)

    with patch.object(FertiDataService, "_get_client", return_value=mock_client):
        # Limpa cache do streamlit se necessário
        FertiDataService.get_brazil_external_dependency.clear()
        df = FertiDataService.get_brazil_external_dependency()

    dap_row = df[df["fertilizer_name"] == "Fosfato Diamônico (DAP)"].iloc[0]
    assert dap_row["is_consolidated"] is True or dap_row["is_consolidated"] == 1
    assert dap_row["data_status"] == "CONSOLIDATED"
    assert dap_row["external_dependency_pct"] == 100.0
    assert dap_row["apparent_consumption_mt"] == 387389.0


def test_price_benchmark_trends_has_map_and_canonical_names():
    """Verifica se o retorno de get_price_benchmark_trends contém MAP e KCL com nomes canônicos e nutrientes corretos."""
    FertiDataService.get_price_benchmark_trends.clear()
    df = FertiDataService.get_price_benchmark_trends()

    assert not df.empty
    nutrients = set(df["nutrient_type"].unique())
    assert "Nitrogenados" in nutrients
    assert "Fosfatados" in nutrients
    assert "Potássicos" in nutrients

    # Verifica se MAP está presente com a nomenclatura canônica exata e ID 2
    map_rows = df[df["fertilizer_id"] == 2]
    assert not map_rows.empty
    assert "Fosfato Monoamônico (MAP)" in map_rows["fertilizer_name"].values
