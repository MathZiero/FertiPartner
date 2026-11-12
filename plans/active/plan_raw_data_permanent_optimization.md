# Plano: Otimização Permanente de Armazenamento da Tabela `public.raw_data`

## Objetivo

Resolver definitivamente o crescimento descontrolado da tabela `public.raw_data` no Supabase (que estava excedendo o limite do plano Free), mantendo o armazenamento bruto (`raw_data`) para rastreabilidade e auditoria 4NF, mas eliminando as causas raiz de duplicação, payloads inchados com dados irrelevantes e órfãos.

## Diagnóstico da Causa Raiz

A inspeção dos 8.070 registros em `public.raw_data` (IDs até 64.592) revelou por que a deduplicação anterior baseada apenas em `payload_hash` não impediu o retorno do problema:

1. **Metadados voláteis quebravam o `payload_hash` em 100% das coletas (`0` hashes duplicados em 8.070 linhas):**
   - **FAOSTAT (`source_id=2` e `source_id=9`)**: Inclui `metadata.processing_time` (muda a cada request em milissegundos) e `metadata.dsd` (definição estrutural repetida).
   - **UN Comtrade (`source_id=3`)**: Inclui `elapsedTime` (ex: `"3.15 secs"`, muda a cada request).
   - **FRED (`source_id=7`)**: Inclui `realtime_start` e `realtime_end` (na raiz e em cada item de `observations`) com a data do dia da consulta.
   - **World Bank (`source_id=8`)**: Inclui `lastupdated` no cabeçalho de paginação.
   - **Comex Stat (`source_id=4, 5`)**: Inclui `processo_info`.

2. **Ausência de Upsert por `(source_id, endpoint_url)` em `BaseCollector.store_raw_payload`:**
   - Quando um mesmo endpoint recebia atualização (ex: série diária `DHHNGSP` no FRED com 425 linhas para a mesma URL, ou Comex no ano corrente), `store_raw_payload` fazia `INSERT` de uma nova linha em `raw_data` em vez de atualizar a linha existente daquele `(source_id, endpoint_url)`.
   - Quando as tabelas de fatos (`trade_records`, `price_records`, etc.) faziam `UPSERT`, o `raw_data_id` passava a apontar para o novo ID e deixava o registro antigo de `raw_data` **órfão** no banco (5.661 linhas órfãs de 8.070 totais = **70% da tabela órfã**).

3. **Gravação em `raw_data` ANTES da filtragem de itens relevantes (3.371 linhas de ~150–316 KB no `source_id=9`):**
   - `FAOSTATInputPricesCollector` (`source_id=9`) consultava o domínio `PP` da FAOSTAT (que retorna 377 a 800 itens de safras agrícolas como maçã, banana, abacate, e **0** itens de fertilizantes), gravava o JSON bruto inteiro em `raw_data` antes de filtrar `FAO_PRICE_ITEM_FERTILIZER_MAP`, e depois inseria **0 linhas** em `price_records`.
   - `FAOSTATCollector` (`source_id=2`) também gravava o payload completo antes de verificar se havia itens do fertilizante consultado.
   - `UNComtradeCollector` (`source_id=3`) armazenava objetos com 47 chaves por linha (mais de 25 chaves `null` ou descrições textuais redundantes).

4. **Loops de re-coleta diária em `scripts/smart_collect.py`:**
   - `_compute_missing_months` verificava os 12 meses (`1..12`) do ano corrente (`current_year`), tratando meses futuros/ainda não publicados como "gaps" todos os dias.
   - `FRED` era chamado uma vez para cada ano ausente (`2010..2026`), embora uma única chamada com `observation_start = min_year` já retorne toda a série histórica.
   - `worldbank` (indicador por país, sem `fertilizer_id`) era executado 13 vezes por rodada (uma para cada fertilizante do catálogo).

## Escopo

1. **`src/app/infrastructure/collectors/base.py` (`BaseCollector`)**:
   - Adicionar `sanitize_raw_payload()` para remover chaves voláteis (`processing_time`, `elapsedTime`, `realtime_start`, `realtime_end`, `processo_info`, `dsd`, `lastupdated`) e chaves com valor `None`/`""` antes de calcular o `payload_hash` e persistir o JSON.
   - Atualizar `store_raw_payload()` para:
     1. Reutilizar registro se `payload_hash` já existir;
     2. Fazer `UPDATE` in-place se já existir registro para o mesmo `(source_id, endpoint_url)`, preservando o `id` e evitando órfãos;
     3. Fazer `INSERT` apenas quando for um endpoint inédito.
2. **Coletores (`faostat_prices_collector.py`, `faostat_collector.py`, `comtrade_collector.py`, `comex_stat_collector.py`, `fred_collector.py`, `worldbank_collector.py`)**:
   - Filtrar os registros válidos de fertilizantes **antes** de chamar `store_raw_payload()`.
   - Não gravar em `raw_data` quando a resposta não contiver nenhum registro aplicável aos fertilizantes monitorados.
   - Armazenar em `raw_data` apenas os registros filtrados pertinentes ao domínio de fertilizantes.
3. **`scripts/smart_collect.py`**:
   - Ignorar meses futuros do ano corrente na detecção de gaps mensais (`comex`, `fred`).
   - Ignorar fertilizantes não mapeados em fontes específicas (ex: fertilizantes sem série no FRED, sem código na FAOSTAT ou Comtrade) para evitar falsos gaps perpétuos.
   - Executar fontes globais sem vínculo por fertilizante (`worldbank`) apenas uma vez por execução, e consolidar a coleta do `fred` a partir do menor ano faltante.
4. **Banco de Dados e Limpeza (`infrastructure/supabase/` e `scripts/cleanup_raw_data.py`)**:
   - Criar migração SQL adicionando índice em `raw_data(source_id, endpoint_url)`.
   - Criar e executar `scripts/cleanup_raw_data.py` para remover os 5.661 registros órfãos, unificar duplicatas de `(source_id, endpoint_url)` e compactar/sanitizar os payloads ativos no Supabase.

## Etapas

- [x] Leitura do contexto (`AGENTS.md`, `README.md`, `skills/tdd/skill.md`, `skills/ci-cd/skill.md`)
- [x] Diagnóstico quantitativo da tabela `public.raw_data` no Supabase
- [x] Criação de branch dedicada e plano ativo
- [ ] Escrita dos testes unitários (TDD RED) para sanitização, upsert por endpoint, filtragem pré-raw nos coletores e `smart_collect`
- [ ] Implementação em `BaseCollector`, coletores e `smart_collect.py` (TDD GREEN)
- [ ] Criação da migração SQL e script de limpeza/compactação `scripts/cleanup_raw_data.py`
- [ ] Execução da limpeza e compactação no banco Supabase e verificação da redução de espaço
- [ ] Execução da suíte completa de testes (`uv run pytest`)
- [ ] Movimentação do plano para `plans/completed/`

## Decisões

- Manter `public.raw_data` ativa e referenciada pelas tabelas de fatos 4NF, garantindo conformidade com `RD08` e `RF20`.
- Adotar semântica de **1 registro canônico em `raw_data` por `(source_id, endpoint_url)`**, atualizando in-place quando o payload mudar.

## Progresso

Iniciado em: 2026-11-11

