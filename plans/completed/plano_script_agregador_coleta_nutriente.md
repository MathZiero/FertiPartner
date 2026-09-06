# Plano de Trabalho: Script Agregador de Coleta por Nutriente / Fertilizante e Tolerância a Falhas

## Status
Concluído com Sucesso. Todos os 109 testes unitários aprovados (incluindo os 7 novos testes de TDD específicos para este plano).

## Objetivo
Criar um script agregador (`scripts/collect_fertilizer_all_sources.py`) que recebe o ID de um fertilizante/nutriente e o ano (`--fertilizer-id` e `--year`) e orquestra a coleta de todas as fontes disponíveis (MDIC Comex Stat, FAOSTAT, FRED e UN Comtrade) de forma integrada e resiliente.

## Requisitos Críticos Atendidos
1. **Tolerância a Falhas**: Uma falha de API ou cota excedida (ex: 403 da ONU Comtrade ou falta de chave FRED) em uma fonte não interrompe nem compromete a execução das outras fontes. Cada pipeline roda em bloco de execução isolado e o script produz um relatório consolidado executivo com status `SUCESSO TOTAL` ou `SUCESSO PARCIAL`.
2. **Parâmetro de ID Opcional em Todos os Scripts**: Todos os scripts de coleta existentes (`collect_brazil_comex.py`, `collect_faostat_production.py`, `collect_benchmark_prices.py`, `collect_top_trade_flows.py`) agora aceitam o argumento opcional `--fertilizer-id` (ou `--id`), permitindo tanto a execução global (sem filtro) quanto a execução direcionada a um único insumo.

## Implementações Realizadas

### 1. Parâmetro `--fertilizer-id` nos Scripts Existentes (`scripts/`)
- `scripts/collect_brazil_comex.py`:
  - Adicionado `--fertilizer-id` (int, opcional). Quando informado, filtra a lista de NCMs apenas para os códigos daquele fertilizante via `NCM_FERTILIZER_MAP`.
  - Suporte propagado no método `ComexStatCollector.run(..., ncms=..., fertilizer_id=...)`.
- `scripts/collect_faostat_production.py`:
  - Adicionado `--fertilizer-id` (int, opcional).
  - Atualizado `run_offline_benchmarks(target_year=..., target_fert_id=...)` para filtrar os registros consolidados pelo fertilizante solicitado.
  - Atualizado `FAOSTATCollector.run(..., fertilizer_id=...)` para filtragem inline de dados online.
- `scripts/collect_benchmark_prices.py`:
  - Adicionado `--fertilizer-id` (int, opcional). Mapeia o ID do fertilizante no catálogo oficial para o slug correspondente e filtra as séries FRED de cotações internacionais.
- `scripts/collect_top_trade_flows.py`:
  - Adicionado `--fertilizer-id` (int, opcional). Filtra os códigos HS associados ao fertilizante em `collector.hs_fertilizer_map`.

### 2. Novo Script Agregador: `scripts/collect_fertilizer_all_sources.py`
- Validação antecipada do `--fertilizer-id` com listagem de produtos válidos se ID for incorreto.
- Implementação de 4 pipelines funcionais modulares:
  - `run_comex_stat_pipeline`: MDIC Comex Stat (import/export).
  - `run_faostat_pipeline`: FAOSTAT online ou benchmarks mundiais.
  - `run_fred_pipeline`: Séries internacionais FRED.
  - `run_comtrade_pipeline`: Descoberta de Top Traders e fluxos bilaterais da ONU.
- Execução isolada com try/except individual.
- Tabela executiva final com status por fonte e status geral da coleta integrada.

### 3. Validação e Testes Unitários com TDD (`tests/unit/scripts/test_cli_scripts.py`)
- Testes desenvolvidos na fase Red e convertidos para Green:
  1. `test_collect_brazil_comex_fertilizer_id_filters_ncms`
  2. `test_collect_faostat_production_fertilizer_id_filter`
  3. `test_collect_benchmark_prices_fertilizer_id_filter`
  4. `test_collect_top_trade_flows_fertilizer_id_filter`
  5. `test_collect_fertilizer_all_sources_invalid_fertilizer_id`
  6. `test_collect_fertilizer_all_sources_success_all_sources`
  7. `test_collect_fertilizer_all_sources_fault_tolerant_to_api_failure`
- Resultado da suíte completa: **109 testes unitários aprovados (100%)**.
