# Convenções de Engenharia — FertiPartner

Este documento define as diretrizes, padrões de código e boas práticas a serem seguidas no desenvolvimento do **FertiPartner**.

---

## 1. Princípios Arquiteturais

O projeto segue os princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**:

* **Independência de Frameworks**: O núcleo do domínio não depende de bibliotecas de terceiros ou frameworks web/CLI.
* **Camadas bem delimitadas**:
  * `domain`: Entidades puras, objetos de valor (Value Objects), regras de negócio centrais e interfaces de repositórios/serviços.
  * `application`: Casos de uso (Use Cases), orquestração de fluxos de dados, DTOs e comandos/consultas.
  * `infrastructure`: Implementação de repositórios, integrações externas (APIs de fontes públicas), banco de dados, drivers e adaptadores.
  * `presentation`: Controladores, rotas de API, comandos CLI ou interfaces de visualização.
* **Regra de Dependência**: As dependências sempre apontam para dentro (`presentation` -> `application` -> `domain` <- `infrastructure`).

---

## 2. Padrões de Código Python

* **Versão**: Python 3.13+
* **Tipagem Estática (Type Hints)**: Obrigatória em assinaturas de funções, métodos e atributos de classes.
  * Utilizar generics nativos (`list[str]`, `dict[str, Any]`, `tuple[int, ...]`).
  * Utilizar `| None` em vez de `Optional[...]`.
* **Imutabilidade e Modelagem**:
  * Utilizar `dataclasses` (com `frozen=True` para Value Objects) ou `pydantic` para validação e serialização de dados na borda.
* **Estilo e Formatação**:
  * Seguir a PEP 8.
  * Limite de linha recomendado: 88 a 100 caracteres.
  * Docstrings em formato Google ou Markdown explicativo para funções públicas e classes de domínio.

---

## 3. Nomenclatura e Organização

* **Módulos e Pacotes**: `snake_case` em minúsculas (ex: `fertilizer_service.py`, `data_pipeline/`).
* **Classes**: `PascalCase` (ex: `FertilizerEntity`, `CalculateTradeBalanceUseCase`).
* **Funções e Métodos**: `snake_case` com verbos de ação (ex: `collect_raw_data()`, `validate_payload()`).
* **Constantes**: `UPPER_SNAKE_CASE` (ex: `DEFAULT_TIMEOUT_SECONDS = 30`).
* **Arquivos de Teste**: Prefixados com `test_` (ex: `test_fertilizer_entity.py`).

---

## 4. Tratamento de Erros e Logs

* **Exceções Customizadas de Domínio**: Definir exceções específicas na camada de domínio (ex: `FertilizerNotFoundError`, `InvalidTradeDataError`).
* **Evitar capturas genéricas**: Não utilizar `except Exception:` sem tratamento ou re-lançamento adequado.
* **Logging Estruturado**: Usar o módulo padrão `logging` com níveis adequados (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
