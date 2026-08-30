# Skill: Test-Driven Development (TDD) com pytest

## Objetivo

Esta skill define como implementar funcionalidades utilizando **Test-Driven Development (TDD)**.

O objetivo é garantir que comportamentos sejam especificados através de testes antes da implementação e que toda nova funcionalidade seja validada localmente antes de ser enviada para o pipeline de CI/CD.

Esta skill trabalha em conjunto com a skill de **CI/CD**.

### Contrato entre as skills

Esta skill é responsável por:

* escrever e manter os testes;
* organizar os testes;
* aplicar o ciclo TDD;
* garantir que os testes possam ser executados localmente;
* manter testes determinísticos e independentes.

A skill de CI/CD é responsável por:

* executar automaticamente os testes definidos por esta skill;
* executar a suíte em ambiente limpo;
* bloquear mudanças que introduzam falhas;
* aplicar verificações adicionais de qualidade;
* construir e, quando aplicável, implantar a aplicação.

Os testes pertencem ao código do projeto. A pipeline não contém a lógica dos testes; apenas executa os comandos definidos pelo projeto.

---

# 1. Princípios fundamentais

## 1.1 Testes como especificação

Todo comportamento relevante do sistema deve ser descrito por um teste.

Antes de implementar uma funcionalidade, responder:

1. Qual comportamento deve existir?
2. Qual é a entrada?
3. Qual é a saída esperada?
4. Quais são os casos inválidos?
5. Quais são os casos extremos?

O teste deve validar comportamento observável, e não detalhes internos de implementação.

Evitar testes como:

```python
assert service._internal_variable == 10
```

Preferir:

```python
assert service.calcular_resultado() == 10
```

---

# 2. Ciclo obrigatório do TDD

Toda implementação nova deve seguir:

```text
RED
 ↓
GREEN
 ↓
REFACTOR
 ↓
RED
```

## 2.1 RED

Escrever um teste que descreve um comportamento ainda inexistente.

O teste deve falhar inicialmente.

Exemplo:

```python
def test_calcula_desconto_de_dez_por_cento():
    assert calcular_desconto(100, 10) == 90
```

Neste momento, a implementação ainda não deve ser criada apenas para antecipar o teste.

Executar:

```bash
uv run pytest
```

Confirmar que a falha acontece pelo motivo esperado.

---

## 2.2 GREEN

Implementar o mínimo necessário para fazer o teste passar.

O objetivo nesta etapa não é produzir a implementação mais sofisticada.

O objetivo é:

```text
Teste falhando
      ↓
Implementação mínima
      ↓
Teste passando
```

Executar:

```bash
uv run pytest
```

---

## 2.3 REFACTOR

Depois que os testes estiverem passando:

* remover duplicações;
* melhorar nomes;
* simplificar estruturas;
* melhorar a organização;
* melhorar a legibilidade;
* extrair responsabilidades quando necessário.

Após cada refatoração:

```bash
uv run pytest
```

Os testes devem continuar passando.

---

# 3. Estrutura obrigatória dos testes

A estrutura padrão do projeto deve ser:

```text
project/
│
├── src/
│   └── application/
│
├── tests/
│   │
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   │
│   ├── integration/
│   │   ├── database/
│   │   └── infrastructure/
│   │
│   ├── e2e/
│   │
│   └── conftest.py
│
├── pyproject.toml
│
└── .github/
    └── workflows/
```

A skill de CI/CD deve utilizar esta estrutura.

Não criar uma estrutura de testes diferente exclusivamente para a pipeline.

---

# 4. Convenções do pytest

## 4.1 Arquivos

Arquivos de teste devem seguir:

```text
test_*.py
```

Exemplo:

```text
test_user_service.py
test_order_service.py
test_repository.py
```

---

## 4.2 Funções

Funções de teste devem seguir:

```text
test_descricao_do_comportamento
```

Exemplo:

```python
def test_usuario_nao_pode_ser_criado_com_email_invalido():
    ...
```

O nome deve descrever:

```text
Comportamento
+
Condição
+
Resultado esperado
```

---

# 5. Estrutura interna dos testes

Utilizar preferencialmente:

```text
Arrange
Act
Assert
```

Também conhecido como AAA.

Exemplo:

```python
def test_calcula_total_do_pedido():

    # Arrange
    pedido = Pedido(valor=100)

    # Act
    total = pedido.calcular_total()

    # Assert
    assert total == 100
```

Evitar múltiplos comportamentos independentes no mesmo teste.

Cada teste deve responder preferencialmente a uma única pergunta.

---

# 6. Testes unitários

Testes unitários devem:

* ser rápidos;
* ser determinísticos;
* não depender de rede;
* não depender de banco real;
* não depender de APIs externas;
* não depender de ordem de execução.

Dependências externas devem ser substituídas por:

* mocks;
* fakes;
* stubs.

Exemplo:

```python
def test_pedido_aprovado_quando_pagamento_sucesso(payment_gateway):

    payment_gateway.process.return_value = True

    resultado = service.criar_pedido()

    assert resultado.status == "APPROVED"
```

Os testes unitários devem representar a maior parte da suíte.

---

# 7. Testes de integração

Testes de integração validam componentes reais trabalhando juntos.

Exemplos:

```text
Service + Repository

Repository + Database

API + Service

Application + Infrastructure
```

Exemplo:

```python
def test_usuario_e_salvo_e_recuperado_do_banco(db):

    usuario = criar_usuario(
        nome="Teste",
        email="teste@example.com"
    )

    usuario_salvo = buscar_usuario(usuario.id)

    assert usuario_salvo.email == "teste@example.com"
```

Testes de integração podem utilizar:

* banco temporário;
* containers;
* serviços de teste;
* infraestrutura isolada.

Nunca devem depender de dados permanentes de produção.

---

# 8. E2E

Testes End-to-End devem validar fluxos críticos completos.

Exemplo:

```text
Usuário
  ↓
Login
  ↓
Criação de recurso
  ↓
Persistência
  ↓
Visualização do resultado
```

Devem existir em quantidade limitada.

Não utilizar E2E para testar toda regra de negócio.

---

# 9. Fixtures

Utilizar fixtures do pytest para:

* dados reutilizáveis;
* configuração de ambiente;
* banco de testes;
* clientes de API;
* objetos compartilhados.

Fixtures globais devem ficar em:

```text
tests/conftest.py
```

Fixtures específicas devem ficar próximas aos testes que as utilizam.

Evitar fixtures excessivamente complexas ou que escondam o comportamento sendo testado.

---

# 10. Parametrização

Quando o mesmo comportamento deve ser validado com múltiplas entradas, utilizar:

```python
import pytest


@pytest.mark.parametrize(
    "valor,percentual,esperado",
    [
        (100, 10, 90),
        (100, 20, 80),
        (200, 50, 100),
    ],
)
def test_calcula_desconto(valor, percentual, esperado):
    assert calcular_desconto(valor, percentual) == esperado
```

Evitar criar diversos testes quase idênticos.

---

# 11. Independência dos testes

Cada teste deve poder ser executado:

```text
Individualmente
Em conjunto
Em ordem diferente
Em ambiente limpo
```

Nunca assumir:

```text
Teste A executou antes do Teste B
```

Nunca compartilhar estado mutável entre testes.

---

# 12. Execução local

Antes de realizar commit, executar:

```bash
uv run pytest
```

Para testes unitários:

```bash
uv run pytest tests/unit
```

Para testes de integração:

```bash
uv run pytest tests/integration
```

Para um teste específico:

```bash
uv run pytest tests/unit/test_service.py
```

A execução local deve reproduzir os mesmos comandos utilizados pela CI sempre que possível.

---

# 13. Cobertura

Cobertura é um indicador auxiliar.

Não escrever testes apenas para aumentar o número de cobertura.

Evitar:

```text
100% de cobertura
+
Testes sem validação relevante
```

Preferir:

```text
Cobertura significativa
+
Comportamentos críticos testados
+
Casos de erro testados
```

A cobertura deve ser executada através de:

```bash
uv run pytest --cov=src
```

A skill de CI/CD deve executar essa verificação conforme as regras definidas no projeto.

---

# 14. Relação obrigatória com CI/CD

Antes de considerar uma implementação concluída:

```text
TDD local
    ↓
Testes passam
    ↓
Commit
    ↓
Push
    ↓
CI executa a mesma suíte
    ↓
Ambiente limpo
    ↓
Todos os testes passam
```

A implementação não deve ser considerada integrada enquanto a CI estiver falhando.

---

# 15. Checklist antes do commit

```text
[ ] O comportamento foi especificado por um teste?
[ ] O teste inicialmente falhou pelo motivo esperado?
[ ] A implementação foi criada após o teste?
[ ] Os testes unitários passam?
[ ] Os testes de integração relevantes passam?
[ ] Os testes são independentes?
[ ] Não existem dependências externas desnecessárias?
[ ] O pytest pode executar a suíte localmente?
[ ] A estrutura segue a convenção definida?
```

---

# Regra final

A fonte de verdade dos comportamentos testados é:

```text
Código da aplicação
        +
Código dos testes
```

A pipeline de CI/CD não deve duplicar lógica de testes.

A pipeline deve apenas:

```text
Preparar ambiente
        ↓
Instalar dependências
        ↓
Executar comandos do projeto
        ↓
Reportar resultado
```

Para regras de execução automática, consultar a skill de CI/CD.
