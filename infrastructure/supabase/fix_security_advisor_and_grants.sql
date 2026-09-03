-- ==============================================================================
-- FertiPartner: Correção dos Alertas do Supabase Security Advisor & Concessão de Privilégios
-- Arquivo: fix_security_advisor_and_grants.sql
--
-- Execute este script no Supabase Dashboard -> SQL Editor
-- para resolver 100% dos avisos e liberar o acesso às tabelas.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. CORREÇÃO: Function Search Path Mutable (public.set_updated_at)
-- Define search_path explícito para prevenir ataques de injeção de search_path
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 2. CORREÇÃO: Public / Signed-In Can Execute SECURITY DEFINER (public.rls_auto_enable)
-- Revoga permissão de execução anônima/pública da RPC rls_auto_enable()
-- ------------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'rls_auto_enable'
    ) THEN
        REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
        GRANT EXECUTE ON FUNCTION public.rls_auto_enable() TO service_role, postgres;
    END IF;
END;
$$;

-- ------------------------------------------------------------------------------
-- 3. CORREÇÃO: Security Definer View em todas as 5 Views Analíticas
-- Recria as views com WITH (security_invoker = true) para respeitar as políticas RLS do usuário que consulta
-- ------------------------------------------------------------------------------

-- 3.1. v_fertilizer_profiles
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

-- 3.2. v_global_production_rankings
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

-- 3.3. v_bilateral_trade_flows
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

-- 3.4. v_brazil_external_dependency
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
)
SELECT 
    f.id AS fertilizer_id,
    f.canonical_name AS fertilizer_name,
    COALESCE(i.ref_year, p.ref_year, e.ref_year) AS ref_year,
    COALESCE(p.prod_mt, 0) AS national_production_mt,
    COALESCE(i.import_mt, 0) AS total_imports_mt,
    COALESCE(e.export_mt, 0) AS total_exports_mt,
    (COALESCE(p.prod_mt, 0) + COALESCE(i.import_mt, 0) - COALESCE(e.export_mt, 0)) AS apparent_consumption_mt,
    ROUND(
        (COALESCE(i.import_mt, 0) / 
        NULLIF(COALESCE(p.prod_mt, 0) + COALESCE(i.import_mt, 0) - COALESCE(e.export_mt, 0), 0)) * 100, 
        2
    ) AS external_dependency_pct
FROM public.fertilizers f
LEFT JOIN br_imports i ON f.id = i.fertilizer_id
LEFT JOIN br_exports e ON f.id = e.fertilizer_id AND i.ref_year = e.ref_year
LEFT JOIN br_prod p ON f.id = p.fertilizer_id AND COALESCE(i.ref_year, e.ref_year) = p.ref_year
WHERE COALESCE(i.ref_year, p.ref_year, e.ref_year) IS NOT NULL;

-- 3.5. v_price_benchmark_trends
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

-- ------------------------------------------------------------------------------
-- 4. CONCESSÃO DE PRIVILÉGIOS BÁSICOS ÀS ROLES DO SUPABASE (anon, authenticated, service_role)
-- ------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO anon, authenticated, service_role;
