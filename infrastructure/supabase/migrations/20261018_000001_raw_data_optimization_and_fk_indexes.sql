-- ==============================================================================
-- Migration: 20261018_000001_raw_data_optimization_and_fk_indexes.sql
-- Description: Otimização de armazenamento e integridade referencial na raw_data.
-- 1. Remove o índice GIN de raw_payload (que causava inchaço desnecessário de 100MB+).
-- 2. Adiciona índices nas colunas raw_data_id das tabelas filhas para prevenir
--    varreduras completas (sequential scans) e timeouts em manutenções.
-- ==============================================================================

-- 1. Remover índice GIN redundante
DROP INDEX IF EXISTS public.idx_raw_data_payload_gin;

-- 2. Índices de chave estrangeira nas tabelas que referenciam raw_data(id)
CREATE INDEX IF NOT EXISTS idx_fk_trade_raw_data ON public.trade_records(raw_data_id);
CREATE INDEX IF NOT EXISTS idx_fk_prod_raw_data ON public.production_records(raw_data_id);
CREATE INDEX IF NOT EXISTS idx_fk_price_raw_data ON public.price_records(raw_data_id);
CREATE INDEX IF NOT EXISTS idx_fk_consump_raw_data ON public.consumption_records(raw_data_id);
CREATE INDEX IF NOT EXISTS idx_fk_ci_raw_data ON public.country_indicators(raw_data_id);
