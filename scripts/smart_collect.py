"""Script CLI de Coleta Inteligente com Detecção de Gaps Temporais (FertiPartner).

Detecta lacunas temporais no banco de dados Supabase para todos os datasets
de fertilizantes e executa coleta direcionada via APIs para preenchê-las.

Estratégia de operação:
  1. Para cada dataset (Comex Stat, FAOSTAT, FRED, UN Comtrade), consulta os
     períodos já presentes no banco por fertilizante.
  2. Calcula os períodos ausentes (gaps) dentro da janela histórica configurada.
  3. Se há gaps → executa coleta apenas dos períodos faltantes (gap-fill).
  4. Se não há gaps → expande a cobertura para trás e/ou para frente (expand).
  5. Gera um relatório consolidado em Markdown publicado no GitHub Actions
     Job Summary via $GITHUB_STEP_SUMMARY.

Granularidade por fonte:
  - Comex Stat (MDIC): mensal (year + month em trade_records)
  - FAOSTAT: anual (year em production_records)
  - FRED: mensal (price_date em price_records)
  - UN Comtrade: anual (period em trade_flows)

Usage:
    python scripts/smart_collect.py --dry-run
    python scripts/smart_collect.py --source faostat --fertilizer-id 8
    python scripts/smart_collect.py --source all --min-year 2015 --mode auto
"""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Garante execução no ambiente virtual do projeto
venv_python = PROJECT_ROOT / ".venv" / (
    "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
)
if venv_python.is_file() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    sys.exit(subprocess.call([str(venv_python)] + sys.argv))

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from domain.fertilizers import FERTILIZERS_CATALOG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smart_collect")


# ---------------------------------------------------------------------------
# Configuração estática das fontes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceConfig:
    """Configuração imutável de uma fonte de dados."""

    name: str
    """Identificador da fonte: 'comex', 'faostat', 'fred', 'comtrade'."""

    table: str
    """Tabela Supabase onde os dados são armazenados."""

    year_column: str
    """Coluna que representa o ano do registro."""

    month_column: str | None
    """Coluna de mês, ou None para fontes anuais."""

    granularity: str
    """'monthly' ou 'annual'."""

    min_year: int
    """Ano mínimo histórico a cobrir por padrão."""

    max_year_offset: int = 0
    """Offset a subtrair do ano corrente para calcular o MAX_YEAR.
    0 = ano corrente (mensais), 1 = ano corrente - 1 (anuais).
    """


SOURCE_CONFIGS: list[SourceConfig] = [
    SourceConfig(
        name="comex",
        table="trade_records",
        year_column="year",
        month_column="month",
        granularity="monthly",
        min_year=2010,
        max_year_offset=0,
    ),
    SourceConfig(
        name="faostat",
        table="production_records",
        year_column="year",
        month_column=None,
        granularity="annual",
        min_year=2010,
        max_year_offset=1,
    ),
    SourceConfig(
        name="fred",
        table="price_records",
        year_column="price_date",   # coluna DATE, extraímos ano/mês
        month_column="price_date",  # mesma coluna, será parseada
        granularity="monthly",
        min_year=2010,
        max_year_offset=0,
    ),
    SourceConfig(
        name="comtrade",
        table="trade_flows",
        year_column="period",
        month_column=None,
        granularity="annual",
        min_year=2018,
        max_year_offset=1,
    ),
]


# ---------------------------------------------------------------------------
# Funções puras de cálculo de gaps
# ---------------------------------------------------------------------------

def _compute_missing_years(
    present: list[int],
    min_year: int,
    max_year: int,
) -> list[int]:
    """Retorna anos ausentes na janela [min_year, max_year] dados os anos presentes.

    Args:
        present: Lista de anos já existentes no banco.
        min_year: Limite inferior da janela de cobertura.
        max_year: Limite superior da janela de cobertura.

    Returns:
        Lista de anos ausentes, ordenada de forma crescente.
    """
    full_range = set(range(min_year, max_year + 1))
    present_set = {y for y in present if min_year <= y <= max_year}
    return sorted(full_range - present_set)


def _compute_missing_months(
    present: list[tuple[int, int]],
    min_year: int,
    max_year: int,
) -> list[tuple[int, int]]:
    """Retorna tuplas (ano, mês) ausentes na janela [min_year, max_year].

    Args:
        present: Lista de tuplas (ano, mês) já existentes no banco.
        min_year: Limite inferior em anos.
        max_year: Limite superior em anos.

    Returns:
        Lista de tuplas (ano, mês) ausentes, ordenada.
    """
    full_set: set[tuple[int, int]] = set()
    for year in range(min_year, max_year + 1):
        for month in range(1, 13):
            full_set.add((year, month))

    present_filtered = {(y, m) for y, m in present if min_year <= y <= max_year}
    return sorted(full_set - present_filtered)


# ---------------------------------------------------------------------------
# Estrutura de dados para resultado de gap
# ---------------------------------------------------------------------------

@dataclass
class DatasetGapResult:
    """Resultado da detecção de gaps para um dataset/fertilizante."""

    source: str
    """Nome da fonte: 'comex', 'faostat', 'fred', 'comtrade'."""

    fertilizer_id: int
    """ID do fertilizante analisado."""

    missing_years: list[int] = field(default_factory=list)
    """Anos ausentes (para fontes anuais)."""

    missing_months: list[tuple[int, int]] = field(default_factory=list)
    """Tuplas (ano, mês) ausentes (para fontes mensais)."""

    present_years: list[int] = field(default_factory=list)
    """Anos/meses já presentes no banco (para referência)."""

    min_year_used: int = 0
    max_year_used: int = 0

    @property
    def has_gaps(self) -> bool:
        """True se há períodos ausentes."""
        return bool(self.missing_years or self.missing_months)

    @property
    def total_periods(self) -> int:
        """Total de períodos ausentes (anos + meses)."""
        return len(self.missing_years) + len(self.missing_months)


# ---------------------------------------------------------------------------
# Detecção de gaps — GapDetector
# ---------------------------------------------------------------------------

class GapDetector:
    """Analisa o banco de dados Supabase e detecta gaps temporais por dataset."""

    def __init__(self, supabase_client: Any | None = None) -> None:
        if supabase_client is not None:
            self.supabase = supabase_client
        else:
            from app.infrastructure.supabase import SupabaseClientManager, SupabaseConfig
            config = SupabaseConfig.from_env()
            self.supabase = SupabaseClientManager.get_admin_client(config)

    def _current_year(self) -> int:
        return datetime.now().year

    def _resolve_max_year(self, cfg: SourceConfig) -> int:
        return self._current_year() - cfg.max_year_offset

    # --- FAOSTAT ---

    def detect_faostat_gaps(
        self,
        fertilizer_id: int,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> DatasetGapResult:
        """Detecta anos ausentes em production_records para o fertilizante."""
        cfg = next(c for c in SOURCE_CONFIGS if c.name == "faostat")
        min_y = min_year if min_year is not None else cfg.min_year
        max_y = max_year if max_year is not None else self._resolve_max_year(cfg)

        try:
            resp = (
                self.supabase
                .table("production_records")
                .select("year")
                .eq("fertilizer_id", fertilizer_id)
                .execute()
            )
            present = [int(row["year"]) for row in (resp.data or [])]
        except Exception as exc:
            logger.warning("Erro ao consultar production_records (faostat): %s", exc)
            present = []

        missing = _compute_missing_years(present, min_y, max_y)
        return DatasetGapResult(
            source="faostat",
            fertilizer_id=fertilizer_id,
            missing_years=missing,
            missing_months=[],
            present_years=sorted(set(present)),
            min_year_used=min_y,
            max_year_used=max_y,
        )

    # --- Comex Stat ---

    def detect_comex_gaps(
        self,
        fertilizer_id: int,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> DatasetGapResult:
        """Detecta meses ausentes em trade_records para o fertilizante."""
        cfg = next(c for c in SOURCE_CONFIGS if c.name == "comex")
        min_y = min_year if min_year is not None else cfg.min_year
        max_y = max_year if max_year is not None else self._resolve_max_year(cfg)

        try:
            resp = (
                self.supabase
                .table("trade_records")
                .select("year,month")
                .eq("fertilizer_id", fertilizer_id)
                .execute()
            )
            present = [
                (int(row["year"]), int(row["month"]))
                for row in (resp.data or [])
                if row.get("year") and row.get("month")
            ]
        except Exception as exc:
            logger.warning("Erro ao consultar trade_records (comex): %s", exc)
            present = []

        missing = _compute_missing_months(present, min_y, max_y)
        present_years = sorted({y for y, _ in present})
        return DatasetGapResult(
            source="comex",
            fertilizer_id=fertilizer_id,
            missing_years=[],
            missing_months=missing,
            present_years=present_years,
            min_year_used=min_y,
            max_year_used=max_y,
        )

    # --- FRED ---

    def detect_fred_gaps(
        self,
        fertilizer_id: int,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> DatasetGapResult:
        """Detecta meses ausentes em price_records (FRED) para o fertilizante."""
        cfg = next(c for c in SOURCE_CONFIGS if c.name == "fred")
        min_y = min_year if min_year is not None else cfg.min_year
        max_y = max_year if max_year is not None else self._resolve_max_year(cfg)

        try:
            resp = (
                self.supabase
                .table("price_records")
                .select("price_date")
                .eq("fertilizer_id", fertilizer_id)
                .execute()
            )
            present: list[tuple[int, int]] = []
            for row in resp.data or []:
                pd = row.get("price_date", "")
                if pd and len(pd) >= 7:
                    try:
                        year_m = int(pd[:4])
                        month_m = int(pd[5:7])
                        present.append((year_m, month_m))
                    except (ValueError, IndexError):
                        pass
        except Exception as exc:
            logger.warning("Erro ao consultar price_records (fred): %s", exc)
            present = []

        missing = _compute_missing_months(present, min_y, max_y)
        present_years = sorted({y for y, _ in present})
        return DatasetGapResult(
            source="fred",
            fertilizer_id=fertilizer_id,
            missing_years=[],
            missing_months=missing,
            present_years=present_years,
            min_year_used=min_y,
            max_year_used=max_y,
        )

    # --- UN Comtrade ---

    def detect_comtrade_gaps(
        self,
        fertilizer_id: int,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> DatasetGapResult:
        """Detecta anos ausentes em trade_flows (Comtrade) para o fertilizante."""
        cfg = next(c for c in SOURCE_CONFIGS if c.name == "comtrade")
        min_y = min_year if min_year is not None else cfg.min_year
        max_y = max_year if max_year is not None else self._resolve_max_year(cfg)

        try:
            resp = (
                self.supabase
                .table("trade_flows")
                .select("period")
                .eq("fertilizer_id", fertilizer_id)
                .execute()
            )
            present = [int(row["period"]) for row in (resp.data or []) if row.get("period")]
        except Exception as exc:
            logger.warning("Erro ao consultar trade_flows (comtrade): %s", exc)
            present = []

        missing = _compute_missing_years(present, min_y, max_y)
        return DatasetGapResult(
            source="comtrade",
            fertilizer_id=fertilizer_id,
            missing_years=missing,
            missing_months=[],
            present_years=sorted(set(present)),
            min_year_used=min_y,
            max_year_used=max_y,
        )

    def detect_all(
        self,
        fertilizer_id: int,
        sources: list[str] | None = None,
        min_year_override: int | None = None,
        max_year_override: int | None = None,
    ) -> list[DatasetGapResult]:
        """Executa detecção de gaps em todas as fontes configuradas."""
        active_sources = sources or [c.name for c in SOURCE_CONFIGS]
        results: list[DatasetGapResult] = []

        detectors = {
            "faostat": self.detect_faostat_gaps,
            "comex": self.detect_comex_gaps,
            "fred": self.detect_fred_gaps,
            "comtrade": self.detect_comtrade_gaps,
        }

        for source_name in active_sources:
            if source_name not in detectors:
                logger.warning("Fonte desconhecida: %s — ignorada.", source_name)
                continue
            logger.info("Detectando gaps em '%s' para fertilizer_id=%d...", source_name, fertilizer_id)
            result = detectors[source_name](
                fertilizer_id=fertilizer_id,
                min_year=min_year_override,
                max_year=max_year_override,
            )
            results.append(result)
            if result.has_gaps:
                logger.info(
                    "  -> %d período(s) ausente(s) em '%s'",
                    result.total_periods,
                    source_name,
                )
            else:
                logger.info("  -> Sem gaps em '%s'.", source_name)

        return results


# ---------------------------------------------------------------------------
# Relatório de coleta
# ---------------------------------------------------------------------------

@dataclass
class CollectedPeriod:
    """Registro de uma coleta executada."""

    source: str
    fertilizer_id: int
    year: int
    month: int | None = None
    status: str = "SUCESSO"
    records: int = 0
    details: str = ""
    elapsed_s: float = 0.0


@dataclass
class CollectionReport:
    """Relatório consolidado de gaps detectados e coletas executadas."""

    results: list[DatasetGapResult] = field(default_factory=list)
    collected: list[dict[str, Any]] = field(default_factory=list)
    run_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def total_gaps(self) -> int:
        return sum(r.total_periods for r in self.results)

    @property
    def total_collected(self) -> int:
        return len(self.collected)

    def to_markdown(self) -> str:
        """Gera relatório Markdown para o GitHub Actions Job Summary."""
        lines: list[str] = []
        lines.append("## FertiPartner — Relatório de Coleta Inteligente")
        lines.append(f"\n**Executado em:** {self.run_at}")
        lines.append(f"**Total de gaps detectados:** {self.total_gaps}")
        lines.append(f"**Coletas executadas:** {self.total_collected}")
        lines.append("")

        # Tabela de gaps por dataset
        lines.append("### Gaps Detectados por Dataset")
        lines.append("")
        lines.append("| Fonte | Fertilizante ID | Períodos Ausentes | Janela |")
        lines.append("|-------|----------------|-------------------|--------|")

        for r in self.results:
            if r.granularity_label == "annual":
                periods_str = ", ".join(str(y) for y in r.missing_years) or "Nenhum"
            else:
                if r.missing_months:
                    periods_str = (
                        f"{len(r.missing_months)} meses"
                        f" (ex: {r.missing_months[0][0]}-{r.missing_months[0][1]:02d})"
                    )
                else:
                    periods_str = "Nenhum"
            janela = f"{r.min_year_used}–{r.max_year_used}"
            lines.append(f"| {r.source} | {r.fertilizer_id} | {periods_str} | {janela} |")

        lines.append("")

        # Tabela de coletas executadas
        if self.collected:
            lines.append("### Coletas Executadas")
            lines.append("")
            lines.append("| Fonte | Fertilizante ID | Ano | Mês | Status | Registros |")
            lines.append("|-------|----------------|-----|-----|--------|-----------|")
            for c in self.collected:
                mes = c.get("month", "–")
                lines.append(
                    f"| {c.get('source', '')} | {c.get('fertilizer_id', '')} "
                    f"| {c.get('year', '')} | {mes} "
                    f"| {c.get('status', '')} | {c.get('records', 0):,} |"
                )
        else:
            lines.append("*Nenhuma coleta executada nesta execução.*")

        lines.append("")
        lines.append("---")
        lines.append("*Gerado automaticamente pelo FertiPartner Smart Collect.*")

        return "\n".join(lines)


# Adiciona propriedade auxiliar para acesso à granularidade na renderização do relatório
def _gap_result_granularity_label(self: DatasetGapResult) -> str:
    cfg = next((c for c in SOURCE_CONFIGS if c.name == self.source), None)
    return cfg.granularity if cfg else "annual"

DatasetGapResult.granularity_label = property(_gap_result_granularity_label)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Orquestrador de coleta — SmartCollector
# ---------------------------------------------------------------------------

class SmartCollector:
    """Orquestra a detecção de gaps e execução das coletas."""

    VALID_MODES = {"auto", "gap-fill", "expand", "expand-back", "expand-forward"}

    def __init__(self, supabase_client: Any | None = None) -> None:
        self._supabase_client = supabase_client
        self._detector = GapDetector(supabase_client=supabase_client)

    def decide_strategy(
        self,
        gap_result: DatasetGapResult,
        mode: str = "auto",
    ) -> str:
        """Decide a estratégia de coleta com base nos gaps e no modo solicitado.

        Args:
            gap_result: Resultado da detecção de gaps para um dataset.
            mode: Modo de operação ('auto', 'gap-fill', 'expand',
                  'expand-back', 'expand-forward').

        Returns:
            Estratégia efetiva a ser executada.
        """
        if mode in ("expand-back", "expand-forward"):
            return mode
        if mode == "expand":
            return "expand"
        if mode == "gap-fill":
            return "gap-fill"
        # auto: prioriza preenchimento de gaps; expande se não há gaps
        if gap_result.has_gaps:
            return "gap-fill"
        return "expand"

    def _collect_year(
        self,
        source: str,
        fertilizer_id: int,
        year: int,
        month: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Executa a coleta de um período específico para uma fonte."""
        from scripts.collect_fertilizer_all_sources import (
            run_comex_stat_pipeline,
            run_faostat_pipeline,
            run_fred_pipeline,
            run_comtrade_pipeline,
        )

        t_start = time.time()
        try:
            if source == "comex":
                m = month or 1
                m_end = month or 12
                res = run_comex_stat_pipeline(
                    fertilizer_id=fertilizer_id,
                    year=year,
                    dry_run=dry_run,
                )
            elif source == "faostat":
                res = run_faostat_pipeline(
                    fertilizer_id=fertilizer_id,
                    year=year,
                    dry_run=dry_run,
                )
            elif source == "fred":
                res = run_fred_pipeline(
                    fertilizer_id=fertilizer_id,
                    year=year,
                    dry_run=dry_run,
                )
            elif source == "comtrade":
                res = run_comtrade_pipeline(
                    fertilizer_id=fertilizer_id,
                    year=year,
                    dry_run=dry_run,
                )
            else:
                return {"source": source, "year": year, "status": "IGNORADO", "records": 0}

            elapsed = time.time() - t_start
            return {
                "source": source,
                "fertilizer_id": fertilizer_id,
                "year": year,
                "month": month,
                "status": res.get("status", "SUCESSO"),
                "records": res.get("records", 0),
                "details": res.get("details", ""),
                "elapsed_s": round(elapsed, 1),
            }
        except Exception as exc:
            elapsed = time.time() - t_start
            logger.error("Erro na coleta %s/%d/%s: %s", source, fertilizer_id, year, exc)
            return {
                "source": source,
                "fertilizer_id": fertilizer_id,
                "year": year,
                "month": month,
                "status": "FALHA",
                "records": 0,
                "details": str(exc),
                "elapsed_s": round(elapsed, 1),
            }

    def _expand_years(
        self,
        gap_result: DatasetGapResult,
        strategy: str,
    ) -> list[int]:
        """Calcula anos a coletar na estratégia de expansão."""
        cfg = next((c for c in SOURCE_CONFIGS if c.name == gap_result.source), None)
        if not cfg:
            return []

        current_year = datetime.now().year
        max_y = current_year - cfg.max_year_offset
        min_y = cfg.min_year

        present = gap_result.present_years
        if not present:
            # Sem dados: coleta o ano mais recente disponível
            return [max_y]

        years: list[int] = []
        if strategy in ("expand", "expand-back"):
            back_target = min(present) - 1
            if back_target >= min_y:
                years.append(back_target)
        if strategy in ("expand", "expand-forward"):
            forward_target = max(present) + 1
            if forward_target <= max_y:
                years.append(forward_target)
        return years

    def run(
        self,
        sources: list[str] | None = None,
        fertilizer_ids: list[int] | None = None,
        mode: str = "auto",
        dry_run: bool = False,
        min_year_override: int | None = None,
        max_year_override: int | None = None,
    ) -> CollectionReport:
        """Executa o ciclo completo: detecta gaps e coleta.

        Args:
            sources: Lista de fontes a processar. None = todas.
            fertilizer_ids: Lista de IDs de fertilizantes. None = todos.
            mode: Estratégia de coleta ('auto', 'gap-fill', 'expand', etc.).
            dry_run: Se True, apenas inspeciona sem gravar no banco.
            min_year_override: Sobrescreve o MIN_YEAR de todas as fontes.
            max_year_override: Sobrescreve o MAX_YEAR de todas as fontes.

        Returns:
            CollectionReport com gaps detectados e coletas realizadas.
        """
        active_ferts = fertilizer_ids or [f["id"] for f in FERTILIZERS_CATALOG]
        active_sources = sources or [c.name for c in SOURCE_CONFIGS]

        all_gap_results: list[DatasetGapResult] = []
        all_collected: list[dict[str, Any]] = []

        for fert_id in active_ferts:
            fert = next((f for f in FERTILIZERS_CATALOG if f["id"] == fert_id), None)
            fert_name = fert["canonical_name"] if fert else f"ID {fert_id}"
            logger.info("=== Processando fertilizante: %s ===", fert_name)

            gap_results = self._detector.detect_all(
                fertilizer_id=fert_id,
                sources=active_sources,
                min_year_override=min_year_override,
                max_year_override=max_year_override,
            )
            all_gap_results.extend(gap_results)

            for gap_result in gap_results:
                strategy = self.decide_strategy(gap_result, mode=mode)
                logger.info(
                    "Estratégia '%s' para %s/%s (%d gaps)",
                    strategy, gap_result.source, fert_name, gap_result.total_periods,
                )

                if strategy == "gap-fill":
                    if gap_result.granularity_label == "annual":  # type: ignore[attr-defined]
                        for year in gap_result.missing_years:
                            result = self._collect_year(
                                gap_result.source, fert_id, year, dry_run=dry_run
                            )
                            all_collected.append(result)
                            status_icon = "OK" if result["status"] != "FALHA" else "FALHA"
                            logger.info(
                                "  [%s] %s/%d: %d registros",
                                status_icon, gap_result.source, year, result["records"],
                            )
                    else:
                        # Mensal: agrupa por ano para eficiência
                        years_to_collect = sorted({y for y, _ in gap_result.missing_months})
                        for year in years_to_collect:
                            result = self._collect_year(
                                gap_result.source, fert_id, year, dry_run=dry_run
                            )
                            all_collected.append(result)
                            logger.info(
                                "  [OK] %s/%d: %d registros",
                                gap_result.source, year, result["records"],
                            )

                elif strategy in ("expand", "expand-back", "expand-forward"):
                    years = self._expand_years(gap_result, strategy)
                    for year in years:
                        result = self._collect_year(
                            gap_result.source, fert_id, year, dry_run=dry_run
                        )
                        all_collected.append(result)
                        logger.info(
                            "  [EXPAND] %s/%d: %d registros",
                            gap_result.source, year, result["records"],
                        )

        return CollectionReport(
            results=all_gap_results,
            collected=all_collected,
        )


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def _publish_job_summary(markdown: str) -> None:
    """Publica o relatório no GitHub Actions Job Summary se disponível."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(markdown + "\n")
            logger.info("Relatório publicado em GITHUB_STEP_SUMMARY.")
        except OSError as exc:
            logger.warning("Não foi possível escrever em GITHUB_STEP_SUMMARY: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FertiPartner — Coleta Inteligente com Detecção de Gaps Temporais"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo de inspeção: detecta gaps e simula coleta sem gravar no banco",
    )
    parser.add_argument(
        "--source",
        choices=["all", "comex", "faostat", "fred", "comtrade"],
        default="all",
        help="Fonte de dados a processar (padrão: all)",
    )
    parser.add_argument(
        "--fertilizer-id",
        "--id",
        dest="fertilizer_id",
        type=int,
        default=None,
        help="ID do fertilizante específico (padrão: todos)",
    )
    parser.add_argument(
        "--min-year",
        type=int,
        default=None,
        help="Sobrescreve o ano mínimo histórico para todas as fontes",
    )
    parser.add_argument(
        "--max-year",
        type=int,
        default=None,
        help="Sobrescreve o ano máximo para todas as fontes",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "gap-fill", "expand", "expand-back", "expand-forward"],
        default="auto",
        help=(
            "Estratégia de coleta: "
            "'auto' (preenche gaps se houver, senão expande), "
            "'gap-fill' (apenas preenche gaps), "
            "'expand' (expande para trás e frente), "
            "'expand-back' (apenas para trás), "
            "'expand-forward' (apenas para frente). "
            "Padrão: auto"
        ),
    )

    args = parser.parse_args()

    sources = None if args.source == "all" else [args.source]
    fert_ids = [args.fertilizer_id] if args.fertilizer_id else None

    print("\n" + "=" * 75)
    print("FERTIPARTNER — COLETA INTELIGENTE COM DETECÇÃO DE GAPS")
    print(f"Modo          : {'DRY-RUN (Inspeção)' if args.dry_run else 'COLETA ATIVA'}")
    print(f"Fontes        : {args.source.upper()}")
    print(f"Estratégia    : {args.mode}")
    print(f"Fertilizante  : {args.fertilizer_id or 'Todos'}")
    print(f"Janela mínima : {args.min_year or 'padrão por fonte'}")
    print(f"Janela máxima : {args.max_year or 'padrão por fonte'}")
    print("=" * 75 + "\n")

    collector = SmartCollector()
    t0 = time.time()

    report = collector.run(
        sources=sources,
        fertilizer_ids=fert_ids,
        mode=args.mode,
        dry_run=args.dry_run,
        min_year_override=args.min_year,
        max_year_override=args.max_year,
    )

    elapsed = time.time() - t0

    # Exibe resumo no console
    print("\n" + "=" * 75)
    print("FERTIPARTNER — RESUMO DA COLETA INTELIGENTE")
    print("=" * 75)
    print(f"Gaps totais detectados : {report.total_gaps}")
    print(f"Coletas executadas     : {report.total_collected}")
    print(f"Tempo total            : {elapsed:.1f}s")
    print("-" * 75)

    for r in report.results:
        if r.has_gaps:
            if r.missing_years:
                anos = ", ".join(str(y) for y in r.missing_years[:5])
                sufixo = f"... (+{len(r.missing_years) - 5} mais)" if len(r.missing_years) > 5 else ""
                print(f"  [{r.source:<10}] Fert {r.fertilizer_id}: {len(r.missing_years)} ano(s) ausente(s) → {anos}{sufixo}")
            if r.missing_months:
                print(f"  [{r.source:<10}] Fert {r.fertilizer_id}: {len(r.missing_months)} mês(es) ausente(s)")
        else:
            print(f"  [{r.source:<10}] Fert {r.fertilizer_id}: Sem gaps na janela {r.min_year_used}-{r.max_year_used}")

    print("=" * 75 + "\n")

    # Publica relatório no GitHub Actions Job Summary
    markdown = report.to_markdown()
    _publish_job_summary(markdown)


if __name__ == "__main__":
    main()
