"""Camada de domínio do FertiPartner contendo entidades e regras de negócio essenciais."""

from domain.fertilizers import FERTILIZERS_CATALOG
from domain.benchmarks import PRODUCTION_BENCHMARKS, BenchmarkItem

__all__ = ["FERTILIZERS_CATALOG", "PRODUCTION_BENCHMARKS", "BenchmarkItem"]
