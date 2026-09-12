-- ==============================================================================
-- FertiPartner: Migração 20260911_000001_add_extra_sources_and_indicators.sql
-- Descrição: Adiciona fontes World Bank Indicators e FAOSTAT Preços,
--             novo mercado de preço para Gás Natural e tabela country_indicators (4NF).
-- ==============================================================================

-- 1. NOVAS FONTES DE DADOS
INSERT INTO public.data_sources (id, organization_id, code, name, api_docs_url, base_url, update_frequency) VALUES
(8, 5, 'WB_INDICATORS', 'World Bank World Development Indicators', 'https://datahelpdesk.worldbank.org/knowledgebase/articles/888548-world-bank-apis', 'https://api.worldbank.org/v2', 'ANNUAL'),
(9, 1, 'FAOSTAT_PP', 'FAOSTAT Producer Prices / Prices Paid', 'https://www.fao.org/faostat/en/docs/redoc-static.html', 'https://faostatservices.fao.org/api/v1/en/data/PP', 'ANNUAL')
ON CONFLICT (code) DO NOTHING;

-- 2. NOVO MERCADO DE PREÇO / BENCHMARK (Gás Natural - Feedstock crítico de fertilizantes nitrogenados)
INSERT INTO public.price_markets (id, code, name, hub_port_name, incoterm) VALUES
(8, 'US_HENRY_HUB_GAS', 'Gás Natural Henry Hub Spot FOB', 'Henry Hub, Louisiana (EUA)', 'FOB')
ON CONFLICT (code) DO NOTHING;

-- 3. TABELA DE FATOS MACROECONÔMICOS POR PAÍS (4NF)
-- Suporta indicadores contínuos por hectare (kg/ha) e percentuais macroeconômicos
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

COMMENT ON TABLE public.country_indicators IS 'Fatos e indicadores macroeconômicos e de intensidade agronômica por país e ano (ex.: kg de adubo/ha).';
COMMENT ON COLUMN public.country_indicators.indicator_code IS 'Código internacional do indicador (ex: AG.CON.FERT.ZS para kg/ha no World Bank).';

CREATE INDEX IF NOT EXISTS idx_country_indicators_lookup
ON public.country_indicators (country_id, indicator_code, year);

-- Habilita RLS
ALTER TABLE public.country_indicators ENABLE ROW LEVEL SECURITY;

-- Política de leitura pública
CREATE POLICY "Permitir leitura publica de country_indicators"
ON public.country_indicators FOR SELECT
TO public
USING (true);

-- Permissão para roles padrão
GRANT SELECT ON public.country_indicators TO anon, authenticated, service_role;
GRANT ALL ON public.country_indicators TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.country_indicators_id_seq TO service_role;
