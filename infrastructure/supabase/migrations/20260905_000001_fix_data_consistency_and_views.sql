-- ==============================================================================
-- Migração: 20260905_000001_fix_data_consistency_and_views.sql
-- Descrição: Solução sistêmica contra assimetria temporal e valores nulos espúrios
--             em indicadores de comércio, produção e dependência externa.
-- ==============================================================================

-- 1. Recriação da View v_brazil_external_dependency com tratamento estrito de NULLs
--    Evita que ausência de censo de produção gere falsos "0 MT de produção" e falsos "100% de dependência".
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

COMMENT ON VIEW public.v_brazil_external_dependency IS 
'Indicador oficial da taxa de dependência externa do Brasil com proteção sistêmica contra defasagem temporal (retorna NULL para dependência e consumo quando o censo de produção ainda não foi consolidado).';

-- 2. View de Matriz de Consistência e Sincronismo Temporal do Banco de Dados
CREATE OR REPLACE VIEW public.v_data_consistency_matrix
WITH (security_invoker = true) AS
WITH active_years AS (
    SELECT DISTINCT EXTRACT(YEAR FROM period_start_date)::INT AS ref_year FROM public.trade_records
    UNION
    SELECT DISTINCT EXTRACT(YEAR FROM period_start_date)::INT AS ref_year FROM public.production_records
    UNION
    SELECT DISTINCT EXTRACT(YEAR FROM price_date)::INT AS ref_year FROM public.price_records
),
year_fert AS (
    SELECT f.id AS fertilizer_id, f.canonical_name, y.ref_year
    FROM public.fertilizers f
    CROSS JOIN active_years y
),
trade_summary AS (
    SELECT 
        fertilizer_id, 
        EXTRACT(YEAR FROM period_start_date)::INT AS ref_year,
        COUNT(*) AS trade_records_count,
        SUM(standard_quantity_mt) AS total_traded_mt
    FROM public.trade_records
    GROUP BY fertilizer_id, EXTRACT(YEAR FROM period_start_date)::INT
),
prod_summary AS (
    SELECT 
        fertilizer_id, 
        EXTRACT(YEAR FROM period_start_date)::INT AS ref_year,
        COUNT(*) AS prod_records_count,
        COUNT(DISTINCT country_id) AS producing_countries_count,
        SUM(standard_quantity_mt) AS total_produced_mt
    FROM public.production_records
    GROUP BY fertilizer_id, EXTRACT(YEAR FROM period_start_date)::INT
),
price_summary AS (
    SELECT 
        fertilizer_id, 
        EXTRACT(YEAR FROM price_date)::INT AS ref_year,
        COUNT(*) AS price_points_count
    FROM public.price_records
    GROUP BY fertilizer_id, EXTRACT(YEAR FROM price_date)::INT
)
SELECT 
    yf.ref_year,
    yf.fertilizer_id,
    yf.canonical_name AS fertilizer_name,
    COALESCE(t.trade_records_count, 0) AS trade_records_count,
    COALESCE(p.prod_records_count, 0) AS prod_records_count,
    COALESCE(p.producing_countries_count, 0) AS producing_countries_count,
    COALESCE(pr.price_points_count, 0) AS price_points_count,
    CASE 
        WHEN COALESCE(t.trade_records_count, 0) > 0 AND COALESCE(p.prod_records_count, 0) > 0 AND COALESCE(pr.price_points_count, 0) > 0 
            THEN 'FULLY_SYNCHRONIZED'
        WHEN COALESCE(t.trade_records_count, 0) > 0 AND COALESCE(p.prod_records_count, 0) = 0 
            THEN 'AWAITING_PRODUCTION_SURVEY'
        WHEN COALESCE(t.trade_records_count, 0) = 0 AND COALESCE(p.prod_records_count, 0) > 0 
            THEN 'AWAITING_TRADE_DATA'
        ELSE 'PARTIAL_DATA'
    END AS synchronization_status
FROM year_fert yf
LEFT JOIN trade_summary t ON yf.fertilizer_id = t.fertilizer_id AND yf.ref_year = t.ref_year
LEFT JOIN prod_summary p ON yf.fertilizer_id = p.fertilizer_id AND yf.ref_year = p.ref_year
LEFT JOIN price_summary pr ON yf.fertilizer_id = pr.fertilizer_id AND yf.ref_year = pr.ref_year
WHERE COALESCE(t.trade_records_count, 0) + COALESCE(p.prod_records_count, 0) + COALESCE(pr.price_points_count, 0) > 0;

COMMENT ON VIEW public.v_data_consistency_matrix IS 
'Matriz de observabilidade analítica de integridade temporal: mapeia assimetrias entre dados aduaneiros (ComexStat/Comtrade) e estatísticas de produção (FAOSTAT/IFA).';

-- Concessão de permissões para anon e authenticated
GRANT SELECT ON public.v_brazil_external_dependency TO anon, authenticated;
GRANT SELECT ON public.v_data_consistency_matrix TO anon, authenticated;
