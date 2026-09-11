# Plano: Coleta Inteligente de Dados com Detecção de Gaps

## Objetivo

Criar um script `scripts/smart_collect.py` e um workflow GitHub Actions
`.github/workflows/smart_collect.yml` que detectam gaps temporais no banco
Supabase e executam coleta inteligente para preenchê-los ou expandir a cobertura.

## Escopo

- Script Python com `GapDetector`, `SmartCollector` e `CollectionReport`.
- Workflow GitHub Actions com cron diário (08:00 UTC) + `workflow_dispatch`.
- Testes unitários em `tests/unit/scripts/test_smart_collect.py`.

## Abordagem

### Detecção de Gaps por Dataset

| Dataset    | Tabela             | Coluna temporal      | Granularidade |
|------------|-------------------|----------------------|---------------|
| Comex Stat | `trade_records`    | `year` + `month`     | Mensal        |
| FAOSTAT    | `production_records` | `year`             | Anual         |
| FRED       | `price_records`    | `price_date` (YYYY-MM) | Mensal     |
| Comtrade   | `trade_flows`      | `period` (ano)       | Anual         |

### MIN_YEAR por fonte

| Fonte      | MIN_YEAR padrão |
|------------|-----------------|
| Comex Stat | 2010            |
| FAOSTAT    | 2010            |
| FRED       | 2010            |
| Comtrade   | 2018            |

### MAX_YEAR

- Fontes anuais (FAOSTAT, Comtrade): `current_year - 1`
- Fontes mensais (Comex, FRED): `current_year` (mês anterior como limite)

### Estratégia `auto`

```
gaps detectados? → SIM → gap-fill (coleta apenas os períodos ausentes)
                  → NÃO → expand-back (1 ano atrás do mínimo) +
                           expand-forward (1 ano à frente do máximo)
```

## Etapas

- [x] Leitura do contexto e skills
- [x] Criação do plano ativo
- [ ] Testes unitários (TDD RED)
- [ ] Implementação `scripts/smart_collect.py`
- [ ] Workflow `.github/workflows/smart_collect.yml`
- [ ] Testes passando (TDD GREEN)
- [ ] Suite completa sem regressões

## Decisões Registradas

- Cron: `0 8 * * *` (diário às 08:00 UTC) — GitHub Actions free tier suporta.
- Granularidade: mensal para Comex/FRED, anual para FAOSTAT/Comtrade.
- MIN_YEAR: por fonte (tabela acima).
- MAX_YEAR: `current_year - 1` para anuais, `current_year` para mensais.
- O script reutiliza as funções de pipeline existentes em `collect_fertilizer_all_sources.py`.
- O relatório é publicado no GitHub Actions Job Summary via `$GITHUB_STEP_SUMMARY`.

## Problemas Encontrados

Nenhum até o momento.

## Progresso

Iniciado em: 2026-09-11
