# Estratégia e Padrões de Testes — FertiPartner

Este documento define a estratégia de testes automatizados adotada no projeto **FertiPartner**.

---

## 1. Pirâmide de Testes

```text
       / \
      /   \      E2E Tests (End-to-End)
     /     \     - Fluxos completos de ponta a ponta
    /───────\
   /         \   Integration Tests
  /           \  - Integrações com banco, APIs e pipelines
 /─────────────\
/               \ Unit Tests
───────────────── - Regras de negócio, entidades e use cases isolados
```

---

## 2. Estrutura de Diretórios de Testes

Os testes estão organizados em:

* `tests/unit/`:
  * Foco em lógica de domínio, validações e casos de uso isolados.
  * Execução rápida e sem dependências de rede, I/O ou banco de dados externo.
  * Utilizam mocks/stubs para contratos externos.
* `tests/integration/`:
  * Foco na comunicação entre componentes (ex: repositórios com banco de dados real/em memória, parsers de arquivos brutos).
* `tests/e2e/`:
  * Foco no fluxo completo desde a ingestão de dados até o cálculo de indicadores e respostas de apresentação.
* `tests/conftest.py`:
  * Fixtures globais compartilhadas entre os módulos de teste.

---

## 3. Execução dos Testes

Utilizamos o **pytest** como ferramenta padrão de execução:

```bash
# Executar todos os testes
pytest

# Executar apenas testes unitários
pytest tests/unit

# Executar apenas testes de integração
pytest tests/integration

# Executar apenas testes e2e
pytest tests/e2e

# Executar com relatório detalhado e medição de cobertura
pytest --cov=src
```

---

## 4. Diretrizes e Boas Práticas

* **Padrão AAA (Arrange, Act, Assert)**: Todo teste deve ser estruturado claramente nas três etapas.
* **Isolamento e Determinismo**: Testes não devem depender da ordem de execução nem de estado persistente compartilhado entre casos.
* **Nomes Descritivos**: O nome da função de teste deve descrever o cenário e o resultado esperado:
  * Exemplo: `def test_should_raise_error_when_fertilizer_percentage_is_negative():`
* **Testes de Borda (Edge Cases)**: Cobrir valores nulos, coleções vazias, dados incompletos e erros de rede esperados.
