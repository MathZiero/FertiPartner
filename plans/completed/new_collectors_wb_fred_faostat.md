# Plano: Integração de Novas Fontes de Dados (World Bank, FRED Séries Extras, FAOSTAT Preços)

## Objetivo

Implementar os 3 novos fluxos de dados aprovados:
1. **P0: FRED Séries Extras** — Ampliar `DEFAULT_FRED_SERIES` no `FREDCollector` com séries de gás natural (`DHHNGSP`), PPIs agregados e subprodutos.
2. **P0: World Bank Indicators API** — Criar `WorldBankCollector` para indicadores macroeconômicos de consumo (`AG.CON.FERT.ZS` - kg/ha e `AG.CON.FERT.PT.ZS` - % produção).
3. **P1: FAOSTAT Input Prices** — Criar `FAOSTATInputPricesCollector` para domínio `PP` (preços pagos por agricultores/preços ao produtor por fertilizante e país).

## Escopo

- Modelagem e migração SQL para novas fontes (`WB_INDICATORS`, `FAOSTAT_PP`), novos mercados de preço (`US_HENRY_HUB_GAS`) e nova tabela `country_indicators`.
- Atualização do coletor FRED e expansão dos testes.
- Novo coletor `WorldBankCollector` + script CLI `scripts/collect_worldbank_indicators.py` + testes unitários.
- Novo coletor `FAOSTATInputPricesCollector` + script CLI `scripts/collect_faostat_prices.py` + testes unitários.
- Atualização de `scripts/populate_database.py` para suportar as novas fontes.
- Suíte completa de testes com TDD rigoroso (RED -> GREEN -> REFACTOR).

## Abordagem

### 1. Migração 4NF e Seeds
- Tabela `country_indicators`:
  - `country_id` (FK `countries`), `indicator_code`, `indicator_name`, `year`, `value`, `unit_code`, `source_id` (FK `data_sources`), `raw_data_id` (FK `raw_data`).
  - Unique constraint: `(country_id, indicator_code, year, source_id)`.
- Seeds em `data_sources`:
  - ID 8: `WB_INDICATORS` (World Bank World Development Indicators, ANNUAL)
  - ID 9: `FAOSTAT_PP` (FAOSTAT Producer Prices / Prices Paid, ANNUAL)
- Seeds em `price_markets`:
  - ID 8: `US_HENRY_HUB_GAS` (Gás Natural Henry Hub Spot, FOB, LA)

### 2. FRED Séries Extras
- Adicionado ao `DEFAULT_FRED_SERIES`:
  - `DHHNGSP` (Henry Hub Gás Natural) -> amônia anidra, benchmark 8, SPOT.
  - `WPU065201` (PPI Nitrogenados Agregado) -> ureia, benchmark 2, SPOT.
  - `WPU065202` (PPI Fosfatados Agregado) -> dap, benchmark 4, SPOT.
  - `WPU0652013A5` (PPI Ureia Soluções) -> ureia, benchmark 2, CONTRACT.
  - `WPU06520201` (PPI Fosfatos de Amônio) -> map, benchmark 4, BENCHMARK.
  - `WPU06520202` (PPI Superfosfatos) -> ssp, benchmark 4, BENCHMARK.
- Garantia de unicidade de tupla `(fertilizer_id, benchmark_id, price_type, source_id)` para evitar conflitos na tabela `price_records`.

### 3. World Bank Collector
- Herda de `BaseCollector` (fonte ID 8).
- Consulta `https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator_id}?format=json`.
- Grava payload bruto em `raw_data`.
- Grava registros normalizados em `country_indicators`.
- CLI: `scripts/collect_worldbank_indicators.py`.

### 4. FAOSTAT Input Prices Collector
- Herda de `BaseCollector` (fonte ID 9).
- Autenticação via `FAOSTATAuthManager`.
- Consulta `https://faostatservices.fao.org/api/v1/en/data/PP`.
- Mapeia itens de fertilizantes e países.
- Grava payload bruto em `raw_data`.
- Grava registros normalizados em `price_records`.
- CLI: `scripts/collect_faostat_prices.py`.

## Etapas

- [x] Criar plano e migração SQL para novas tabelas/fontes
- [x] TDD: Testes unitários para FRED Séries Extras (RED -> GREEN)
- [x] Implementar expansão do FREDCollector
- [x] TDD: Testes unitários para WorldBankCollector (RED -> GREEN)
- [x] Implementar WorldBankCollector e script CLI
- [x] TDD: Testes unitários para FAOSTATInputPricesCollector (RED -> GREEN)
- [x] Implementar FAOSTATInputPricesCollector e script CLI
- [x] Atualizar scripts de povoamento (`populate_database.py`)
- [x] Executar suíte completa de testes e validar 0 regressões (222 testes passando)

## Decisões Registradas

- World Bank Indicator `AG.CON.FERT.ZS` expressa intensidade (kg/ha), portanto não deve ser forçado em `consumption_records` (que exige MT de fertilizante específico). A criação da tabela `country_indicators` preserva a 4NF.
- Gás natural (`DHHNGSP`) foi mapeado para `amonia-anidra` como fertilizante/insumo de base e novo mercado `US_HENRY_HUB_GAS` (id 8).
- Respeitada a restrição de chave única de `price_records` alternando `price_type` (`SPOT`, `CONTRACT`, `BENCHMARK`) para séries FRED do mesmo fertilizante e porto.

## Progresso

Iniciado em: 2026-09-11
Concluído em: 2026-09-11
Resultado: 222 testes unitários passando, 0 regressões.
