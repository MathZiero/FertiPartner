# Plano Concluído: Redesign do Front-End, Modo Claro (Light Mode) e Refinamentos de UX

## 1. Objetivo
Atender às 11 solicitações de melhorias de interface, experiência do usuário e design system feitas pelo usuário, migrando a aplicação para Modo Claro moderno (AgTech), eliminando referências a detalhes de especificação técnica/arquitetura (RFs, 4NF), reestruturando a barra lateral, redesenhando a página de Visão Geral e o Catálogo de Fertilizantes, centralizando títulos, corrigindo eixos do Plotly e unificando a página de Observabilidade.

---

## 2. Escopo das Modificações

### Item 1 & 5: Barra Lateral (Sidebar)
- Inserir o logotipo profissional do FertiPartner no topo absoluto da sidebar usando `st.logo()`, acima de qualquer menu ou navegação.
- Remover o indicador de status de conexão com o Supabase da barra lateral (permanecendo exclusivamente na página de Observabilidade).
- Manter rodapé limpo e elegante.

### Item 2: Remoção de Referências Técnicas (RFs, 4NF, etc.)
- Varrer e substituir em todas as páginas, componentes e views qualquer menção a "RF01".."RF24", "4NF", "Quarta Forma Normal", "FN4" por termos profissionais voltados ao negócio ("Catálogo Oficial", "Padrão Homologado", "Balanço Nacional", etc.).

### Item 3 & 4: Observabilidade & Infraestrutura no Rodapé
- Posicionar a seção `"⚙️ Infraestrutura"` no final da navegação na sidebar.
- Renomear a página de auditoria para `"Observabilidade"` (`09_observabilidade.py`).
- Criar na página de Observabilidade uma aba unificada ("📡 Fontes de Dados & Ingestão Integrada") com uma tabela dedicada para cada fonte de dados (MDIC Comex Stat, UN Comtrade, FAOSTAT, FRED / Banco Mundial), contendo:
  - Dados requisitados daquela fonte
  - Última data em que foi requisitado
  - Volume de registros e status
  - Latência média e periodicidade oficial

### Item 6: Centralização de Títulos
- Centralizar todos os títulos de páginas no componente `render_header()` e via regras CSS globais para `h1`, `.fp-header-title`, `.fp-header-subtitle`.

### Item 7: Remoção de Botões de Exportação
- Remover todas as chamadas e renderizações de botões de download CSV (`render_download_csv_button`) em todas as páginas da aplicação.

### Item 8: Correção de Eixos do Plotly ("undefined")
- Revisar todos os gráficos Plotly garantindo títulos explícitos em português ("Volume (Milhões de MT)", "Preço (USD / t)", "Fertilizante", "Data", etc.).
- Corrigir a renderização do Plotly.js forçando `title=dict(text="")` e `legend=dict(title=dict(text=""))` para eliminar completamente a palavra `undefined` desenhada no SVG/canvas.

### Item 9: Redesenho Completo da "Visão Geral"
- Reformular a página `01_visao_geral.py`:
  - 4 Cards executivos em destaque: Consumo Aparente Nacional, Dependência Externa de Importação, Volume Total Importado, Preço Médio Internacional de Referência.
  - Gráfico de barras agrupadas claro de Balanço Nacional (Produção Nacional vs. Importações) com eixos em português.
  - Gráfico em rosca dos principais países de origem das importações brasileiras.
  - Painel de Inteligência e Dinâmica de Mercado NPK no agronegócio nacional.

### Item 10: Redesenho do Catálogo de Fertilizantes
- Reformular `02_catalogo.py`:
  - Remover a opção "Todas" do seletor de categorias.
  - Remover a barra de seleção de produto individual.
  - Apresentar uma listagem elegante em cards estruturados com todos os produtos da categoria selecionada, exibindo fórmula, CAS, garantias nutricionais, códigos NCM/HS, sinônimos e botão para ficha técnica completa.

### Item 11: Modo Claro (Light Mode) & Paleta AgTech Moderna
- `.streamlit/config.toml`: `base = "light"`, `primaryColor = "#2D6A4F"`, `backgroundColor = "#F8FAF9"`, `secondaryBackgroundColor = "#EDF3EF"`, `textColor = "#1F2937"`.
- `styles.py`: Reescrita completa do CSS para tema claro com cartões brancos (`#FFFFFF`), sombras sutis, bordas suaves (`#E5E7EB`), tipografia refinada e acentos em tons verdes agrícolas modernos (`#2D6A4F`, `#40916C`).
- `theme.py`: Configurar template Plotly para `plotly_white`, ajustando eixos, fontes e hover para legibilidade perfeita no fundo claro.

---

## 3. Etapas de Execução
- [x] Atualizar `.streamlit/config.toml`, `styles.py` e `theme.py` para Modo Claro AgTech Moderno.
- [x] Atualizar `components/ui.py` (centralização de títulos, badges em modo claro, remoção de referências técnicas).
- [x] Atualizar `dashboard.py` (logo no topo da sidebar com `st.logo()`, remoção do status Supabase da sidebar, reposicionamento da Infraestrutura com página Observabilidade).
- [x] Criar `09_observabilidade.py` com a aba unificada e tabelas dedicadas por provedor.
- [x] Redesenhar `01_visao_geral.py` (narrativa executiva, KPIs claros, gráficos com eixos corretos e sem botão de exportação).
- [x] Redesenhar `02_catalogo.py` (remover 'Todas', remover selectbox, listar produtos da categoria em cards estruturados, sem botão de exportação).
- [x] Atualizar páginas 03, 04, 05, 06, 07, 08 (remover botões de exportação, remover referências a RF/4NF, preencher títulos dos eixos Plotly).
- [x] Executar suíte de testes unitários (`pytest -m "not integration"`) e garantir 100% de aprovação (81 de 81 testes aprovados).
- [x] Validação visual interativa no navegador via `browser_subagent` com captura de screenshots confirmando Modo Claro, layout e ausência de bugs.
- [x] Registrar conclusão em `plans/completed/` e atualizar `walkthrough.md`.
