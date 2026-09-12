-- ==============================================================================
-- FertiPartner: Arquitetura de Dados em Quarta Forma Normal (4NF)
-- Migração Inicial: 20260902_000001_initial_schema_4nf.sql
-- Banco de Dados: Supabase (PostgreSQL 15+)
--
-- Conformidade: 4ª Forma Normal (4NF), BCNF, RLS, Rastreabilidade (RNF02),
-- Auditoria de Coleta e Compatibilidade com APIs (FAOSTAT, Comtrade, Comex Stat, WB)
-- ==============================================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. FUNÇÕES AUXILIARES E TRIGGERS
-- ==============================================================================

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = CLOCK_TIMESTAMP();
    RETURN NEW;
END;
$$;

-- ==============================================================================
-- 2. DOMÍNIO DE UNIDADES E MOEDAS (PADRONIZAÇÃO - RF08, RN02)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.currencies (
    code CHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.currencies IS 'Moedas internacionais para registro e conversão de valores aduaneiros e preços.';
COMMENT ON COLUMN public.currencies.code IS 'Código ISO 4217 alfabético de 3 caracteres (ex: USD, BRL, EUR).';

CREATE TABLE IF NOT EXISTS public.measurement_units (
    code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    unit_type VARCHAR(20) NOT NULL CHECK (unit_type IN ('MASS', 'VOLUME', 'NUTRIENT_MASS', 'COUNT')),
    to_metric_tons_factor NUMERIC(16, 8) NOT NULL,
    is_standard_unit BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.measurement_units IS 'Catálogo de unidades de medida físicas e agronômicas com fator de normalização.';
COMMENT ON COLUMN public.measurement_units.to_metric_tons_factor IS 'Fator multiplicador exato para converter a unidade original em Toneladas Métricas (MT).';

-- ==============================================================================
-- 3. DOMÍNIO GEOGRÁFICO E PADRONIZAÇÃO ESPACIAL (RD02)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.regions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(40) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_region_id INT REFERENCES public.regions(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.regions IS 'Continentes, blocos econômicos e sub-regiões estruturados em hierarquia.';

CREATE TABLE IF NOT EXISTS public.countries (
    id SERIAL PRIMARY KEY,
    iso2 CHAR(2) UNIQUE NOT NULL,
    iso3 CHAR(3) UNIQUE NOT NULL,
    numeric_code INT UNIQUE,
    name VARCHAR(100) NOT NULL,
    official_name VARCHAR(200),
    region_id INT REFERENCES public.regions(id) ON DELETE SET NULL,
    subregion_id INT REFERENCES public.regions(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

CREATE TRIGGER trg_countries_updated_at
BEFORE UPDATE ON public.countries
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.countries IS 'Catálogo central de países normalizado em BCNF baseado no padrão ISO 3166-1.';

-- 4NF: Isola a dependência multivalorada (MVD) Country ->> Alias Name
CREATE TABLE IF NOT EXISTS public.country_aliases (
    id BIGSERIAL PRIMARY KEY,
    country_id INT NOT NULL REFERENCES public.countries(id) ON DELETE CASCADE,
    alias_name VARCHAR(150) NOT NULL,
    language_code VARCHAR(10) DEFAULT 'pt',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_country_aliases UNIQUE (country_id, alias_name)
);

COMMENT ON TABLE public.country_aliases IS '4NF: Grafias alternativas e traduções de países isoladas para evitar anomalias de redundância.';

-- ==============================================================================
-- 4. DOMÍNIO DE FONTES, AUDITORIA E DADOS BRUTOS (RD07, RD08, RF19, RF20, RNF02)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.data_organizations (
    id SERIAL PRIMARY KEY,
    acronym VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    organization_type VARCHAR(50) NOT NULL DEFAULT 'INTERNATIONAL_ORGANIZATION',
    website_url VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.data_organizations IS 'Organizações provedoras de dados primários (ex: FAO, ONU, MDIC, USDA, Banco Mundial).';

CREATE TABLE IF NOT EXISTS public.data_sources (
    id SERIAL PRIMARY KEY,
    organization_id INT NOT NULL REFERENCES public.data_organizations(id) ON DELETE RESTRICT,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    api_docs_url VARCHAR(255),
    base_url VARCHAR(255),
    update_frequency VARCHAR(30) NOT NULL DEFAULT 'MONTHLY' CHECK (update_frequency IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUAL', 'IRREGULAR')),
    collection_method VARCHAR(50) NOT NULL DEFAULT 'REST_API' CHECK (collection_method IN ('REST_API', 'BULK_DOWNLOAD', 'WEB_SCRAPING', 'MANUAL_IMPORT')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.data_sources IS 'Catálogo formal de endpoints, datasets e APIs públicas monitoradas.';

-- 4NF: Isola a dependência multivalorada (MVD) Country ->> Source External Code (ex: FAO AreaCode, Comex CO_PAIS)
CREATE TABLE IF NOT EXISTS public.country_source_codes (
    id BIGSERIAL PRIMARY KEY,
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE CASCADE,
    external_code VARCHAR(50) NOT NULL,
    country_id INT NOT NULL REFERENCES public.countries(id) ON DELETE CASCADE,
    external_name VARCHAR(150),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_country_source_codes UNIQUE (source_id, external_code)
);

COMMENT ON TABLE public.country_source_codes IS '4NF: Mapeamento de chaves primárias externas das APIs para países ISO.';

CREATE TABLE IF NOT EXISTS public.data_collection_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE RESTRICT,
    trigger_type VARCHAR(30) NOT NULL DEFAULT 'AUTOMATIC' CHECK (trigger_type IN ('AUTOMATIC', 'MANUAL', 'SCHEDULED')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED')),
    records_fetched INT NOT NULL DEFAULT 0,
    records_inserted INT NOT NULL DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE public.data_collection_runs IS 'Auditoria rigorosa de cada pipeline de ingestão executado no sistema (RF19).';

CREATE TABLE IF NOT EXISTS public.raw_data (
    id BIGSERIAL PRIMARY KEY,
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE RESTRICT,
    collection_run_id UUID REFERENCES public.data_collection_runs(id) ON DELETE SET NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    reference_date DATE,
    endpoint_url TEXT,
    payload_hash CHAR(64),
    raw_payload JSONB NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'RAW' CHECK (status IN ('RAW', 'VALIDATED', 'PROCESSED', 'FAILED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.raw_data IS 'Armazenamento imutável de payloads brutos em JSONB para reprodutibilidade e auditoria (RD08, RF20).';

-- ==============================================================================
-- 5. DOMÍNIO DE FERTILIZANTES EM 4NF (RD01, RF01, RF02, RF21)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.fertilizer_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(40) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.fertilizer_categories IS 'Categorias agronômicas canônicas (Nitrogenados, Fosfatados, Potássicos, NPK Misturas, Micronutrientes).';

CREATE TABLE IF NOT EXISTS public.fertilizers (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    canonical_name VARCHAR(150) NOT NULL,
    category_id INT NOT NULL REFERENCES public.fertilizer_categories(id) ON DELETE RESTRICT,
    cas_rn VARCHAR(30),
    chemical_formula VARCHAR(100),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

CREATE TRIGGER trg_fertilizers_updated_at
BEFORE UPDATE ON public.fertilizers
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.fertilizers IS 'Entidade central contendo apenas atributos funcionais monovalorados em BCNF.';

-- 4NF: Isola a dependência multivalorada (MVD) Fertilizer ->> Nutrient Percentage
CREATE TABLE IF NOT EXISTS public.fertilizer_nutrients (
    fertilizer_id INT NOT NULL REFERENCES public.fertilizers(id) ON DELETE CASCADE,
    nutrient_code VARCHAR(20) NOT NULL CHECK (nutrient_code IN ('N', 'P2O5', 'K2O', 'S', 'CA', 'MG', 'ZN', 'B', 'CU', 'MN', 'MO', 'FE')),
    percentage_typical NUMERIC(5, 2) CHECK (percentage_typical >= 0 AND percentage_typical <= 100),
    percentage_min NUMERIC(5, 2) CHECK (percentage_min >= 0 AND percentage_min <= 100),
    percentage_max NUMERIC(5, 2) CHECK (percentage_max >= 0 AND percentage_max <= 100),
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    PRIMARY KEY (fertilizer_id, nutrient_code),
    CONSTRAINT chk_fertilizer_nutrient_range CHECK (percentage_min IS NULL OR percentage_max IS NULL OR percentage_min <= percentage_max)
);

COMMENT ON TABLE public.fertilizer_nutrients IS '4NF: Teores garantidos e típicos de nutrientes químicos decompostos em relação atômica.';

-- 4NF: Isola a dependência multivalorada (MVD) Fertilizer ->> Synonym Name
CREATE TABLE IF NOT EXISTS public.fertilizer_synonyms (
    id BIGSERIAL PRIMARY KEY,
    fertilizer_id INT NOT NULL REFERENCES public.fertilizers(id) ON DELETE CASCADE,
    synonym_name VARCHAR(200) NOT NULL,
    language_code VARCHAR(10) NOT NULL DEFAULT 'pt',
    context VARCHAR(50) DEFAULT 'COMMERCIAL',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_fertilizer_synonyms UNIQUE (fertilizer_id, synonym_name)
);

COMMENT ON TABLE public.fertilizer_synonyms IS '4NF: Nomes comerciais, grafias e traduções de fertilizantes decompostos em relação atômica.';

-- 4NF: Isola a dependência multivalorada (MVD) Fertilizer ->> Tariff Classification (HS, NCM, CPC)
CREATE TABLE IF NOT EXISTS public.fertilizer_classifications (
    id BIGSERIAL PRIMARY KEY,
    fertilizer_id INT NOT NULL REFERENCES public.fertilizers(id) ON DELETE CASCADE,
    classification_system VARCHAR(30) NOT NULL CHECK (classification_system IN ('HS6', 'NCM8', 'CPC', 'CAS', 'FAO_ITEM')),
    classification_code VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_fertilizer_classifications UNIQUE (classification_system, classification_code, fertilizer_id)
);

COMMENT ON TABLE public.fertilizer_classifications IS '4NF: Classificações aduaneiras e códigos alfandegários decompostos em relação atômica.';

-- ==============================================================================
-- 6. FATOS EM 4NF: PRODUÇÃO GLOBAL (RD03, RF03)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.production_records (
    id BIGSERIAL PRIMARY KEY,
    fertilizer_id INT NOT NULL REFERENCES public.fertilizers(id) ON DELETE RESTRICT,
    country_id INT NOT NULL REFERENCES public.countries(id) ON DELETE RESTRICT,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL DEFAULT 'YEAR' CHECK (period_type IN ('YEAR', 'MONTH', 'QUARTER')),
    original_quantity NUMERIC(18, 4),
    original_unit_code VARCHAR(20) REFERENCES public.measurement_units(code) ON DELETE RESTRICT,
    standard_quantity_mt NUMERIC(18, 4) NOT NULL CHECK (standard_quantity_mt >= 0),
    data_status VARCHAR(30) NOT NULL DEFAULT 'OFFICIAL' CHECK (data_status IN ('OFFICIAL', 'ESTIMATED', 'PROVISIONAL', 'UNOFFICIAL')),
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE RESTRICT,
    raw_data_id BIGINT REFERENCES public.raw_data(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_production_facts UNIQUE (fertilizer_id, country_id, period_start_date, period_type, source_id),
    CONSTRAINT chk_production_dates CHECK (period_start_date <= period_end_date)
);

CREATE TRIGGER trg_production_records_updated_at
BEFORE UPDATE ON public.production_records
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.production_records IS 'Fato de produção agrícola e industrial em 4NF. Sem MVDs e com quantidade padronizada em MT.';

-- ==============================================================================
-- 7. FATOS EM 4NF: COMÉRCIO INTERNACIONAL (RD04, RF04, RF05, RF06)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.trade_records (
    id BIGSERIAL PRIMARY KEY,
    fertilizer_id INT NOT NULL REFERENCES public.fertilizers(id) ON DELETE RESTRICT,
    flow_type VARCHAR(20) NOT NULL CHECK (flow_type IN ('IMPORT', 'EXPORT', 'RE_EXPORT', 'RE_IMPORT')),
    exporter_country_id INT NOT NULL REFERENCES public.countries(id) ON DELETE RESTRICT,
    importer_country_id INT NOT NULL REFERENCES public.countries(id) ON DELETE RESTRICT,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL DEFAULT 'MONTH' CHECK (period_type IN ('MONTH', 'YEAR', 'QUARTER')),
    original_quantity NUMERIC(18, 4),
    original_unit_code VARCHAR(20) REFERENCES public.measurement_units(code) ON DELETE RESTRICT,
    standard_quantity_mt NUMERIC(18, 4) NOT NULL CHECK (standard_quantity_mt >= 0),
    original_value NUMERIC(18, 4),
    currency_code CHAR(3) REFERENCES public.currencies(code) ON DELETE RESTRICT,
    standard_value_usd NUMERIC(18, 4) CHECK (standard_value_usd IS NULL OR standard_value_usd >= 0),
    incoterm VARCHAR(10) CHECK (incoterm IN ('FOB', 'CIF', 'CFR', 'DESconhecido')),
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE RESTRICT,
    raw_data_id BIGINT REFERENCES public.raw_data(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_trade_facts UNIQUE (fertilizer_id, flow_type, exporter_country_id, importer_country_id, period_start_date, period_type, source_id),
    CONSTRAINT chk_trade_dates CHECK (period_start_date <= period_end_date),
    CONSTRAINT chk_trade_distinct_countries CHECK (exporter_country_id <> importer_country_id)
);

CREATE TRIGGER trg_trade_records_updated_at
BEFORE UPDATE ON public.trade_records
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.trade_records IS 'Fato universal de fluxos de comércio exterior bilateral em 4NF.';

-- 4NF: Isola dimensões aduaneiras subnacionais do Brasil (Comex Stat)
CREATE TABLE IF NOT EXISTS public.brazil_trade_details (
    trade_record_id BIGINT PRIMARY KEY REFERENCES public.trade_records(id) ON DELETE CASCADE,
    ncm_code VARCHAR(10) NOT NULL,
    brazilian_state_uf CHAR(2) NOT NULL,
    transport_mode VARCHAR(30) CHECK (transport_mode IN ('MARITIMA', 'RODOVIARIA', 'FERROVIARIA', 'AEREA', 'FLUVIAL', 'OUTROS')),
    entry_exit_urf VARCHAR(120),
    freight_value_usd NUMERIC(18, 4) CHECK (freight_value_usd IS NULL OR freight_value_usd >= 0),
    insurance_value_usd NUMERIC(18, 4) CHECK (insurance_value_usd IS NULL OR insurance_value_usd >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.brazil_trade_details IS '4NF: Extensão de comércio específica brasileira (UF, modal, URF) isolada da tabela global.';

-- ==============================================================================
-- 8. FATOS EM 4NF: PREÇOS E BENCHMARKS (RD05, RF07)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.price_markets (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    benchmark_region_id INT REFERENCES public.regions(id) ON DELETE SET NULL,
    country_id INT REFERENCES public.countries(id) ON DELETE SET NULL,
    hub_port_name VARCHAR(100),
    incoterm VARCHAR(10) NOT NULL DEFAULT 'FOB' CHECK (incoterm IN ('FOB', 'CFR', 'CIF', 'EXW', 'FCA')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP()
);

COMMENT ON TABLE public.price_markets IS 'Hubs e praças de negociação de referência (ex: Baltic FOB, US Gulf FOB, Brasil CFR).';

CREATE TABLE IF NOT EXISTS public.price_records (
    id BIGSERIAL PRIMARY KEY,
    fertilizer_id INT NOT NULL REFERENCES public.fertilizers(id) ON DELETE RESTRICT,
    benchmark_id INT NOT NULL REFERENCES public.price_markets(id) ON DELETE RESTRICT,
    price_date DATE NOT NULL,
    frequency VARCHAR(20) NOT NULL DEFAULT 'MONTHLY' CHECK (frequency IN ('DAILY', 'WEEKLY', 'MONTHLY')),
    price_type VARCHAR(30) NOT NULL DEFAULT 'SPOT' CHECK (price_type IN ('SPOT', 'BENCHMARK', 'CONTRACT')),
    original_price NUMERIC(14, 4) NOT NULL CHECK (original_price >= 0),
    currency_code CHAR(3) NOT NULL REFERENCES public.currencies(code) ON DELETE RESTRICT,
    original_unit_code VARCHAR(20) NOT NULL REFERENCES public.measurement_units(code) ON DELETE RESTRICT,
    standard_price_usd_per_mt NUMERIC(14, 4) NOT NULL CHECK (standard_price_usd_per_mt >= 0),
    data_status VARCHAR(30) NOT NULL DEFAULT 'OFFICIAL' CHECK (data_status IN ('OFFICIAL', 'ESTIMATED', 'PROVISIONAL')),
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE RESTRICT,
    raw_data_id BIGINT REFERENCES public.raw_data(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_price_facts UNIQUE (fertilizer_id, benchmark_id, price_date, price_type, source_id)
);

CREATE TRIGGER trg_price_records_updated_at
BEFORE UPDATE ON public.price_records
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.price_records IS 'Fato de séries temporais de preços com normalização em USD/MT em 4NF.';

-- ==============================================================================
-- 9. FATOS EM 4NF: CONSUMO E DEMANDA (RD06)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.consumption_records (
    id BIGSERIAL PRIMARY KEY,
    fertilizer_id INT NOT NULL REFERENCES public.fertilizers(id) ON DELETE RESTRICT,
    country_id INT NOT NULL REFERENCES public.countries(id) ON DELETE RESTRICT,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL DEFAULT 'YEAR' CHECK (period_type IN ('YEAR', 'MONTH', 'QUARTER')),
    original_quantity NUMERIC(18, 4),
    original_unit_code VARCHAR(20) REFERENCES public.measurement_units(code) ON DELETE RESTRICT,
    standard_quantity_mt NUMERIC(18, 4) NOT NULL CHECK (standard_quantity_mt >= 0),
    sector VARCHAR(30) NOT NULL DEFAULT 'AGRICULTURE' CHECK (sector IN ('AGRICULTURE', 'INDUSTRIAL', 'TOTAL')),
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE RESTRICT,
    raw_data_id BIGINT REFERENCES public.raw_data(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_consumption_facts UNIQUE (fertilizer_id, country_id, period_start_date, period_type, sector, source_id),
    CONSTRAINT chk_consumption_dates CHECK (period_start_date <= period_end_date)
);

CREATE TRIGGER trg_consumption_records_updated_at
BEFORE UPDATE ON public.consumption_records
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.consumption_records IS 'Fato de consumo aparente e entrega de fertilizantes ao mercado final em 4NF.';

CREATE TABLE IF NOT EXISTS public.country_indicators (
    id BIGSERIAL PRIMARY KEY,
    country_id INT NOT NULL REFERENCES public.countries(id) ON DELETE RESTRICT,
    indicator_code VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(255) NOT NULL,
    year INT NOT NULL,
    value NUMERIC(18, 4) NOT NULL,
    unit_code VARCHAR(30) NOT NULL DEFAULT 'KG_PER_HA',
    data_status VARCHAR(30) NOT NULL DEFAULT 'OFFICIAL' CHECK (data_status IN ('OFFICIAL', 'ESTIMATED', 'PROVISIONAL')),
    source_id INT NOT NULL REFERENCES public.data_sources(id) ON DELETE RESTRICT,
    raw_data_id BIGINT REFERENCES public.raw_data(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CLOCK_TIMESTAMP(),
    CONSTRAINT uq_country_indicator_facts UNIQUE (country_id, indicator_code, year, source_id)
);

CREATE TRIGGER trg_country_indicators_updated_at
BEFORE UPDATE ON public.country_indicators
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

COMMENT ON TABLE public.country_indicators IS 'Fatos e indicadores macroeconômicos e de intensidade agronômica por país e ano (ex.: kg de adubo/ha).';

-- ==============================================================================
-- 10. ÍNDICES DE DESEMPENHO (RNF05)
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_prod_fert_date ON public.production_records(fertilizer_id, period_start_date);
CREATE INDEX IF NOT EXISTS idx_prod_country_date ON public.production_records(country_id, period_start_date);
CREATE INDEX IF NOT EXISTS idx_trade_fert_flow ON public.trade_records(fertilizer_id, flow_type, period_start_date);
CREATE INDEX IF NOT EXISTS idx_trade_exporter ON public.trade_records(exporter_country_id, period_start_date);
CREATE INDEX IF NOT EXISTS idx_trade_importer ON public.trade_records(importer_country_id, period_start_date);
CREATE INDEX IF NOT EXISTS idx_price_fert_date ON public.price_records(fertilizer_id, benchmark_id, price_date);
CREATE INDEX IF NOT EXISTS idx_consump_fert_date ON public.consumption_records(fertilizer_id, country_id, period_start_date);
CREATE INDEX IF NOT EXISTS idx_country_indicators_lookup ON public.country_indicators(country_id, indicator_code, year);
CREATE INDEX IF NOT EXISTS idx_raw_data_hash ON public.raw_data(payload_hash);
CREATE INDEX IF NOT EXISTS idx_raw_data_source ON public.raw_data(source_id, reference_date);
CREATE INDEX IF NOT EXISTS idx_raw_data_payload_gin ON public.raw_data USING gin(raw_payload);

-- ==============================================================================
-- 11. VIEWS ANALÍTICAS DE ALTA PERFORMANCE (RF02, RF03, RF06, RF07, RF13, RF14, RNF05)
-- ==============================================================================

-- 11.1. Perfil completo do fertilizante com composição nutricional
CREATE OR REPLACE VIEW public.v_fertilizer_profiles
WITH (security_invoker = true) AS
SELECT 
    f.id,
    f.slug,
    f.canonical_name,
    c.name AS category_name,
    f.chemical_formula,
    f.cas_rn,
    f.description,
    COALESCE(
        jsonb_object_agg(fn.nutrient_code, fn.percentage_typical) 
        FILTER (WHERE fn.nutrient_code IS NOT NULL), 
        '{}'::jsonb
    ) AS typical_nutrients,
    ARRAY_AGG(DISTINCT fs.synonym_name) FILTER (WHERE fs.synonym_name IS NOT NULL) AS synonyms,
    ARRAY_AGG(DISTINCT fc.classification_code) FILTER (WHERE fc.classification_code IS NOT NULL) AS hs_ncm_codes
FROM public.fertilizers f
JOIN public.fertilizer_categories c ON f.category_id = c.id
LEFT JOIN public.fertilizer_nutrients fn ON f.id = fn.fertilizer_id
LEFT JOIN public.fertilizer_synonyms fs ON f.id = fs.fertilizer_id
LEFT JOIN public.fertilizer_classifications fc ON f.id = fc.fertilizer_id
GROUP BY f.id, f.slug, f.canonical_name, c.name, f.chemical_formula, f.cas_rn, f.description;

COMMENT ON VIEW public.v_fertilizer_profiles IS 'Visão agregada de fertilizantes com composição e sinônimos.';

-- 11.2. Ranking de produção global e participação percentual (RF03, RF15)
CREATE OR REPLACE VIEW public.v_global_production_rankings
WITH (security_invoker = true) AS
WITH annual_production AS (
    SELECT 
        pr.fertilizer_id,
        f.canonical_name AS fertilizer_name,
        pr.country_id,
        co.name AS country_name,
        co.iso3 AS country_iso3,
        EXTRACT(YEAR FROM pr.period_start_date)::INT AS production_year,
        pr.standard_quantity_mt,
        SUM(pr.standard_quantity_mt) OVER(PARTITION BY pr.fertilizer_id, EXTRACT(YEAR FROM pr.period_start_date)) AS global_total_mt
    FROM public.production_records pr
    JOIN public.fertilizers f ON pr.fertilizer_id = f.id
    JOIN public.countries co ON pr.country_id = co.id
    WHERE pr.period_type = 'YEAR'
)
SELECT 
    fertilizer_id,
    fertilizer_name,
    country_id,
    country_name,
    country_iso3,
    production_year,
    standard_quantity_mt,
    global_total_mt,
    ROUND((standard_quantity_mt / NULLIF(global_total_mt, 0)) * 100, 2) AS global_market_share_pct,
    DENSE_RANK() OVER(PARTITION BY fertilizer_id, production_year ORDER BY standard_quantity_mt DESC) AS rank_position
FROM annual_production;

COMMENT ON VIEW public.v_global_production_rankings IS 'Ranking anual de produtores globais de fertilizantes e market share.';

-- 11.3. Fluxos bilaterais de comércio exterior para Sankey e Mapas (RF06)
CREATE OR REPLACE VIEW public.v_bilateral_trade_flows
WITH (security_invoker = true) AS
SELECT 
    tr.fertilizer_id,
    f.canonical_name AS fertilizer_name,
    tr.flow_type,
    exp.id AS exporter_id,
    exp.name AS exporter_country,
    exp.iso3 AS exporter_iso3,
    imp.id AS importer_id,
    imp.name AS importer_country,
    imp.iso3 AS importer_iso3,
    EXTRACT(YEAR FROM tr.period_start_date)::INT AS trade_year,
    SUM(tr.standard_quantity_mt) AS total_quantity_mt,
    SUM(tr.standard_value_usd) AS total_value_usd,
    ROUND(SUM(tr.standard_value_usd) / NULLIF(SUM(tr.standard_quantity_mt), 0), 2) AS avg_usd_per_mt
FROM public.trade_records tr
JOIN public.fertilizers f ON tr.fertilizer_id = f.id
JOIN public.countries exp ON tr.exporter_country_id = exp.id
JOIN public.countries imp ON tr.importer_country_id = imp.id
GROUP BY 
    tr.fertilizer_id, f.canonical_name, tr.flow_type,
    exp.id, exp.name, exp.iso3,
    imp.id, imp.name, imp.iso3,
    EXTRACT(YEAR FROM tr.period_start_date)::INT;

COMMENT ON VIEW public.v_bilateral_trade_flows IS 'Fluxos de comércio internacional consolidados para diagramas e mapas.';

-- 11.4. Dependência Externa Brasileira de Fertilizantes (RF13, RF14)
CREATE OR REPLACE VIEW public.v_brazil_external_dependency
WITH (security_invoker = true) AS
WITH br_country AS (
    SELECT id FROM public.countries WHERE iso2 = 'BR' LIMIT 1
),
br_imports AS (
    SELECT 
        tr.fertilizer_id,
        EXTRACT(YEAR FROM tr.period_start_date)::INT AS ref_year,
        SUM(tr.standard_quantity_mt) AS import_mt
    FROM public.trade_records tr, br_country br
    WHERE tr.importer_country_id = br.id AND tr.flow_type = 'IMPORT'
    GROUP BY tr.fertilizer_id, EXTRACT(YEAR FROM tr.period_start_date)::INT
),
br_exports AS (
    SELECT 
        tr.fertilizer_id,
        EXTRACT(YEAR FROM tr.period_start_date)::INT AS ref_year,
        SUM(tr.standard_quantity_mt) AS export_mt
    FROM public.trade_records tr, br_country br
    WHERE tr.exporter_country_id = br.id AND tr.flow_type = 'EXPORT'
    GROUP BY tr.fertilizer_id, EXTRACT(YEAR FROM tr.period_start_date)::INT
),
br_prod AS (
    SELECT 
        pr.fertilizer_id,
        EXTRACT(YEAR FROM pr.period_start_date)::INT AS ref_year,
        SUM(pr.standard_quantity_mt) AS prod_mt
    FROM public.production_records pr, br_country br
    WHERE pr.country_id = br.id AND pr.period_type = 'YEAR'
    GROUP BY pr.fertilizer_id, EXTRACT(YEAR FROM pr.period_start_date)::INT
),
combined_periods AS (
    SELECT fertilizer_id, ref_year FROM br_imports
    UNION
    SELECT fertilizer_id, ref_year FROM br_exports
    UNION
    SELECT fertilizer_id, ref_year FROM br_prod
)
SELECT 
    f.id AS fertilizer_id,
    f.canonical_name AS fertilizer_name,
    cp.ref_year,
    p.prod_mt AS national_production_mt,
    COALESCE(i.import_mt, 0) AS total_imports_mt,
    COALESCE(e.export_mt, 0) AS total_exports_mt,
    CASE 
        WHEN p.prod_mt IS NOT NULL THEN (p.prod_mt + COALESCE(i.import_mt, 0) - COALESCE(e.export_mt, 0))
        ELSE NULL 
    END AS apparent_consumption_mt,
    CASE 
        WHEN p.prod_mt IS NOT NULL AND (p.prod_mt + COALESCE(i.import_mt, 0) - COALESCE(e.export_mt, 0)) > 0 
        THEN ROUND(
            (COALESCE(i.import_mt, 0) / 
            (p.prod_mt + COALESCE(i.import_mt, 0) - COALESCE(e.export_mt, 0))) * 100, 
            2
        )
        ELSE NULL 
    END AS external_dependency_pct,
    CASE
        WHEN p.prod_mt IS NOT NULL AND i.import_mt IS NOT NULL THEN 'CONSOLIDATED'
        WHEN p.prod_mt IS NULL AND i.import_mt IS NOT NULL THEN 'PENDING_PRODUCTION'
        WHEN p.prod_mt IS NOT NULL AND i.import_mt IS NULL THEN 'PENDING_TRADE'
        ELSE 'INSUFFICIENT_DATA'
    END AS data_status,
    (p.prod_mt IS NOT NULL AND i.import_mt IS NOT NULL) AS is_consolidated
FROM combined_periods cp
JOIN public.fertilizers f ON cp.fertilizer_id = f.id
LEFT JOIN br_imports i ON cp.fertilizer_id = i.fertilizer_id AND cp.ref_year = i.ref_year
LEFT JOIN br_exports e ON cp.fertilizer_id = e.fertilizer_id AND cp.ref_year = e.ref_year
LEFT JOIN br_prod p ON cp.fertilizer_id = p.fertilizer_id AND cp.ref_year = p.ref_year;

COMMENT ON VIEW public.v_brazil_external_dependency IS 'Indicador oficial da taxa de dependência externa do Brasil com proteção contra assimetria temporal.';

-- 11.5. Tendências de preços de fertilizantes (RF07)
CREATE OR REPLACE VIEW public.v_price_benchmark_trends
WITH (security_invoker = true) AS
SELECT 
    pr.fertilizer_id,
    f.canonical_name AS fertilizer_name,
    pr.benchmark_id,
    pm.name AS benchmark_name,
    pm.hub_port_name,
    pm.incoterm,
    pr.price_date,
    pr.standard_price_usd_per_mt,
    LAG(pr.standard_price_usd_per_mt, 1) OVER(
        PARTITION BY pr.fertilizer_id, pr.benchmark_id 
        ORDER BY pr.price_date
    ) AS prev_price_usd_per_mt,
    ROUND(
        ((pr.standard_price_usd_per_mt - LAG(pr.standard_price_usd_per_mt, 1) OVER(
            PARTITION BY pr.fertilizer_id, pr.benchmark_id ORDER BY pr.price_date
        )) / NULLIF(LAG(pr.standard_price_usd_per_mt, 1) OVER(
            PARTITION BY pr.fertilizer_id, pr.benchmark_id ORDER BY pr.price_date
        ), 0)) * 100, 
        2
    ) AS month_over_month_pct_change,
    ROUND(
        AVG(pr.standard_price_usd_per_mt) OVER(
            PARTITION BY pr.fertilizer_id, pr.benchmark_id 
            ORDER BY pr.price_date 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS moving_avg_3m_usd
FROM public.price_records pr
JOIN public.fertilizers f ON pr.fertilizer_id = f.id
JOIN public.price_markets pm ON pr.benchmark_id = pm.id;

COMMENT ON VIEW public.v_price_benchmark_trends IS 'Séries históricas de preços com variações percentuais e média móvel de 3 meses.';


COMMENT ON VIEW public.v_price_benchmark_trends IS 'Séries históricas de preços com variações percentuais e média móvel de 3 meses.';

-- ==============================================================================
-- 12. SEGURANÇA: ROW LEVEL SECURITY (RLS) (RNF08)
-- ==============================================================================

-- Ativa RLS em todas as tabelas
ALTER TABLE public.currencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurement_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.regions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.countries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.country_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.country_source_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_collection_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.raw_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fertilizer_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fertilizers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fertilizer_nutrients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fertilizer_synonyms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fertilizer_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.production_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trade_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brazil_trade_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.price_markets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.price_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consumption_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.country_indicators ENABLE ROW LEVEL SECURITY;

-- 12.1. Políticas de Leitura Pública (anon e authenticated para catálogo e dados históricos)
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_type = 'BASE TABLE'
          AND table_name NOT IN ('raw_data', 'data_collection_runs')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS p_public_read ON public.%I', tbl);
        EXECUTE format('CREATE POLICY p_public_read ON public.%I FOR SELECT TO anon, authenticated USING (true)', tbl);
    END LOOP;
END;
$$;

-- 12.2. Políticas de Leitura Restrita para logs e raw_data (apenas usuários autenticados e service_role)
DROP POLICY IF EXISTS p_raw_data_read ON public.raw_data;
CREATE POLICY p_raw_data_read ON public.raw_data FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS p_runs_read ON public.data_collection_runs;
CREATE POLICY p_runs_read ON public.data_collection_runs FOR SELECT TO authenticated USING (true);

-- 12.3. Políticas de Escrita Total para service_role (back-end e pipelines de ingestão)
DO $$
DECLARE
    tbl text;
BEGIN
    FOR tbl IN
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS p_service_role_all ON public.%I', tbl);
        EXECUTE format('CREATE POLICY p_service_role_all ON public.%I FOR ALL TO service_role USING (true) WITH CHECK (true)', tbl);
    END LOOP;
END;
$$;

-- 12.4. Concessão de Privilégios Básicos às Roles do Supabase
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO anon, authenticated, service_role;

-- ==============================================================================
-- 13. SEED DATA INICIAL: CATÁLOGO DE REFERÊNCIA
-- ==============================================================================

-- 13.1. Moedas
INSERT INTO public.currencies (code, name, symbol) VALUES
('USD', 'Dólar Americano', '$'),
('BRL', 'Real Brasileiro', 'R$'),
('EUR', 'Euro', '€'),
('CNY', 'Yuan Chinês', '¥')
ON CONFLICT (code) DO NOTHING;

-- 13.2. Unidades de Medida
INSERT INTO public.measurement_units (code, name, unit_type, to_metric_tons_factor, is_standard_unit) VALUES
('MT', 'Tonelada Métrica', 'MASS', 1.00000000, TRUE),
('KG', 'Quilograma', 'MASS', 0.00100000, FALSE),
('SHORT_TON', 'Tonelada Curta (US)', 'MASS', 0.90718474, FALSE),
('NUTRIENT_MT', 'Tonelada de Nutriente', 'NUTRIENT_MASS', 1.00000000, FALSE),
('LITER', 'Litro', 'VOLUME', 0.00100000, FALSE)
ON CONFLICT (code) DO NOTHING;

-- 13.3. Regiões Principais
INSERT INTO public.regions (id, code, name, parent_region_id) VALUES
(1, 'GLOBAL', 'Global', NULL),
(2, 'AMERICAS', 'Américas', 1),
(3, 'SOUTH_AMERICA', 'América do Sul', 2),
(4, 'NORTH_AMERICA', 'América do Norte', 2),
(5, 'ASIA', 'Ásia', 1),
(6, 'EUROPE', 'Europa', 1),
(7, 'AFRICA', 'África', 1),
(8, 'MIDDLE_EAST', 'Oriente Médio', 1)
ON CONFLICT (code) DO NOTHING;

-- 13.4. Países Estratégicos
INSERT INTO public.countries (id, iso2, iso3, numeric_code, name, official_name, region_id, subregion_id) VALUES
(1, 'BR', 'BRA', 76, 'Brasil', 'República Federativa do Brasil', 2, 3),
(2, 'CN', 'CHN', 156, 'China', 'República Popular da China', 5, NULL),
(3, 'IN', 'IND', 356, 'Índia', 'República da Índia', 5, NULL),
(4, 'US', 'USA', 840, 'Estados Unidos', 'Estados Unidos da América', 2, 4),
(5, 'RU', 'RUS', 643, 'Rússia', 'Federação Russa', 6, NULL),
(6, 'CA', 'CAN', 124, 'Canadá', 'Canadá', 2, 4),
(7, 'MA', 'MAR', 504, 'Marrocos', 'Reino de Marrocos', 7, NULL),
(8, 'BY', 'BLR', 112, 'Belarus', 'República de Belarus', 6, NULL),
(9, 'QA', 'QAT', 634, 'Catar', 'Estado do Catar', 8, NULL),
(10, 'SA', 'SAU', 682, 'Arábia Saudita', 'Reino da Arábia Saudita', 8, NULL),
(11, 'EG', 'EGY', 818, 'Egito', 'República Árabe do Egito', 7, NULL),
(12, 'AR', 'ARG', 32, 'Argentina', 'República Argentina', 2, 3),
(13, 'DE', 'DEU', 276, 'Alemanha', 'República Federal da Alemanha', 6, NULL),
(14, 'NO', 'NOR', 578, 'Noruega', 'Reino da Noruega', 6, NULL)
ON CONFLICT (iso2) DO NOTHING;

-- 13.5. Organizações e Fontes de Dados
INSERT INTO public.data_organizations (id, acronym, name, website_url) VALUES
(1, 'FAO', 'Organização das Nações Unidas para a Alimentação e a Agricultura', 'https://www.fao.org'),
(2, 'UN_STAT', 'Divisão de Estatísticas das Nações Unidas', 'https://unstats.un.org'),
(3, 'MDIC', 'Ministério do Desenvolvimento, Indústria, Comércio e Serviços (Brasil)', 'https://www.gov.br/mdic'),
(4, 'USDA', 'Departamento de Agricultura dos Estados Unidos', 'https://www.usda.gov'),
(5, 'WORLD_BANK', 'Grupo Banco Mundial', 'https://www.worldbank.org'),
(6, 'FRED', 'Federal Reserve Bank of St. Louis', 'https://fred.stlouisfed.org')
ON CONFLICT (acronym) DO NOTHING;

INSERT INTO public.data_sources (id, organization_id, code, name, api_docs_url, base_url, update_frequency) VALUES
(1, 1, 'FAOSTAT_RFN', 'FAOSTAT Fertilizers by Nutrient', 'https://www.fao.org/faostat/en/docs/redoc-static.html', 'https://fenixservices.fao.org/faostat/api/v1/en/data/RFN', 'ANNUAL'),
(2, 1, 'FAOSTAT_RFB', 'FAOSTAT Fertilizers by Product', 'https://www.fao.org/faostat/en/docs/redoc-static.html', 'https://fenixservices.fao.org/faostat/api/v1/en/data/RFB', 'ANNUAL'),
(3, 2, 'UN_COMTRADE', 'UN Comtrade API v1', 'https://github.com/uncomtrade/comtradeapicall', 'https://comtradeapi.un.org/public/v1', 'MONTHLY'),
(4, 3, 'COMEXSTAT_IMP', 'Comex Stat Importações (Brasil)', 'https://api-comexstat.mdic.gov.br/docs#/', 'https://api-comexstat.mdic.gov.br/general', 'MONTHLY'),
(5, 3, 'COMEXSTAT_EXP', 'Comex Stat Exportações (Brasil)', 'https://api-comexstat.mdic.gov.br/docs#/', 'https://api-comexstat.mdic.gov.br/general', 'MONTHLY'),
(6, 5, 'WB_COMMODITY_PRICES', 'World Bank Commodity Markets (Pink Sheet)', 'https://www.worldbank.org/en/research/commodity-markets', 'https://api.worldbank.org/v2', 'MONTHLY'),
(7, 6, 'FRED_FERT_PRICES', 'FRED St. Louis Commodity Prices', 'https://fred.stlouisfed.org/docs/api/fred/', 'https://api.stlouisfed.org/fred', 'MONTHLY'),
(8, 5, 'WB_INDICATORS', 'World Bank World Development Indicators', 'https://datahelpdesk.worldbank.org/knowledgebase/articles/888548-world-bank-apis', 'https://api.worldbank.org/v2', 'ANNUAL'),
(9, 1, 'FAOSTAT_PP', 'FAOSTAT Producer Prices / Prices Paid', 'https://www.fao.org/faostat/en/docs/redoc-static.html', 'https://faostatservices.fao.org/api/v1/en/data/PP', 'ANNUAL')
ON CONFLICT (code) DO NOTHING;

-- 13.6. Categorias de Fertilizantes
INSERT INTO public.fertilizer_categories (id, code, name, description) VALUES
(1, 'NITROGENOUS', 'Fertilizantes Nitrogenados', 'Produtos ricos em Nitrogênio (N) essenciais para crescimento vegetativo.'),
(2, 'PHOSPHATIC', 'Fertilizantes Fosfatados', 'Produtos ricos em Fósforo (P2O5) fundamentais para desenvolvimento radicular e energia celular.'),
(3, 'POTASSIC', 'Fertilizantes Potássicos', 'Produtos ricos em Potássio (K2O) para tolerância hídrica, enchimento de grãos e qualidade.'),
(4, 'NPK_MIXTURES', 'Misturas e Complexos NPK', 'Fertilizantes formulados combinando dois ou mais macronutrientes primários.'),
(5, 'MICRONUTRIENTS', 'Micronutrientes', 'Nutrientes de demanda em pequenas frações (Zn, B, Cu, Mn, Mo, Fe).')
ON CONFLICT (code) DO NOTHING;

-- 13.7. Fertilizantes Centrais do Setor (com atributos monovalorados)
INSERT INTO public.fertilizers (id, slug, canonical_name, category_id, cas_rn, chemical_formula, description) VALUES
(1, 'ureia', 'Ureia', 1, '57-13-6', 'CO(NH2)2', 'Fertilizante nitrogenado sólido de mais alta concentração (46% N), amplamente utilizado no mundo e no Brasil.'),
(2, 'map', 'Fosfato Monoamônico (MAP)', 2, '7722-76-1', 'NH4H2PO4', 'Fertilizante fosfatado concentrado fornecendo Nitrogênio (11%) e Fósforo (52% P2O5).'),
(3, 'dap', 'Fosfato Diamônico (DAP)', 2, '7783-28-0', '(NH4)2HPO4', 'Fertilizante fosfatado de alta solubilidade contendo 18% N e 46% P2O5.'),
(4, 'cloreto-de-potassio', 'Cloreto de Potássio (KCl / MOP)', 3, '7447-40-7', 'KCl', 'Fonte potássica predominante mundialmente, garantindo 60% de K2O solúvel em água.'),
(5, 'amonia-anidra', 'Amônia Anidra', 1, '7664-41-7', 'NH3', 'Matéria-prima básica fundamental para quase todos os fertilizantes nitrogenados (82% N).'),
(6, 'nitrato-de-amonio', 'Nitrato de Amônio', 1, '6484-52-2', 'NH4NO3', 'Fertilizante nitrogenado com ação rápida e residual (33% a 34% N).'),
(7, 'sulfato-de-amonio', 'Sulfato de Amônio', 1, '7783-20-2', '(NH4)2SO4', 'Fonte sólida combinada de Nitrogênio (21% N) e Enxofre (24% S).')
ON CONFLICT (slug) DO NOTHING;

-- 13.8. 4NF: Teores Nutricionais Isolados
INSERT INTO public.fertilizer_nutrients (fertilizer_id, nutrient_code, percentage_typical, percentage_min, percentage_max, is_primary) VALUES
(1, 'N', 46.00, 45.00, 46.50, TRUE),
(2, 'N', 11.00, 10.00, 12.00, FALSE),
(2, 'P2O5', 52.00, 50.00, 54.00, TRUE),
(3, 'N', 18.00, 17.00, 19.00, FALSE),
(3, 'P2O5', 46.00, 45.00, 48.00, TRUE),
(4, 'K2O', 60.00, 58.00, 62.00, TRUE),
(5, 'N', 82.00, 81.00, 82.50, TRUE),
(6, 'N', 34.00, 33.00, 34.50, TRUE),
(7, 'N', 21.00, 20.50, 21.50, TRUE),
(7, 'S', 24.00, 23.00, 24.50, TRUE)
ON CONFLICT (fertilizer_id, nutrient_code) DO NOTHING;

-- 13.9. 4NF: Sinônimos e Nomes Comerciais Isolados
INSERT INTO public.fertilizer_synonyms (fertilizer_id, synonym_name, language_code, context) VALUES
(1, 'Ureia 46%', 'pt', 'COMMERCIAL'),
(1, 'Urea', 'en', 'SCIENTIFIC'),
(1, 'Carbamide', 'en', 'SCIENTIFIC'),
(2, 'MAP', 'pt', 'ACRONYM'),
(2, 'Monoammonium Phosphate', 'en', 'SCIENTIFIC'),
(3, 'DAP', 'pt', 'ACRONYM'),
(3, 'Diammonium Phosphate', 'en', 'SCIENTIFIC'),
(4, 'KCl', 'pt', 'CHEMICAL_FORMULA'),
(4, 'Muriate of Potash', 'en', 'COMMERCIAL'),
(4, 'MOP', 'en', 'ACRONYM'),
(4, 'Cloruro de Potasio', 'es', 'SCIENTIFIC')
ON CONFLICT (fertilizer_id, synonym_name) DO NOTHING;

-- 13.10. 4NF: Classificações Tarifárias (HS / NCM) Isoladas
INSERT INTO public.fertilizer_classifications (fertilizer_id, classification_system, classification_code, description) VALUES
(1, 'HS6', '310210', 'Ureia, mesmo em solução aquosa'),
(1, 'NCM8', '31021010', 'Ureia com teor de nitrogênio superior a 45% em peso'),
(2, 'HS6', '310540', 'Fosfato monoamônico (MAP)'),
(2, 'NCM8', '31054000', 'Fosfato monoamônico (MAP), mesmo misturado com fosfato diamônico'),
(3, 'HS6', '310530', 'Fosfato diamônico (DAP)'),
(3, 'NCM8', '31053000', 'Fosfato diamônico (DAP)'),
(4, 'HS6', '310420', 'Cloreto de potássio'),
(4, 'NCM8', '31042090', 'Outros cloretos de potássio'),
(5, 'HS6', '281410', 'Amônia anidra')
ON CONFLICT (classification_system, classification_code, fertilizer_id) DO NOTHING;

-- 13.11. Mercados e Benchmarks de Preço
INSERT INTO public.price_markets (id, code, name, hub_port_name, incoterm) VALUES
(1, 'BALTIC_UREA_FOB', 'Ureia Granulada FOB Mar Báltico', 'Portos do Báltico', 'FOB'),
(2, 'US_GULF_UREA_FOB', 'Ureia Prill/Granulada FOB Golfo dos EUA', 'NOLA (New Orleans)', 'FOB'),
(3, 'BRAZIL_UREA_CFR', 'Ureia Granulada CFR Portos Brasileiros', 'Paranaguá / Santos', 'CFR'),
(4, 'US_GULF_DAP_FOB', 'DAP FOB Golfo dos EUA', 'Tampa / NOLA', 'FOB'),
(5, 'MOROCCO_DAP_FOB', 'DAP FOB Marrocos', 'Jorf Lasfar', 'FOB'),
(6, 'VANCOUVER_POTASH_FOB', 'Cloreto de Potássio FOB Vancouver', 'Porto de Vancouver', 'FOB'),
(7, 'BRAZIL_POTASH_CFR', 'Cloreto de Potássio CFR Brasil', 'Paranaguá', 'CFR'),
(8, 'US_HENRY_HUB_GAS', 'Gás Natural Henry Hub Spot FOB', 'Henry Hub, Louisiana (EUA)', 'FOB')
ON CONFLICT (code) DO NOTHING;

-- Reset das sequences para evitar conflitos com IDs manuais do seed
SELECT setval('public.regions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.regions));
SELECT setval('public.countries_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.countries));
SELECT setval('public.data_organizations_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.data_organizations));
SELECT setval('public.data_sources_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.data_sources));
SELECT setval('public.fertilizer_categories_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.fertilizer_categories));
SELECT setval('public.fertilizers_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.fertilizers));
SELECT setval('public.price_markets_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.price_markets));
