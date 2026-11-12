-- ==============================================================================
-- Migration: 20261111_000001_raw_data_permanent_dedup_and_compaction.sql
-- Description: Solução permanente para controle de armazenamento em public.raw_data.
-- 1. Consolida registros duplicados por (source_id, endpoint_url) apontando FKs
--    das tabelas de fatos para o ID mais recente de cada endpoint.
-- 2. Remove todos os registros órfãos em public.raw_data (não referenciados por
--    nenhuma tabela de fatos 4NF).
-- 3. Cria índice composto (source_id, endpoint_url) para acelerar o upsert in-place
--    do BaseCollector.store_raw_payload().
-- ==============================================================================

-- 1. Índice composto para busca e atualização in-place por (source_id, endpoint_url)
CREATE INDEX IF NOT EXISTS idx_raw_data_source_endpoint ON public.raw_data(source_id, endpoint_url);

-- 2. Remoção de registros órfãos em raw_data (sem referência em tabelas de fatos)
DELETE FROM public.raw_data r
WHERE NOT EXISTS (SELECT 1 FROM public.trade_records t WHERE t.raw_data_id = r.id)
  AND NOT EXISTS (SELECT 1 FROM public.production_records p WHERE p.raw_data_id = r.id)
  AND NOT EXISTS (SELECT 1 FROM public.price_records pr WHERE pr.raw_data_id = r.id)
  AND NOT EXISTS (SELECT 1 FROM public.consumption_records c WHERE c.raw_data_id = r.id)
  AND NOT EXISTS (SELECT 1 FROM public.country_indicators ci WHERE ci.raw_data_id = r.id);

