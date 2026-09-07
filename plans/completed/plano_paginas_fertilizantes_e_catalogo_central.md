# Plano Ativo: Catálogo Central de Fertilizantes, Páginas Dedicadas e Filtros por Visualização

## 1. Objetivo
Transformar o Catálogo de Fertilizantes no hub central do FertiPartner, organizar a navegação em categorias agronômicas (Macronutrientes Primários, Secundários e Micronutrientes) e criar páginas dedicadas para cada fertilizante com todos os gráficos e mapas replicados e dotados de filtros independentes por visualização, além de filtro de tipo (produção, exportação e importação) no mapa global.

## 2. Escopo
- **Branch**: `feature/fertilizer-catalog-pages` (criada).
- **Páginas e Navegação**:
  - `dashboard.py`: Atualização do `st.navigation` com as categorias agronômicas e suas respectivas páginas.
  - `pages/`: Criação das páginas individuais de fertilizantes (`fert_ureia.py`, `fert_map.py`, etc.).
  - `v02_fertilizers_catalog.py`: Reformulação como hub central de produtos e portas de entrada diretas.
  - `v_fertilizer_detail.py`: View genérica e reutilizável que renderiza o painel completo do fertilizante selecionado.
- **Gráficos e Filtros**:
  - Página única alongada por fertilizante (sem abas), com seções sequenciais e índice/âncoras de navegação rápida na sidebar.
  - Eliminação de filtros globais de página.
  - Cada gráfico e mapa possui seus próprios seletores de ano, métrica e exibição com chaves isoladas.
  - Mapa Global com filtro de ano e tipo de fluxo (`Produção`, `Exportação`, `Importação`).
- **Páginas Inalteradas**:
  - `01_inicio.py`, `08_analises_comparativas.py` e `09_observabilidade.py` mantidas intactas conforme especificado.

## 3. Etapas de Execução
1. [x] Criação e ativação da branch `feature/fertilizer-catalog-pages`.
2. [x] Elaboração do plano detalhado e submissão para aprovação.
3. [x] Criação do serviço de dados com suporte a agregações de mapa global por tipo (Produção, Exportação, Importação).
4. [x] Implementação da view modular `v_fertilizer_detail.py` (página única alongada com navegação rápida na sidebar e filtros independentes por gráfico/mapa).
5. [x] Criação da view analítica de `v_micronutrients.py` para mapeamento de micronutrientes.
6. [x] Criação das 13 páginas individuais de fertilizantes em `src/app/presentation/streamlit/pages/`.
7. [x] Reestruturação da view `v02_fertilizers_catalog.py` como hub central com categorias agronômicas e links diretos.
8. [x] Atualização da árvore de navegação em `src/app/presentation/streamlit/dashboard.py`.
9. [x] Atualização e expansão dos testes unitários em `tests/unit/test_frontend_pages.py` e `tests/unit/test_frontend_services.py`.
10. [x] Execução da suíte completa de 138 testes unitários aprovados (`uv run pytest tests/unit`).

