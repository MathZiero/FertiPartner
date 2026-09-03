# FertiPartner

Plataforma de inteligência de mercado e análise de dados para a cadeia produtiva e comercial de fertilizantes (Nitrogenados, Fosfatados e Potássicos — NPK), desenvolvida para atender produtores agrícolas, distribuidores e tradings.

O sistema ingere dados complexos de comércio exterior, produção, consumo e índices econômicos de fontes internacionais e nacionais, processa-os através de uma arquitetura resiliente e normalizada em 4ª Forma Normal (4NF) no Supabase (PostgreSQL), disponibilizando visões analíticas de alta performance.

---

## Principais Funcionalidades

- **Ingestão Multi-Fonte Resiliente**:
  - **MDIC Comex Stat**: Microdados mensais detalhados de importações e exportações brasileiras (por NCM, país de origem e UF de destino).
  - **UN Comtrade**: Fluxos de comércio bilateral global entre os principais players mundiais (por códigos SH/HS).
  - **FRED (Federal Reserve)**: Séries históricas de preços internacionais de commodities e índices de preços ao produtor (PPI).
  - **FAOSTAT (FAO)**: Dados anuais globais de produção, consumo agrícola e balanço de nutrientes.
- **Arquitetura de Dados em Quarta Forma Normal (4NF)**:
  - Eliminação de dependências multivaloradas e redundâncias.
  - Separação estrita de tabelas de fatos (`trade_records`, `production_records`, `consumption_records`, `price_records`, `brazil_trade_details`).
  - Armazenamento imutável de payloads brutos em `raw_data` com hash SHA-256 para auditoria completa e garantia de idempotência (RNF02).
  - Políticas de segurança ativas via **Row Level Security (RLS)** no PostgreSQL.
- **Cliente HTTP Resiliente**:
  - Controle de taxa (*rate limiting*) dedicado por provedor.
  - Retentativas com *exponential backoff* e *jitter* para evitar estrangulamento de requisições e tratar limites de cota (HTTP 429).
- **Visões Analíticas Otimizadas**:
  - Views SQL consolidadas (ex.: `v_fertilizer_profiles`) para consultas rápidas de inteligência de mercado.

---

## Arquitetura do Projeto

O FertiPartner segue os princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**:

```text
FertiPartner/
├── docs/                      # Documentação de arquitetura, decisões (ADRs) e regras
│   ├── architecture/          # Modelagem de dados 4NF, arquitetura e boas práticas de APIs
│   │   └── decisions/         # Architecture Decision Records (ADRs)
│   ├── engineering/           # Convenções de código, estratégia de testes e DoD
│   └── product/               # Requisitos funcionais/não-funcionais e visão de produto
├── infrastructure/            # Configurações de infraestrutura e migrações
│   └── supabase/              # Scripts SQL (schema 4NF, migrations, grants de segurança)
├── scripts/                   # Utilitários CLI (ingestão, migrações, gerador de tokens)
├── src/
│   ├── main.py                # Ponto de entrada da aplicação
│   └── app/
│       ├── domain/            # Entidades de negócio e interfaces puras
│       ├── application/       # Casos de uso e orquestração
│       ├── infrastructure/    # Adaptadores de banco (Supabase), HTTP e coletores de dados
│       │   ├── collectors/    # Coletores para Comex Stat, Comtrade, FAOSTAT e FRED
│       │   ├── faostat/       # Autenticação JWT e gerenciador de sessão da FAO
│       │   ├── http/          # Cliente HTTP resiliente com retentativas e rate limit
│       │   └── supabase/      # Repositórios, gerenciador de conexão e mapeamento 4NF
│       └── presentation/      # Interfaces de usuário, rotas de API e CLI
└── tests/
    ├── conftest.py            # Fixtures globais do pytest
    ├── unit/                  # Testes unitários rápidos e isolados (com mocks)
    └── integration/           # Testes de integração ao vivo (Supabase e APIs externas)
```

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

2. Instale as dependências do projeto e configure o ambiente com `uv`:
   ```bash
   uv sync
   ```

### Configuração de Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto baseado nas suas credenciais:

```dotenv
# Supabase
SUPABASE_URL="https://seu-projeto.supabase.co"
SUPABASE_KEY="sua-chave-anon-publica"
SUPABASE_SERVICE_ROLE_KEY="sua-chave-service-role-admin"

# APIs Externas
FRED_API_KEY="sua-chave-api-fred"
COMTRADE_API_KEY="sua-chave-api-un-comtrade"

# FAOSTAT (Opcional - para autenticação e renovação automática)
FAOSTAT_USERNAME="seu-usuario-fao"
FAOSTAT_PASSWORD="sua-senha-fao"
FAOSTAT_TOKEN="seu-jwt-token"
```

---

## Scripts e Execução

### 1. Migrações do Banco de Dados (Supabase)

Para validar a integridade do banco e aplicar o schema 4NF:

```bash
uv run python scripts/apply_supabase_migrations.py --check
```

### 2. Ingestão e Povoamento da Base de Dados

O FertiPartner disponibiliza um script unificado de coleta de dados:

```bash
# Executar todos os coletores de dados
uv run python scripts/populate_database.py --all

# Ou executar um coletor específico:
uv run python scripts/populate_database.py --source fred
uv run python scripts/populate_database.py --source comex
uv run python scripts/populate_database.py --source comtrade
uv run python scripts/populate_database.py --source faostat
```

### 3. Autenticação e Token do FAOSTAT

Para inspecionar a validade do token JWT ou autenticar programmaticamente:

```bash
# Verificar status e expiração do token atual
uv run python scripts/faostat_token_generator.py --check

# Efetuar login e obter novo token de 1 hora
uv run python scripts/faostat_token_generator.py --login --username seu_email --password sua_senha
```

### 4. Inicialização do Front-end (Streamlit + Plotly)

O FertiPartner conta com uma interface analítica interativa construída em **Streamlit 1.63+** e **Plotly**:

```bash
# Executar o painel analítico diretamente
uv run python scripts/run_dashboard.py

# Ou via comando nativo do Streamlit:
uv run streamlit run src/app/presentation/streamlit/dashboard.py
```

A aplicação será disponibilizada em seu navegador no endereço: `http://localhost:8501`.

---

## Testes Automatizados

O conjunto de testes do FertiPartner é dividido em testes unitários (executados no CI sem necessidade de credenciais) e testes de integração:

```bash
# Executar apenas testes unitários e com mocks (rápido e padrão do CI):
uv run pytest -m "not integration"

# Executar todos os testes (incluindo testes de integração ao vivo com APIs e Supabase):
uv run pytest
```

---

## Documentação Técnica

Para se aprofundar nos detalhes do projeto, consulte a pasta `docs/`:

- [Arquitetura Geral](docs/architecture/architecture.md)
- [Modelagem de Dados em Quarta Forma Normal (4NF)](docs/architecture/data-model.md)
- [Boas Práticas de Integração com APIs Externas](docs/architecture/external-apis-best-practices.md)
- [ADR 0001: Supabase e Arquitetura 4NF](docs/architecture/decisions/0001-supabase-4nf-data-architecture.md)
- [Convenções de Engenharia](docs/engineering/conventions.md)
- [Estratégia de Testes](docs/engineering/testing.md)
- [Definição de Pronto (Definition of Done)](docs/engineering/definition-of-done.md)
- [Diretrizes de Agentes de IA](AGENTS.md)