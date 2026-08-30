# Skill: CI/CD com GitHub Actions e pytest

## Objetivo

Esta skill define como configurar e manter a automação de **Continuous Integration (CI)** e **Continuous Delivery/Deployment (CD)**.

A pipeline deve executar automaticamente as verificações definidas pelo projeto e validar a mesma suíte de testes utilizada durante o desenvolvimento local.

Esta skill trabalha em conjunto com a skill de **TDD com pytest**.

---

# 1. Contrato com a skill de TDD

A skill de TDD define:

```text
O que é testado
Como os testes são escritos
Onde os testes ficam
Como os testes são executados
```

Esta skill define:

```text
Quando os testes são executados
Em qual ambiente
Em qual ordem
Quais condições bloqueiam a integração
Como o build e deploy acontecem
```

A pipeline nunca deve conter uma implementação alternativa dos testes.

A fonte de verdade deve permanecer:

```text
project/
├── src/
├── tests/
└── pyproject.toml
```

O GitHub Actions deve apenas executar os comandos definidos pelo projeto.

---

# 2. Princípio fundamental

A CI deve reproduzir um ambiente limpo e independente.

Fluxo:

```text
git push
    ↓
GitHub Actions
    ↓
Runner temporário
    ↓
Checkout do código
    ↓
Instalação do ambiente
    ↓
Instalação das dependências
    ↓
Execução das verificações
    ↓
Resultado
```

A aplicação não deve depender de:

* arquivos locais do desenvolvedor;
* bancos locais;
* variáveis não documentadas;
* caches necessários para funcionamento;
* estado pré-existente.

---

# 3. Estrutura esperada

A pipeline deve assumir:

```text
project/
│
├── src/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── pyproject.toml
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── cd.yml
```

A estrutura de testes é definida pela skill de TDD.

---

# 4. Continuous Integration

A CI deve executar automaticamente em:

```text
push
pull_request
```

Fluxo mínimo:

```text
Checkout
    ↓
Setup Python
    ↓
Instalar dependências
    ↓
Lint
    ↓
Testes unitários
    ↓
Testes de integração
    ↓
Coverage
    ↓
Build
```

O objetivo da CI é responder:

> A mudança pode ser integrada com segurança?

---

# 5. Separação das etapas

A pipeline deve separar responsabilidades.

## Fast Checks

Devem fornecer feedback rápido.

```text
Lint
Type checking
Unit tests
```

Exemplo:

```text
Código inválido
    ↓
Falha rapidamente
```

---

## Integration Checks

Devem validar:

```text
Database
Repositories
APIs
Infraestrutura
```

Executar:

```bash
pytest tests/integration
```

---

## Quality Checks

Podem incluir:

```text
Coverage
Static analysis
Dependency checks
Security scanning
```

Essas verificações devem ser adicionadas conforme a maturidade do projeto.

---

# 6. Ordem recomendada

```text
┌────────────────────┐
│ Checkout           │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Setup Environment  │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Install Dependencies│
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Lint / Type Check  │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Unit Tests         │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Integration Tests  │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Coverage           │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ Build              │
└────────────────────┘
```

Se uma etapa falhar, as etapas dependentes não devem continuar.

---

# 7. Workflow base de CI

Arquivo:

```text
.github/workflows/ci.yml
```

Exemplo:

```yaml
name: CI

on:
  push:
    branches:
      - main

  pull_request:

jobs:

  unit-tests:

    name: Unit Tests

    runs-on: ubuntu-latest

    steps:

      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Python
        uses: actions/setup-python@v5

        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run unit tests
        run: |
          pytest tests/unit


  integration-tests:

    name: Integration Tests

    runs-on: ubuntu-latest

    needs: unit-tests

    steps:

      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Python
        uses: actions/setup-python@v5

        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run integration tests
        run: |
          pytest tests/integration
```

Os comandos da pipeline devem ser compatíveis com a execução local definida pela skill de TDD.

---

# 8. Ambiente de integração

Quando testes de integração precisarem de infraestrutura real, a CI deve fornecer um ambiente isolado.

Exemplos:

```text
PostgreSQL temporário
Redis temporário
Container temporário
API simulada
```

Nunca utilizar:

```text
Banco de produção
Serviço de produção
Dados reais de usuários
Credenciais de produção
```

---

# 9. Continuous Delivery / Deployment

CD deve acontecer apenas depois que a CI estiver aprovada.

Fluxo:

```text
Código
   ↓
CI aprovada
   ↓
Build
   ↓
Artifact
   ↓
Deploy Staging
   ↓
Smoke Tests
   ↓
Deploy Production
```

Dependendo da estratégia do projeto:

```text
Continuous Delivery
```

significa:

```text
Pronto para produção
+
Aprovação manual
```

Enquanto:

```text
Continuous Deployment
```

significa:

```text
CI aprovada
    ↓
Deploy automático
```

A escolha depende do risco e do contexto do sistema.

---

# 10. Staging

Antes de produção, preferir:

```text
Production-like environment
```

Fluxo:

```text
Build
  ↓
Deploy Staging
  ↓
Smoke Tests
  ↓
E2E
  ↓
Validação
```

Staging deve ser usado para validar integrações que não podem ser adequadamente reproduzidas apenas com mocks.

---

# 11. Smoke Tests

Após um deploy:

```text
Deploy
   ↓
Health Check
   ↓
Endpoint crítico
   ↓
Dependência crítica
```

Exemplo:

```python
def test_application_is_healthy(client):

    response = client.get("/health")

    assert response.status_code == 200
```

Smoke tests devem ser:

* rápidos;
* simples;
* confiáveis;
* focados em funcionalidades críticas.

---

# 12. Testes E2E

E2E deve ser executado em ambientes adequados, normalmente:

```text
Staging
```

ou ambientes temporários.

Não executar E2E excessivamente em todos os commits se isso prejudicar significativamente o tempo de feedback.

Preferir:

```text
Pull Request
    ↓
Unit
Integration
    ↓
Merge
    ↓
Staging
    ↓
E2E
```

A estratégia pode variar conforme a criticidade do projeto.

---

# 13. Cobertura

A CI deve gerar cobertura usando a mesma suíte definida pela skill de TDD.

Exemplo:

```bash
pytest \
  tests/unit \
  tests/integration \
  --cov=src \
  --cov-report=xml \
  --cov-report=term
```

Cobertura não deve ser utilizada isoladamente como medida de qualidade.

O objetivo é identificar áreas potencialmente não testadas.

Não escrever testes apenas para aumentar porcentagens.

---

# 14. Falha da pipeline

Se qualquer etapa crítica falhar:

```text
CI = FAILED
```

A alteração não deve ser considerada validada.

Fluxo:

```text
Pipeline falhou
      ↓
Investigar causa
      ↓
Corrigir código ou teste
      ↓
Executar localmente
      ↓
Commit
      ↓
Push
      ↓
CI executa novamente
```

Nunca corrigir diretamente a pipeline para ignorar um teste legítimo sem investigar a causa.

---

# 15. Relação entre execução local e CI

Os comandos devem ser consistentes.

Exemplo:

Local:

```bash
pytest tests/unit
pytest tests/integration
```

CI:

```bash
pytest tests/unit
pytest tests/integration
```

Isso reduz diferenças entre:

```text
Funciona na minha máquina
```

e:

```text
Funciona no ambiente reproduzível
```

---

# 16. Arquitetura completa

```text
DEVELOPMENT
│
├── TDD
│   │
│   ├── RED
│   ├── GREEN
│   └── REFACTOR
│
├── pytest local
│
└── git push
        │
        ▼
CI
│
├── Environment Setup
│
├── Lint
│
├── Unit Tests
│
├── Integration Tests
│
├── Coverage
│
└── Build
        │
        ▼
CI APPROVED
        │
        ▼
CD
│
├── Deploy Staging
│
├── Smoke Tests
│
├── E2E Tests
│
└── Deploy Production
        │
        ▼
Production Monitoring
```

---

# 17. Regras de comunicação com a skill de TDD

Ao implementar ou modificar código:

1. Consultar a skill de TDD para criar ou modificar testes.
2. Garantir que os testes passam localmente.
3. Utilizar `pytest` como executor padrão.
4. Não criar lógica de teste exclusiva dentro do GitHub Actions.
5. A CI deve executar os mesmos testes existentes no diretório `tests/`.
6. Se uma mudança exigir infraestrutura adicional, modificar a configuração da CI sem alterar artificialmente os testes para se adaptar ao ambiente.
7. Se houver divergência entre ambiente local e CI, corrigir a causa raiz e não ignorar a falha.

---

# Checklist de CI/CD

## CI

```text
[ ] Workflow versionado no repositório
[ ] Ambiente reproduzível
[ ] Dependências instaladas explicitamente
[ ] Lint executado
[ ] Testes unitários executados
[ ] Testes de integração executados
[ ] Cobertura gerada
[ ] Build validado
```

## CD

```text
[ ] CI aprovada antes do deploy
[ ] Ambiente de staging disponível quando necessário
[ ] Smoke tests após deploy
[ ] E2E para fluxos críticos
[ ] Segredos não expostos no código
[ ] Produção isolada de testes
```

---

# Regra final

A arquitetura deve manter esta separação:

```text
TESTES
│
└── Definem o comportamento
    e pertencem ao projeto
        │
        ▼
PYTEST
│
└── Executa os testes
        │
        ▼
CI/CD
│
└── Automatiza quando e onde
    pytest será executado
```

Para criação, alteração ou organização de testes, consultar a skill de **TDD com pytest**.

Esta skill deve concentrar-se exclusivamente em automação, integração, qualidade e entrega.
