"""Testes unitários para o script smart_collect.py.

Cobre os comportamentos críticos de GapDetector, SmartCollector e CollectionReport
sem dependência de banco real, rede ou APIs externas.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch, call
import pytest

# Garante que scripts/ e src/ estejam no path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.smart_collect import (
    GapDetector,
    SmartCollector,
    CollectionReport,
    DatasetGapResult,
    SourceConfig,
    SOURCE_CONFIGS,
    _compute_missing_years,
    _compute_missing_months,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_supabase():
    """Mock do client Supabase."""
    return MagicMock()


@pytest.fixture
def gap_detector(mock_supabase):
    """GapDetector com Supabase mockado."""
    return GapDetector(supabase_client=mock_supabase)


@pytest.fixture
def current_year() -> int:
    return datetime.now().year


# ---------------------------------------------------------------------------
# _compute_missing_years — lógica pura, sem dependências externas
# ---------------------------------------------------------------------------

class TestComputeMissingYears:

    def test_retorna_gaps_quando_ha_anos_ausentes_entre_cobertura(self):
        # Arrange
        present = [2010, 2011, 2014, 2015]
        min_year, max_year = 2010, 2015

        # Act
        gaps = _compute_missing_years(present, min_year, max_year)

        # Assert
        assert gaps == [2012, 2013]

    def test_retorna_vazio_quando_cobertura_e_completa(self):
        present = [2010, 2011, 2012, 2013]
        gaps = _compute_missing_years(present, 2010, 2013)
        assert gaps == []

    def test_retorna_todos_os_anos_quando_dataset_vazio(self):
        gaps = _compute_missing_years([], 2020, 2023)
        assert gaps == [2020, 2021, 2022, 2023]

    def test_retorna_anos_anteriores_ao_minimo_existente(self):
        # min_year < menor ano presente → gaps no passado
        present = [2015, 2016]
        gaps = _compute_missing_years(present, 2012, 2016)
        assert 2012 in gaps
        assert 2013 in gaps
        assert 2014 in gaps

    def test_retorna_anos_posteriores_ao_maximo_existente(self):
        present = [2015, 2016]
        gaps = _compute_missing_years(present, 2015, 2018)
        assert 2017 in gaps
        assert 2018 in gaps

    def test_ignora_anos_fora_da_janela_solicitada(self):
        # Anos presentes fora do range não devem distorcer o resultado
        present = [2000, 2010, 2020]
        gaps = _compute_missing_years(present, 2010, 2012)
        assert 2000 not in gaps
        assert 2011 in gaps
        assert 2012 in gaps

    @pytest.mark.parametrize("present,min_y,max_y,expected", [
        ([2022, 2025], 2022, 2025, [2023, 2024]),
        ([2022, 2023, 2024, 2025], 2022, 2025, []),
        ([], 2024, 2024, [2024]),
        ([2024], 2024, 2024, []),
    ])
    def test_casos_parametrizados(self, present, min_y, max_y, expected):
        assert _compute_missing_years(present, min_y, max_y) == expected


# ---------------------------------------------------------------------------
# _compute_missing_months — para Comex Stat e FRED (granularidade mensal)
# ---------------------------------------------------------------------------

class TestComputeMissingMonths:

    def test_retorna_gap_de_meses_ausentes(self):
        # Dados presentes: ano 2022 meses 1-6 e ano 2022 meses 10-12
        present = [(2022, m) for m in range(1, 7)] + [(2022, m) for m in range(10, 13)]
        gaps = _compute_missing_months(present, min_year=2022, max_year=2022)
        assert (2022, 7) in gaps
        assert (2022, 8) in gaps
        assert (2022, 9) in gaps

    def test_retorna_vazio_quando_todos_os_meses_presentes(self):
        present = [(2022, m) for m in range(1, 13)]
        gaps = _compute_missing_months(present, min_year=2022, max_year=2022)
        assert gaps == []

    def test_retorna_todos_os_meses_quando_dataset_vazio(self):
        gaps = _compute_missing_months([], min_year=2023, max_year=2023)
        assert len(gaps) == 12
        assert (2023, 1) in gaps
        assert (2023, 12) in gaps

    def test_cobre_multiplos_anos(self):
        present = [(2021, m) for m in range(1, 13)] + [(2023, m) for m in range(1, 13)]
        gaps = _compute_missing_months(present, min_year=2021, max_year=2023)
        # 2022 inteiro deve estar ausente
        for month in range(1, 13):
            assert (2022, month) in gaps

    def test_nao_retorna_meses_presentes_como_gap(self):
        present = [(2022, m) for m in range(1, 13)]
        gaps = _compute_missing_months(present, min_year=2021, max_year=2022)
        for month in range(1, 13):
            assert (2022, month) not in gaps


# ---------------------------------------------------------------------------
# GapDetector — consultas ao Supabase mockadas
# ---------------------------------------------------------------------------

class TestGapDetectorFaostat:

    def test_detecta_gap_anual_em_production_records(self, gap_detector, mock_supabase, current_year):
        # Arrange: banco retorna anos 2010 e 2014 para fertilizer_id=8
        mock_response = MagicMock()
        mock_response.data = [{"year": 2010}, {"year": 2014}]
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = mock_response

        # Act
        result = gap_detector.detect_faostat_gaps(
            fertilizer_id=8, min_year=2010, max_year=2014
        )

        # Assert
        assert isinstance(result, DatasetGapResult)
        assert result.source == "faostat"
        assert result.fertilizer_id == 8
        assert 2011 in result.missing_years
        assert 2012 in result.missing_years
        assert 2013 in result.missing_years
        assert 2010 not in result.missing_years
        assert 2014 not in result.missing_years

    def test_sem_dados_retorna_todos_os_anos_como_gap(self, gap_detector, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = []
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = mock_response

        result = gap_detector.detect_faostat_gaps(
            fertilizer_id=1, min_year=2020, max_year=2022
        )

        assert result.missing_years == [2020, 2021, 2022]

    def test_sem_gaps_retorna_lista_vazia(self, gap_detector, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = [{"year": y} for y in range(2020, 2023)]
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = mock_response

        result = gap_detector.detect_faostat_gaps(
            fertilizer_id=1, min_year=2020, max_year=2022
        )

        assert result.missing_years == []
        assert result.has_gaps is False


class TestGapDetectorComex:

    def test_detecta_gap_mensal_em_trade_records(self, gap_detector, mock_supabase):
        # Banco tem dados para jan-jun de 2022 e out-dez 2022 → gap em jul/ago/set
        present = [{"year": 2022, "month": m} for m in list(range(1, 7)) + list(range(10, 13))]
        mock_response = MagicMock()
        mock_response.data = present
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = mock_response

        result = gap_detector.detect_comex_gaps(
            fertilizer_id=8, min_year=2022, max_year=2022
        )

        assert result.source == "comex"
        assert (2022, 7) in result.missing_months
        assert (2022, 8) in result.missing_months
        assert (2022, 9) in result.missing_months
        assert (2022, 1) not in result.missing_months

    def test_sem_dados_comex_retorna_todos_os_meses(self, gap_detector, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = []
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = mock_response

        result = gap_detector.detect_comex_gaps(
            fertilizer_id=8, min_year=2023, max_year=2023
        )

        assert len(result.missing_months) == 12


class TestGapDetectorFred:

    def test_detecta_gap_mensal_em_price_records(self, gap_detector, mock_supabase):
        # Banco tem jan-jun 2021, gap em jul-dez 2021
        present = [{"price_date": f"2021-{m:02d}-01"} for m in range(1, 7)]
        mock_response = MagicMock()
        mock_response.data = present
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = mock_response

        result = gap_detector.detect_fred_gaps(
            fertilizer_id=1, min_year=2021, max_year=2021
        )

        assert result.source == "fred"
        assert (2021, 7) in result.missing_months
        assert (2021, 12) in result.missing_months
        assert (2021, 1) not in result.missing_months


class TestGapDetectorComtrade:

    def test_detecta_gap_anual_em_trade_flows(self, gap_detector, mock_supabase):
        mock_response = MagicMock()
        mock_response.data = [{"period": 2018}, {"period": 2022}]
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = mock_response

        result = gap_detector.detect_comtrade_gaps(
            fertilizer_id=1, min_year=2018, max_year=2022
        )

        assert result.source == "comtrade"
        assert 2019 in result.missing_years
        assert 2020 in result.missing_years
        assert 2021 in result.missing_years
        assert 2018 not in result.missing_years


# ---------------------------------------------------------------------------
# DatasetGapResult — propriedades derivadas
# ---------------------------------------------------------------------------

class TestDatasetGapResult:

    def test_has_gaps_true_quando_ha_anos_faltando(self):
        result = DatasetGapResult(
            source="faostat",
            fertilizer_id=1,
            missing_years=[2020, 2021],
            missing_months=[],
        )
        assert result.has_gaps is True

    def test_has_gaps_false_quando_nao_ha_gaps(self):
        result = DatasetGapResult(
            source="faostat",
            fertilizer_id=1,
            missing_years=[],
            missing_months=[],
        )
        assert result.has_gaps is False

    def test_has_gaps_true_quando_ha_meses_faltando(self):
        result = DatasetGapResult(
            source="comex",
            fertilizer_id=8,
            missing_years=[],
            missing_months=[(2022, 7), (2022, 8)],
        )
        assert result.has_gaps is True

    def test_total_periods_soma_anos_e_meses(self):
        result = DatasetGapResult(
            source="comex",
            fertilizer_id=1,
            missing_years=[2020],
            missing_months=[(2021, 3), (2021, 4)],
        )
        assert result.total_periods == 3


# ---------------------------------------------------------------------------
# CollectionReport — geração de Markdown
# ---------------------------------------------------------------------------

class TestCollectionReport:

    def test_to_markdown_contem_cabecalho(self):
        report = CollectionReport(results=[])
        md = report.to_markdown()
        assert "FertiPartner" in md or "Coleta" in md

    def test_to_markdown_indica_sem_gaps_quando_vazio(self):
        results = [
            DatasetGapResult("faostat", 1, [], []),
            DatasetGapResult("comex", 1, [], []),
        ]
        report = CollectionReport(results=results)
        md = report.to_markdown()
        assert "gap" in md.lower() or "sem gaps" in md.lower() or "0" in md

    def test_to_markdown_lista_gaps_encontrados(self):
        results = [
            DatasetGapResult("faostat", 8, [2021, 2022], []),
        ]
        report = CollectionReport(results=results, collected=[])
        md = report.to_markdown()
        assert "2021" in md
        assert "2022" in md

    def test_to_markdown_retorna_string_nao_vazia(self):
        report = CollectionReport(results=[])
        assert len(report.to_markdown()) > 0

    def test_summary_counts_gaps_and_collected(self):
        results = [
            DatasetGapResult("faostat", 1, [2020, 2021], []),
            DatasetGapResult("comex", 1, [], [(2022, 5)]),
        ]
        report = CollectionReport(results=results, collected=[
            {"source": "faostat", "year": 2020, "status": "SUCESSO", "records": 10},
        ])
        assert report.total_gaps == 3   # 2 anos + 1 mês
        assert report.total_collected == 1


# ---------------------------------------------------------------------------
# SOURCE_CONFIGS — validação de configuração estática
# ---------------------------------------------------------------------------

class TestSourceConfigs:

    def test_todas_as_fontes_conhecidas_estao_configuradas(self):
        sources = {cfg.name for cfg in SOURCE_CONFIGS}
        assert "comex" in sources
        assert "faostat" in sources
        assert "fred" in sources
        assert "comtrade" in sources

    def test_cada_fonte_tem_min_year_valido(self):
        for cfg in SOURCE_CONFIGS:
            assert isinstance(cfg.min_year, int)
            assert cfg.min_year >= 1990

    def test_granularidade_correta_por_fonte(self):
        cfg_by_name = {cfg.name: cfg for cfg in SOURCE_CONFIGS}
        assert cfg_by_name["comex"].granularity == "monthly"
        assert cfg_by_name["fred"].granularity == "monthly"
        assert cfg_by_name["faostat"].granularity == "annual"
        assert cfg_by_name["comtrade"].granularity == "annual"


# ---------------------------------------------------------------------------
# SmartCollector.decide_strategy — lógica de decisão de modo
# ---------------------------------------------------------------------------

class TestSmartCollectorDecideStrategy:

    def test_retorna_gap_fill_quando_ha_gaps(self, mock_supabase):
        collector = SmartCollector(supabase_client=mock_supabase)
        gap_result = DatasetGapResult("faostat", 1, [2020, 2021], [])
        strategy = collector.decide_strategy(gap_result, mode="auto")
        assert strategy == "gap-fill"

    def test_retorna_expand_quando_sem_gaps_e_modo_auto(self, mock_supabase):
        collector = SmartCollector(supabase_client=mock_supabase)
        gap_result = DatasetGapResult("faostat", 1, [], [])
        strategy = collector.decide_strategy(gap_result, mode="auto")
        assert strategy == "expand"

    def test_modo_forcado_sobrescreve_auto(self, mock_supabase):
        collector = SmartCollector(supabase_client=mock_supabase)
        # mesmo com gaps, se modo for 'expand-forward', deve respeitar
        gap_result = DatasetGapResult("faostat", 1, [2020], [])
        strategy = collector.decide_strategy(gap_result, mode="expand-forward")
        assert strategy == "expand-forward"

    def test_modo_gap_fill_forcado_quando_sem_gaps_nao_expande(self, mock_supabase):
        collector = SmartCollector(supabase_client=mock_supabase)
        gap_result = DatasetGapResult("faostat", 1, [], [])
        strategy = collector.decide_strategy(gap_result, mode="gap-fill")
        assert strategy == "gap-fill"
