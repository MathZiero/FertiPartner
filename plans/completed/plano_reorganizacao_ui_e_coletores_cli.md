# Plano de Trabalho Concluído: Reorganização de Menu, Cards de Catálogo, Estilo de Mapa e Scripts CLI

## Objetivo
Atender aos 5 requisitos solicitados pelo usuário para o FertiPartner:
1. Dividir a categoria "Preços e Inteligência" em duas: "Preços" e "Inteligência".
2. Mudar a disposição do Catálogo de Fertilizantes para horizontal em formato de cards (Nome, Descrição, Garantia Nutricional e Botão Ficha Técnica), eliminando abas e exibindo as 3 categorias na mesma página separadas por `st.divider()`.
3. Adicionar contornos em preto nos países e no globo no Mapa Global de Produção, com uma cor suave de fundo para países sem produção.
4. Mover a página "Produção Global" para a categoria de comércio, renomeando-a para "Oferta e Demanda".
5. Desenvolver scripts CLI parametrizados (especialmente por ano) para todas as outras fontes de dados da aplicação (`collect_brazil_comex.py`, `collect_faostat_production.py`, `collect_benchmark_prices.py`, `populate_fertilizer_catalog.py`), no mesmo padrão com `Usage:` de `collect_top_trade_flows.py`.

## Escopo e Arquitetura
- **presentation**:
  - `src/app/presentation/streamlit/dashboard.py` (menu de navegação)
  - `src/app/presentation/streamlit/views/v02_fertilizers_catalog.py` (layout de cards)
  - `src/app/presentation/streamlit/views/v03_global_production.py` (estilização de mapa choropleth)
- **domain**:
  - `src/domain/fertilizers.py` (catálogo mestre de entidades isolado de presentation)
- **scripts**:
  - `scripts/collect_brazil_comex.py`
  - `scripts/collect_faostat_production.py`
  - `scripts/collect_benchmark_prices.py`
  - `scripts/populate_fertilizer_catalog.py`
- **tests**:
  - `tests/unit/scripts/test_cli_scripts.py`
  - `tests/unit/test_frontend_pages.py`

## Etapas Concluídas
1. [x] Análise do repositório, execução da suíte de testes (95 testes passando) e elaboração do plano de implementação.
2. [x] Validação do plano com o usuário e aprovação.
3. [x] Implementação da reorganização das categorias e menu em `dashboard.py`.
4. [x] Implementação dos cards horizontais e remoção de abas em `v02_fertilizers_catalog.py`.
5. [x] Correção e aprimoramento da estilização do mapa mundi em `v03_global_production.py`.
6. [x] Criação dos novos scripts CLI em `scripts/` com headers explicativos de `Usage`.
7. [x] Criação de testes unitários para os scripts CLI e páginas em `tests/`.
8. [x] Execução da suíte completa de testes (`pytest`, 112 testes passando) e verificação manual dos comandos CLI.
9. [x] Registro no walkthrough e finalização.
