# FertiPartner

Plataforma de inteligência de mercado, análise de dados e suporte cognitivo para a cadeia produtiva e comercial de fertilizantes agrícolas (Macronutrientes Primários N-P-K, Secundários e Micronutrientes), desenvolvida para atender produtores agrícolas, distribuidores de insumos, tradings e consultorias do agronegócio.

O sistema ingere dados complexos de comércio exterior, produção industrial, consumo agrícola, cotações internacionais e notícias setoriais de fontes governamentais e multilaterais, processa-os através de uma arquitetura resiliente e normalizada em **Quarta Forma Normal (4NF)** no Supabase (PostgreSQL), disponibilizando visões analíticas de alta performance e um assistente especialista com inteligência artificial (**FertiPartner.AI**) baseado no Google Gemini 3.x com Function Calling e GuardRails de segurança.

---

## Proposta de Valor e Perspectivas

### 1. Perspectiva de Negócio & Agronegócio
O Brasil é o quarto maior consumidor global de fertilizantes e importa aproximadamente **85%** de sua demanda anual. O FertiPartner resolve a assimetria de informação no setor através de:
- **Mitigação de Riscos de Suprimento:** Mapeamento antecipado de origens, dependência de grandes polos exportadores (Rússia, Canadá, China, Marrocos) e estoques de passagem.
- **Previsibilidade e Paridade de Troca (Barter):** Acompanhamento da relação histórica de preços entre adubos (Ureia, MAP, KCl) e sacas de grãos (soja e milho) para identificar janelas oportunas de compra para safra e safrinha.
- **Logística Portuária e Distribuição Regional:** Monitoramento de fluxos de importação nos portos brasileiros (Paranaguá, Santos, Itaqui, Rio Grande) e consumo por estado (Mato Grosso, Paraná, Rio Grande do Sul, Goiás, etc.).
- **Catálogo Técnico Agronômico:** Fichas completas com garantias nutricionais, limites de higroscopicidade (PCUR), sinônimos fiscais (NCM/CAS) e compatibilidade em misturas.

### 2. Perspectiva de Engenharia & Solução de Software
- **Clean Architecture & Domain-Driven Design (DDD):** Isolamento total das regras de negócio em relação a frameworks de interface, clientes HTTP e drivers de banco.
- **Modelagem Relacional em Quarta Forma Normal (4NF):** Eliminação de dependências multivaloradas e anomalias de atualização, com separação de tabelas de fatos atômicos e dimensões.
- **Idempotência Criptográfica (SHA-256):** Cada lote de dados coletado possui cálculo de `payload_hash`, impedindo inserções duplicadas e assegurando auditabilidade contínua.
- **Segurança Nativa via Row Level Security (RLS):** Permissões restritas de leitura pública e escrita restrita a tokens de serviço autenticados.
- **FertiPartner.AI com GuardRails:** RAG quantitativo determinístico acoplado a Function Calling que elimina alucinações numéricas, operando com baixa latência (`thinkingLevel: LOW`), suporte a `thoughtSignature` e blindagem pré-inferência contra Prompt Injections e desvios de escopo.
- **Desenvolvimento Orientado a Testes (TDD):** Mais de 165 testes unitários automatizados cobrindo entidades de domínio, orquestração de IA, clientes de rede e integridade de páginas.

---

## Funcionalidades da Plataforma

### 1. Catálogo Estruturado de Fertilizantes (13 Painéis Dedicados)
Páginas analíticas completas organizadas em submenus na barra lateral:
- **Macronutrientes Primários — Nitrogenados (N):** Ureia, Amônia Anidra, Nitrato de Amônio e Sulfato de Amônio.
- **Macronutrientes Primários — Fosfatados (P):** Fosfato Monoamônico (MAP), Fosfato Diamônico (DAP), Superfosfato Simples (SSP), Superfosfato Triplo (TSP) e Rocha Fosfática.
- **Macronutrientes Primários — Potássicos (K):** Cloreto de Potássio (KCl) e Sulfato de Potássio (SOP).
- **Macronutrientes Secundários:** Enxofre Elementar Pastilhado.
- **Micronutrientes:** Painel estratégico de Zinco (Zn), Boro (B), Cobre (Cu), Manganês (Mn), Molibdênio (Mo) e Cobalto (Co).

Cada painel dedicado conta com:
- Mapa mundi coroplético interativo com alternância entre Produção, Exportação e Importação.
- Diagrama de Fluxos Bilaterais Sankey (Top 10 rotas globais ponderadas por volume ou valor).
- Séries históricas de cotações internacionais com médias móveis trimestrais (3M).
- Balanço físico nacional (Produção Interna vs. Importações) e taxa de dependência externa (%).
- Ficha técnica agronômica, propiedades físico-químicas e cuidados de PCUR/armazenagem.

### 2. Módulo de Inteligência de Mercado
- **Análises & Comparações:**
  - Comparador dinâmico de preços nominais e indexados em Base 100.
  - Calculadora de paridades e ratios livres (ex.: DAP/Ureia, KCl/Ureia) com bandas estatísticas de Bollinger ($\pm 1\sigma$).
  - Indicador Herfindahl-Hirschman (HHI) de concentração e risco geopolítico da oferta global.
  - Demanda regional e entregas por Unidade Federativa brasileira.
  - Matriz estatística multidimensional de correlação linear de Pearson e volatilidade anualizada (CV %).
- **Radar de Notícias NPK (Últimos 7 Dias):**
  - Captura contínua via Google News RSS com corte temporal estrito de 168 horas (7 dias).
  - Barômetros semicirculares em Plotly para os 5 tópicos estratégicos: Frete & Logística, Produção Industrial, Consumo & Demanda, Preços & Mercado e Geopolítica.
  - Diagnóstico automatizado em 3 estados (*Melhorando*, *Estável*, *Piorando*) e pontuação quantitativa líquida de -10 a +10 pontos.
- **FertiPartner.AI:**
  - Assistente conversacional especialista em nutrição vegetal e macroeconomia agrícola.
  - Integração com a família de modelos **Google Gemini 3.x Flash** (`gemini-3.6-flash`, `gemini-3.8-flash`).
  - Execução de 6 ferramentas analíticas conectadas ao banco de dados relacional.
  - **AIGuardrails:** Blindagem determinística contra Prompt Injections, tentativas de Jailbreak ("DAN", override de regras), exfiltração de system prompt e contenção estrita de escopo ao agronegócio.

### 3. Módulo de Infraestrutura & Governança
- **Observabilidade:** Monitoramento do status operacional das fontes de dados (MDIC, Comtrade, FAOSTAT, FRED, Google News RSS), logs de rotinas de ingestão (`data_collection_runs`), matriz de consistência temporal e SLAs.
- **Software:** Documentação interativa detalhando a Clean Architecture, modelagem 4NF, esteira de TDD e especificações de IA.
- **Documentação (README):** Renderização direta deste arquivo no Streamlit para consulta rápida em tempo de execução.

---

## Arquitetura do Software

O projeto segue estritamente a **Clean Architecture**:

```text
FertiPartner/
├── docs/                      # Documentação de arquitetura, ADRs e requisitos
├── infrastructure/            # Configurações de infraestrutura e migrações SQL
│   └── supabase/              # Schema 4NF, tabelas de fatos, views e políticas RLS
├── scripts/                   # Utilitários CLI de ingestão, tokens e manutenção
├── src/
│   ├── main.py                # Ponto de entrada da aplicação
│   └── app/
│       ├── domain/            # Regras de negócio puras (sem dependências externas)
│       │   ├── entities/      # Entidades agronômicas e de mercado
│       │   └── ai/            # Entidades de chat, tools schema, prompts e AIGuardrails
│       ├── application/       # Casos de uso e orquestração
│       │   ├── use_cases/     # Briefing executivo, diagnósticos de produtos
│       │   │   └── ai/        # CopilotOrchestrator e ToolExecutor
│       ├── infrastructure/    # Adaptadores externos, APIs e banco de dados
│       │   ├── ai/            # Cliente Google Gemini 3.x com thoughtSignature e retentativa
│       │   ├── collectors/    # Coletores para MDIC, UN Comtrade, FAOSTAT e FRED
│       │   ├── http/          # Cliente HTTP resiliente com retentativas exponenciais e jitter
│       │   └── supabase/      # Repositórios PostgREST e mapeamento 4NF
│       └── presentation/      # Interface gráfica e serviços da UI
│           └── streamlit/     # Dashboard, páginas (pages/), views (views/) e estilos (styles.py)
└── tests/
    ├── conftest.py            # Fixtures globais do pytest
    └── unit/                  # Suíte de mais de 165 testes unitários rápidos e isolados
```

### Regras de Dependência:
- `Domain` não depende de nenhuma camada externa.
- `Application` depende exclusivamente de `Domain` e abstrações de infraestrutura.
- `Infrastructure` implementa os contratos e serviços externos.
- `Presentation` consome `Application` e expõe a experiência analítica.

---

## Primeiros Passos

### Pré-requisitos
- **Python 3.13+**
- **uv** (gerenciador de dependências e ambientes virtuais ultrarrápido da Astral)

### Instalação
1. Clone o repositório:
   ```bash
   git clone https://github.com/MathZiero/FertiPartner.git
   cd FertiPartner
   ```

2. Crie o ambiente virtual e sincronize as dependências:
   ```bash
   uv sync
   ```

### Configuração de Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com as suas credenciais:

```dotenv
# Supabase / PostgreSQL (4NF Data Layer)
SUPABASE_URL="https://seu-projeto.supabase.co"
SUPABASE_KEY="sua-chave-anon-publica"
SUPABASE_SERVICE_ROLE_KEY="sua-chave-service-role-admin"

# Google Gemini API (FertiPartner.AI)
# Obtenha gratuitamente em: https://aistudio.google.com/app/apikey
GEMINI_API_KEY="AIzaSy..."

# APIs Externas (Ingestão)
FRED_API_KEY="sua-chave-api-fred"
COMTRADE_API_KEY="sua-chave-api-un-comtrade"

# FAOSTAT (Opcional - para renovação automática de token)
FAOSTAT_USERNAME="seu-usuario-fao"
FAOSTAT_PASSWORD="sua-senha-fao"
FAOSTAT_TOKEN="seu-jwt-token"
```

---

## Execução

### 1. Iniciar o Painel Streamlit
```bash
# Execução direta via uv:
uv run streamlit run src/app/presentation/streamlit/dashboard.py

# Ou via script auxiliar:
uv run python scripts/run_dashboard.py
```
Acesse no navegador: `http://localhost:8501`.

### 2. Ingestão de Dados (Pipelines)
```bash
# Executar todos os coletores de dados:
uv run python scripts/populate_database.py --all

# Ou executar coletores específicos:
uv run python scripts/populate_database.py --source comex
uv run python scripts/populate_database.py --source comtrade
uv run python scripts/populate_database.py --source faostat
uv run python scripts/populate_database.py --source fred
```

### 3. Migrações e Verificação de Integridade 4NF
```bash
uv run python scripts/apply_supabase_migrations.py --check
```

---

## Testes Automatizados (TDD)

A suíte de testes unitários conta com **165+ testes automatizados**, executados sem dependência de rede externa ou credenciais ativas:

```bash
# Executar toda a suíte de testes unitários:
uv run pytest tests/unit

# Executar testes com relatório detalhado:
uv run pytest tests/unit -v
```

---

## Licença e Diretrizes
Este projeto adota padrões estritos de governança:
- Branches de desenvolvimento específicas (ex.: `feature/...`).
- Proibição de emojis em textos e relatórios institucionais para manutenção de tom corporativo.
- Conformidade integral com as diretrizes do `AGENTS.md`.