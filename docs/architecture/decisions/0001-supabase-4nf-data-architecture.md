# [ADR-0001] Arquitetura do Banco de Dados Supabase em Quarta Forma Normal (4NF)

* **Status**: Aceito
* **Data**: 2026-09-02
* **Autores**: Equipe de Engenharia e Arquitetura FertiPartner
* **Decisores**: Engenharia de Dados, Arquitetura de Software

---

## 1. Contexto e Declaração do Problema

O **FertiPartner** é uma plataforma analítica para monitoramento, inteligência de mercado e visualização de dados históricos e contemporâneos do setor global e nacional de fertilizantes. O sistema consome dados de múltiplos ecossistemas heterogêneos com estruturas, terminologias, periodicidades e granularidades distintas:

* **FAOSTAT (ONU/FAO)**: Estatísticas anuais de produção agrícola e balanço de fertilizantes por nutrientes e por produtos, identificadas por códigos M49 e códigos de produto FAO, com flags de confiabilidade estatística (Oficial, Estimado, Não Oficial).
* **UN Comtrade**: Estatísticas aduaneiras bilaterais mundiais baseadas no Sistema Harmonizado (códigos HS de 6 dígitos), fluxos de Importação/Exportação, valores primários em USD (FOB/CIF) e pesos líquidos em kg.
* **Comex Stat (MDIC / Brasil)**: Microdados de comércio exterior brasileiro com alta granularidade: códigos NCM de 8 dígitos, Unidade da Federação de origem/destino (UF), modais de transporte (Marítima, Aérea, Rodoviária), recintos alfandegários (URF) e detalhamento de frete e seguro.
* **FRED & Banco Mundial (Commodity Markets)**: Séries históricas de preços mensais e semanais em hubs e mercados de referência (Baltic Urea FOB, US Gulf DAP FOB, Vancouver Potash FOB, etc.).

### Desafios de Modelagem
1. **Heterogeneidade e Conflitos de Vocabulário**: Diferentes fontes utilizam nomes, códigos e sistemas de classificação tarifária distintos para o mesmo composto químico (ex: *Urea*, *Ureia*, *Carbamide*, *46-0-0*, *HS 310210*, *NCM 31021010*, *CPC 34611*).
2. **Multiplicidade de Relações Independentes (Risco de Anomalias de Atualização e Redundância)**: Se atributos multivalorados independentes (como nutrientes químicos, sinônimos em múltiplos idiomas e códigos aduaneiros) forem mantidos juntos na mesma entidade de fertilizante, geram-se dependências multivaloradas (*Multi-Valued Dependencies* — MVDs), criando produtos cartesianos, duplicações de registros e anomalias de exclusão/atualização.
3. **Requisitos de Conformidade e Rastreabilidade (RN01, RN02, RNF02)**: Nenhuma métrica pode ser exibida sem fonte rastreável; dados brutos devem ser preservados para auditoria; e as unidades originais devem ser salvas juntamente com as métricas normalizadas para toneladas métricas e USD.

---

## 2. Opções Consideradas

### Opção 1: Modelo Desnormalizado / Documental (JSONB único por fertilizante)
Armazenar dados analíticos em tabelas desnormalizadas ou colunas JSON amplas no Postgres.
* *Prós*: Ingestão rápida sem validação rígida de schema.
* *Contras*: Impossibilidade de impor integridade referencial via chaves estrangeiras; lentidão em queries analíticas de agregação complexa e joins relacionais; propensão a dados corrompidos; violação de integridade matemática.

### Opção 2: Terceira Forma Normal (3NF / BCNF clássica)
Eliminar dependências parciais e transitivas, mantendo listas de nutrientes em colunas fixas (`nitrogen_pct`, `phosphorus_pct`, `potassium_pct`) ou arrays no fertilizante.
* *Prós*: Estrutura familiar e menor número de tabelas.
* *Contras*: Não atende compostos que possuem micronutrientes múltiplos (Enxofre, Cálcio, Magnésio, Zinco, Boro) sem alterar schema; não resolve dependências multivaloradas independentes entre sinônimos, classificações e composições, violando a 4ª Forma Normal.

### Opção 3: Quarta Forma Normal (4NF) Estrita com Camada de Views Analíticas (Escolhida)
Modelar todas as relações até a BCNF e decompor rigorosamente todas as Dependências Multivaloradas não-triviais ($X \twoheadrightarrow Y$) em tabelas independentes dedicadas com chaves candidatas bem definidas. Para performance de consulta, disponibilizar Views e Materialized Views pré-calculadas.
* *Prós*:
  - **Zero anomalias de redundância**: Nenhuma combinação cartesiana artificial entre sinônimos, composições e classificações tarifárias.
  - **Extensibilidade ilimitada (RNF04)**: Inclusão de novos fertilizantes, novos nutrientes, novos esquemas de classificação e novas fontes de dados sem quebrar código ou exigir migrações DDL destrutivas.
  - **Integridade Referencial Absoluta**: Todas as chaves estrangeiras com regras `RESTRICT` e `CASCADE` apropriadas.
  - **Rastreabilidade Ponta a Ponta (RNF02)**: Cada fato numérico (produção, comércio, preço) referencia tanto sua fonte (`source_id`) quanto a carga bruta que o originou (`raw_data_id`).
* *Contras*:
  - Exige queries com mais joins relacionais para consultas analíticas brutas.
  - *Mitigação*: Criação de Views especializadas no Postgres (`v_fertilizer_profiles`, `v_global_production_rankings`, `v_bilateral_trade_flows`, `v_brazil_external_dependency`, `v_price_benchmark_trends`) que abstraem a complexidade para o front-end e repositórios.

---

## 3. Decisão Escolhida

Adotar a **Quarta Forma Normal (4NF)** como padrão estrutural no banco de dados Supabase (PostgreSQL), organizando o schema em domínios lógicos claros:

### 3.1. Formalização Matemática da 4NF no Modelo

Uma relação $R$ está na **Quarta Forma Normal (4NF)** se e somente se, para toda dependência multivalorada não-trivial $X \twoheadrightarrow Y$ válida em $R$, $X$ é uma superchave de $R$.

As seguintes decomposições foram obrigatoriamente aplicadas:

#### A. Decomposição da Entidade Fertilizante
No modelo conceitual preliminar (RD01), um fertilizante concentrava composições químicas, nomes e códigos. Na 4NF, o fertilizante possui três fatos multivalorados mutuamente independentes:
1. $\text{fertilizer\_id} \twoheadrightarrow \text{nutrient\_code}$ (um fertilizante tem múltiplos nutrientes).
2. $\text{fertilizer\_id} \twoheadrightarrow \text{synonym\_name}$ (um fertilizante tem múltiplos nomes/traduções).
3. $\text{fertilizer\_id} \twoheadrightarrow \text{classification\_code}$ (um fertilizante tem múltiplos códigos tarifários HS/NCM/CAS).

Se armazenados juntos, para um fertilizante com 3 nutrientes, 4 sinônimos e 2 códigos HS, haveria $3 \times 4 \times 2 = 24$ linhas redundantes!
**Solução 4NF**:
- `fertilizers`: Armazena apenas atributos monovalorados funcionalmente dependentes da chave primária (`id`, `slug`, `canonical_name`, `category_id`, `cas_rn`, `chemical_formula`, `description`, `is_active`).
- `fertilizer_nutrients`: Chave primária composta `(fertilizer_id, nutrient_code)`. Registra teores típico, mínimo e máximo.
- `fertilizer_synonyms`: Chave única `(fertilizer_id, synonym_name)`. Registra aliases contextuais e idiomas.
- `fertilizer_classifications`: Chave única `(classification_system, classification_code, fertilizer_id)`. Registra códigos HS, NCM, CPC, CAS.

#### B. Decomposição da Entidade País
Um país possui fatos multivalorados independentes:
1. $\text{country\_id} \twoheadrightarrow \text{alias\_name}$ (ex: "Brazil", "Brasil", "Brésil").
2. $\text{country\_id} \twoheadrightarrow \text{source\_external\_code}$ (códigos de área FAOSTAT, códigos numéricos Comtrade, códigos de país MDIC).

**Solução 4NF**:
- `countries`: Apenas atributos canônicos e códigos padrão ISO 3166-1 (`id`, `iso2`, `iso3`, `numeric_code`, `name`, `official_name`, `region_id`, `subregion_id`).
- `country_aliases`: `(country_id, alias_name, source_id)`.
- `country_source_codes`: `(source_id, external_code) -> country_id`.

#### C. Isolamento de Dimensões Aduaneiras Específicas do Brasil (Comex Stat)
O comércio internacional padrão (UN Comtrade) opera na granularidade `(fertilizer_id, flow_type, exporter, importer, period)`. O Comex Stat brasileiro fornece atributos subnacionais multivalorados (UF de destino/origem, Recinto Alfandegário URF, Via de Transporte).
**Solução 4NF**:
- `trade_records`: Fato global universal de comércio exterior padronizado.
- `brazil_trade_details`: Tabela filha 1-para-1 ou 1-para-0 que estende `trade_records` apenas quando o dado provém do Comex Stat, contendo `brazilian_state_uf`, `transport_mode`, `entry_exit_urf`, `freight_value_usd` e `insurance_value_usd`.

#### D. Desacoplamento entre Mercados/Benchmarks e Cotações de Preço
- `price_markets`: Cadastro de hubs geográficos e incoterms (`id`, `code`, `name`, `benchmark_region_id`, `hub_port_name`, `incoterm`).
- `price_records`: Série temporal atômica `(fertilizer_id, benchmark_id, price_date, price_type, source_id) -> price, standard_price_usd_per_mt`.

---

## 4. Mapeamento das APIs Externas para o Schema

| API de Origem | Atributos Originais | Tabela Destino (4NF) | Atributos Mapeados |
| :--- | :--- | :--- | :--- |
| **FAOSTAT** (QCL, RFN, RFB) | `AreaCode`, `ItemCode`, `ElementCode` (51=Prod), `Year`, `Unit`, `Value`, `Flag` | `production_records`<br>`country_source_codes`<br>`fertilizer_classifications` | `fertilizer_id`, `country_id`, `period_start_date`, `standard_quantity_mt`, `data_status` (Official, Estimated) |
| **UN Comtrade** | `period`, `reporterCode`, `partnerCode`, `flowCode`, `cmdCode` (HS), `primaryValue`, `netWgt` | `trade_records`<br>`fertilizer_classifications` | `flow_type` (IMPORT, EXPORT), `exporter_country_id`, `importer_country_id`, `standard_quantity_mt`, `standard_value_usd` |
| **Comex Stat** (MDIC) | `CO_ANO`, `CO_MES`, `CO_NCM`, `CO_PAIS`, `SG_UF_NCM`, `CO_VIA`, `CO_URF`, `KG_LIQUIDO`, `VL_FOB`, `VL_FRETE` | `trade_records`<br>`brazil_trade_details` | `period_start_date`, `standard_quantity_mt`, `standard_value_usd`, `brazilian_state_uf`, `transport_mode`, `entry_exit_urf` |
| **FRED / World Bank** | `series_id`, `date`, `value`, commodity specs | `price_records`<br>`price_markets` | `benchmark_id`, `price_date`, `standard_price_usd_per_mt`, `currency_code = 'USD'` |

---

## 5. Segurança: Supabase Row Level Security (RLS)

Todas as tabelas do schema possuem Row Level Security (RLS) obrigatoriamente ativado (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`). As políticas são segregadas por *roles*:

1. **Role `anon` (Usuários Públicos / Visitantes — RF01 a RF15)**:
   - Permissão: `SELECT` irrestrito nas tabelas de catálogo (`fertilizers`, `fertilizer_categories`, `fertilizer_nutrients`, `countries`, `regions`, `measurement_units`, `currencies`).
   - Permissão: `SELECT` nas tabelas de fatos históricos (`production_records`, `trade_records`, `brazil_trade_details`, `price_records`, `consumption_records`) e em todas as views analíticas.
   - Restrição: Nenhum acesso de escrita (`INSERT`, `UPDATE`, `DELETE`).

2. **Role `authenticated` (Analistas)**:
   - Permissão: Leitura de dados operacionais e acesso a logs agregados de fontes.

3. **Role `service_role` (Pipelines de Coleta Automatizada e Back-end FertiPartner)**:
   - Permissão: Acesso total (`ALL` — INSERT, UPDATE, SELECT, DELETE) para inserção de dados brutos (`raw_data`), orquestração de coletas (`data_collection_runs`), processamento e carga de fatos padronizados.

---

## 6. Desempenho e Estratégia de Índices

Para atender aos requisitos de usabilidade (RNF06) e desempenho de agregação (RNF05):
1. **Chaves Primárias Naturais/Substitutas com UUIDs**: Uso de `uuid_generate_v4()` ou chaves canônicas para tabelas de fatos.
2. **Índices Compostos B-Tree**:
   - `production_records(fertilizer_id, period_start_date)`
   - `production_records(country_id, period_start_date)`
   - `trade_records(fertilizer_id, flow_type, period_start_date)`
   - `trade_records(importer_country_id, period_start_date)`
   - `trade_records(exporter_country_id, period_start_date)`
   - `price_records(fertilizer_id, benchmark_id, price_date)`
3. **Índices GIN**:
   - `raw_data(raw_payload jsonb_path_ops)` para consultas flexíveis de busca em payloads brutos JSONB.

---

## 7. Consequências da Decisão

### Positivas
* **Eliminação Completa de Anomalias**: Banco de dados robusto, à prova de inconsistências de dados e sem repetição desnecessária de dados.
* **Aderência Estrita aos Requisitos**: Cumpre integralmente os requisitos de negócio (RN01, RN02, RN03, RN04, RN05), funcionais (RF01 a RF24) e não-funcionais (RNF01 a RNF08).
* **Compatibilidade Imediata com Repositórios**: Compatível com `SupabaseFertilizerRepository` e `SupabaseRawDataRepository`.
* **Segurança Nativa**: RLS protege os dados analíticos e isola dados sensíveis de auditoria.

### Negativas / Riscos e Mitigações
* *Trade-off*: Maior número de tabelas exige maior rigor no desenvolvimento de consultas.
* *Mitigação*: Disponibilização de views analíticas oficiais consolidadas no banco de dados (`v_fertilizer_profiles`, `v_global_production_rankings`, etc.), simplificando o consumo tanto pela API Python quanto pela interface web.
