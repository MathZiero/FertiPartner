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
- [x] Testes unitários (TDD RED) — 38 testes
- [x] Implementação `scripts/smart_collect.py`
- [x] Workflow `.github/workflows/smart_collect.yml`
- [x] Testes passando (TDD GREEN) — 38/38
- [x] Suite completa sem regressões — 210/210
- [x] Correção e alinhamento com o schema 4NF (2026-09-13):
  - `trade_records` e `production_records` usam `period_start_date` em vez de `year`/`month`.
  - UN Comtrade consulta `trade_records` com `period_type = 'YEAR'`.
  - Blocos `try/except` resilientes em `detect_worldbank_gaps` e `detect_faostat_prices_gaps`.
  - Fallbacks de credenciais (`secrets.SUPABASE_KEY || secrets.SUPABASE_ANON_KEY`) no workflow.
  - Novos testes unitários 4NF: 45/45 passando.
  - Suite completa sem regressões: 230/230 testes passando.

## Decisões Registradas

- Cron: `0 8 * * *` (diário às 08:00 UTC) — GitHub Actions free tier suporta.
- Granularidade: mensal para Comex/FRED, anual para FAOSTAT/Comtrade.
- MIN_YEAR: por fonte (tabela acima).
- MAX_YEAR: `current_year - 1` para anuais, `current_year` para mensais.
- O script reutiliza as funções de pipeline existentes em `collect_fertilizer_all_sources.py`.
- O relatório é publicado no GitHub Actions Job Summary via `$GITHUB_STEP_SUMMARY`.
- Schema 4NF: a dimensão temporal universal utiliza `period_start_date` (DATE) e `period_type` ('MONTH' / 'YEAR'), tanto para comércio (Comex, Comtrade) quanto para produção (FAOSTAT).

## Problemas Encontrados

- Incompatibilidade entre as queries de `GapDetector` e o schema 4NF (`column year does not exist` e `table trade_flows not found`), além de falha por ausência da migração da tabela `country_indicators`. Resolvido harmonizando as queries com `period_start_date` e adicionando resiliência contra tabelas pendentes de migração.

## Progresso

Iniciado em: 2026-09-11
Concluído em: 2026-09-11
Bugfix Schema 4NF: 2026-09-13

